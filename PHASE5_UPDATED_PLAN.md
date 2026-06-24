# PHASE 5: AGENT INTEGRATION - UPDATED WITH PHASE 3 LEARNINGS

**Status**: 🔄 READY FOR REVISION & ENHANCEMENT  
**Analysis Date**: 2026-06-24  
**Target**: Complete Phase 5 with Phase 3 security + observability  
**Duration**: 3-4 days

---

## FINDINGS

### Phase 5 Current State
✅ **ALREADY IMPLEMENTED:**
- 8 agent endpoints (Centinela, Taty, Radar, Social-Ops, Audit, Approval, Maestro, Pulso)
- WebSocket handler with ConnectionManager
- Agent context with permissions
- Agent transformers + validation

❌ **MISSING (Integration gaps):**
- Multi-tenant RLS policies (from Phase 3 T12)
- Cost tracking per operation (from Phase 3 T11.6)
- Audit logging per operation (from Phase 3 T12)
- Tenant_id propagation in all queries

---

## PROPOSED 5-STEP UPDATE

### STEP 1: Add Multi-Tenant RLS (1 day)
- Create `agent_operations` table with tenant_id
- Add RLS policies (prevent cross-tenant access)
- Create `AgentAccessControl` middleware

### STEP 2: Add Cost Tracking (1 day)
- Inherit cost matrix from Phase 3 T11.6
- Track operation_type → cost ($0.003-$0.025 per operation)
- Update each agent endpoint to log costs

### STEP 3: Add Audit Logging (1 day)
- Create `agent_audit_log` table with full context
- Log every operation (success/failed/blocked)
- Restrict logs to admin users (Phase 3 RLS pattern)

### STEP 4: Update WebSocket (1 day)
- Inject tenant_id from JWT
- Accumulate costs per session
- Return cost metadata in responses

### STEP 5: E2E Testing (1 day)
- Test multi-tenant isolation
- Test cost tracking accuracy
- Verify no cross-tenant leakage

---

## ACCEPTANCE CRITERIA (UPDATED)

**Functional:**
- ✅ 8 agents respond to WebSocket (already done)
- ✅ Components render real data (already done)
- **NEW**: Multi-tenant isolation verified
- **NEW**: Cost tracking per operation
- **NEW**: Audit logging per operation

**Security:**
- ✅ JWT context propagated
- **NEW**: tenant_id in all agent queries
- **NEW**: RLS policies active
- **NEW**: No cross-tenant data leakage

---

## RECOMMENDATION

**Option A (Recommended)**: Implement all 5 steps with full Phase 3 integration
- Result: Production-grade secure agent system
- Effort: 3-4 days
- Risk: Low (proven patterns from Phase 3)

**Option B**: Keep current Phase 5 as-is
- Result: Functional but missing observability/security
- Effort: 0 days
- Risk: Cross-tenant leakage possible, no cost tracking

---

**What would you like to do?**
- [A] Begin Phase 5 update with all 5 steps
- [B] Start with Step 1 only (RLS)
- [C] Review the plan first
- [D] Something else
