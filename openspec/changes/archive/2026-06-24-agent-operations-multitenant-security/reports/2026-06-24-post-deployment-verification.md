# Post-Deployment Verification Checklist

**After Railway deploy completes, follow this checklist to verify governance layer is live.**

**Expected deployment completion:** ~2 minutes after merge to main  
**Verification time:** ~10 minutes  
**Rollback time:** ~2 minutes (if needed)

---

## ✅ Phase 1: Deploy Verification (2 min)

### 1.1 Confirm Deploy Succeeded

```bash
# Check Railway logs
# URL: https://railway.app/[project]/deployments

# Look for:
# ✅ "Deployment successful" (green status)
# ✅ "Running" (active)
# ❌ No "Build failed" or "Crashed" messages

# Tail logs in terminal:
railway logs --follow
```

**Expected output:**
```
[Backend] Starting FastAPI server...
[Backend] Uvicorn running on 0.0.0.0:8000
[Backend] INFO: Application startup complete
```

### 1.2 Verify Service-Role Client Initialization

```bash
# In Railway logs, search for:
railway logs | grep -E "service.*role|AgentAccessControl|SUPABASE_SERVICE_ROLE_KEY"
```

**Expected:**
```
[Backend] AgentAccessControl: service-role client loaded
[Backend] supabase_client: two clients initialized (anon, service-role)
```

**If missing:** SUPABASE_SERVICE_ROLE_KEY not set in Railway env. **ROLLBACK REQUIRED.**

---

## ✅ Phase 2: Live Smoke Tests (5 min)

### 2.1 Test Successful Agent Invocation

**Setup:**
- Open production PWA: https://contexia.online/app/bunker
- Log in with valid user (Entidad A)
- Open browser DevTools → Network tab → WS (WebSocket messages)

**Test:**
```javascript
// In browser console, send WebSocket message:
// (assuming WS connection exists)
{
  "type": "agent_invoke",
  "agent": "pulso",
  "params": {}
}
```

**Expected response:**
```javascript
{
  "type": "agent_output",
  "agent": "pulso",
  "data": {
    "status": "success",
    "agent": "pulso",
    "data": { "caja_real": "...", ... },
    "cost": 0.005,              // ← NEW (VERIFY PRESENT)
    "session_cost": 0.005       // ← NEW (VERIFY PRESENT)
  },
  "timestamp": "2026-06-24T..."
}
```

**✅ PASS if:**
- Response includes `cost` and `session_cost` fields
- Values are numbers > 0
- No JavaScript errors in console

### 2.2 Query Production Database

**Via Supabase Dashboard:**

```sql
SELECT 
  agent_name, 
  status, 
  cost, 
  user_id, 
  tenant_id, 
  created_at
FROM agent_operations
ORDER BY created_at DESC
LIMIT 5
```

**Expected rows:**
```
pulso     | success | 0.005   | u1@example.com | t1        | 2026-06-24T...
...
```

**✅ PASS if:**
- Latest rows show status=success (from test invocation)
- cost values match AGENT_OPERATION_COSTS matrix (0.005 for pulso, 0.01 for centinela, etc.)
- No NULL costs
- created_at is recent (within last minute)

### 2.3 Verify RLS is Enforced

**Test:**
```bash
# Query with USER_A's token (Entidad A, tenant t1)
curl -H "Authorization: Bearer $JWT_USER_A" \
  "https://antigravity-app-production-175a.up.railway.app/api/v1/agent-operations?tenant_id=t1" \
  | jq '.data | length'

# Query with USER_B's token (Entidad B, tenant t2)
curl -H "Authorization: Bearer $JWT_USER_B" \
  "https://antigravity-app-production-175a.up.railway.app/api/v1/agent-operations?tenant_id=t1" \
  | jq '.data | length'
```

**Expected:**
- USER_A sees: rows from tenant t1 only (count = N)
- USER_B sees: 0 rows (RLS blocks tenant t1)

**✅ PASS if:**
- USER_A can see own tenant operations
- USER_B cannot see tenant t1 (RLS enforced)

---

## ✅ Phase 3: Edge Case Verification (3 min)

### 3.1 Test Blocked Invocation (Access Denied)

**Setup:**
```bash
# Create a non-member context (user not in target tenant)
export USER_ID="nonmember@example.com"
export TENANT_ID="t999"  # Tenant user is not member of
export JWT=$(./generate_token.sh $USER_ID)
```

**Test:**
```bash
curl -X POST http://localhost:8000/ws/invoke_agent \
  -H "Authorization: Bearer $JWT" \
  -H "X-User-Id: $USER_ID" \
  -H "X-Workspace-Id: $TENANT_ID" \
  -d '{"agent": "pulso", "params": {}}'
```

**Expected response:**
```json
{
  "status": "error",
  "message": "Access denied: not_a_member"
}
```

**Database check:**
```sql
SELECT status, cost, error_message
FROM agent_operations
WHERE user_id = 'nonmember@example.com' AND status = 'blocked'
LIMIT 1

-- Expected: status='blocked', cost=0, error_message='not_a_member'
```

**✅ PASS if:**
- Response denied user access
- Row logged with status=blocked, cost=0

### 3.2 Test Cost Accumulation

**Setup:**
```bash
# Single WebSocket connection, multiple invocations
wscat -c "wss://contexia.online/ws/bunker?token=$JWT&workspace_id=t1&user_id=u1@example.com"
```

**Send 3 invocations:**
```javascript
// Invocation 1
{ "type": "agent_invoke", "agent": "pulso", "params": {} }
// Response: session_cost = 0.005

// Invocation 2
{ "type": "agent_invoke", "agent": "centinela", "params": {} }
// Response: session_cost = 0.015 (0.005 + 0.010)

// Invocation 3
{ "type": "agent_invoke", "agent": "radar", "params": {} }
// Response: session_cost = 0.023 (0.015 + 0.008)
```

**✅ PASS if:**
- session_cost increases with each invocation
- Total ≈ 0.023 (±0.0001 for floating-point rounding)

### 3.3 Stream Operation Logging

**Setup:**
```javascript
// Subscribe to agent stream
{ "type": "subscribe", "agent": "pulso" }

// Wait 10 seconds (stream processing)

// Unsubscribe
{ "type": "unsubscribe", "agent": "pulso" }
```

**Database check:**
```sql
SELECT operation_type, status, duration_ms, output_data
FROM agent_operations
WHERE agent_name = 'pulso' AND operation_type = 'stream'
ORDER BY created_at DESC
LIMIT 1

-- Expected: operation_type='stream', status='success', duration_ms > 5000
```

**✅ PASS if:**
- Stream operation logged separately (operation_type='stream')
- duration_ms reflects actual stream time
- output_data includes line_count

---

## ✅ Phase 4: Audit & Compliance (1 min)

### 4.1 Verify All Operations Are Logged

```sql
-- Count invocations in last hour
SELECT COUNT(*) as total_ops, status, SUM(cost) as total_cost
FROM agent_operations
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY status

-- Expected breakdown:
-- status='success': N rows, total_cost > 0
-- status='blocked': M rows, total_cost = 0
-- status='failed': K rows, total_cost > 0
```

### 4.2 Check for Audit Trail

```sql
-- Verify admin/finance role can read cross-tenant audit
SELECT DISTINCT tenant_id, COUNT(*) as ops_per_tenant
FROM agent_operations
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY tenant_id

-- Expected: Multiple tenants visible (if admin querying)
```

---

## ❌ Rollback Decision Tree

### If any test FAILS:

**Q1: Is SUPABASE_SERVICE_ROLE_KEY missing?**
```
→ YES: Add to Railway env (Step 11.0), redeploy
→ NO: Continue to Q2
```

**Q2: Are operations NOT being logged?**
```
→ YES: Check Railway logs for "Failed to record agent operation"
       If missing AgentOperationsLogger import → rollback
→ NO: Continue to Q3
```

**Q3: Is RLS not enforcing tenant isolation?**
```
→ YES: Verify agent_operations RLS policies exist:
       SELECT tablename, policyname FROM pg_policies 
       WHERE tablename='agent_operations'
       If policies missing → rollback (migration failed)
→ NO: Issue is elsewhere (collect logs, investigate)
```

**Q4: Are costs incorrect?**
```
→ YES: Check AgentCostTracker matrix in code
       Verify cost resolver is being called
       If matrix incomplete → can fix without rollback
→ NO: All tests pass! ✅
```

---

## 🔄 Rollback Procedure

**If tests FAIL and rollback is required:**

### Option A: Revert Deploy (Fastest)

```bash
# In Railway dashboard:
# Deployments → Select previous working version → "Restart"
# Takes ~1 minute to revert to prior state
```

### Option B: Drop Schema (Full Reset)

```sql
-- Only if migration introduced errors
DROP TABLE agent_operations CASCADE;
-- No data loss (new table, no consumers)

-- Then redeploy (fixes will be in code)
```

### Option C: Disable Governance (Temporary)

```python
# In websocket_handler.py, comment out governance gate:
# if not access_decision.allowed:
#     return {status: error, message: ...}

# Allows operations to continue while investigating
# NOT RECOMMENDED — use Option A or B instead
```

---

## Post-Verification Reporting

If all tests **PASS**, create final report:

```markdown
# Deployment Verification Report — 2026-06-24

**Status:** ✅ LIVE IN PRODUCTION

## Tests Passed
- [x] Deploy succeeded (green status, running)
- [x] Service-role client initialized
- [x] Successful invocation: cost/session_cost in response
- [x] RLS enforced: users see only own tenant ops
- [x] Blocked invocation: access denied, cost=0
- [x] Cost accumulation: session_cost increases correctly
- [x] Stream operations: logged separately with duration
- [x] Audit trail: all operations logged by status/tenant

## Production Evidence
- DB row count: [X operations in last hour]
- Cost accumulation: $[X.XX] total in 1h window
- Tenants isolated: [X distinct tenants, no cross-read]
- Errors logged: 0 (no audit failures)

## Timeline
- Deploy started: 2026-06-24 17:32 UTC
- Deploy completed: 2026-06-24 17:34 UTC
- Verification completed: 2026-06-24 17:44 UTC
- **Total time: 12 minutes**

## Conclusion
Governance layer is fully operational in production. All 5 slices + 11 steps complete.
Agent invocations are now:
- ✅ Gated by tenant membership
- ✅ Audited (agent_operations table)
- ✅ Costed (per-operation, per-tenant)
- ✅ Isolated (RLS enforced)

**Next steps:** Monitor logs for 24h, then release to external users.
```

If any test **FAILS**, document:

```markdown
# Deployment Issue Report — 2026-06-24

**Status:** ❌ ROLLBACK REQUIRED

## Failed Test
- [ ] [Test name]: [Expected] vs [Actual]

## Root Cause
[Analysis]

## Rollback Action Taken
[Option A/B/C + time taken]

## Fix Required
[Code change needed]

## Redeployment ETA
[When to retry]
```

---

**Report Templates:** See above ↑  
**Rollback SLA:** < 5 minutes (Option A)  
**Success Criteria:** All 8 tests PASS

---

**Document Created:** 2026-06-24  
**Author:** Claude Code (Haiku 4.5)  
**Next:** Follow this checklist immediately after Railway deploy completes.
