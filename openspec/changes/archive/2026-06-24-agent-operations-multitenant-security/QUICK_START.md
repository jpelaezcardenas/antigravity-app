# 🚀 QUICK START — Deploy Now

**Status:** ✅ Code complete, tests passing, ready to deploy  
**Time needed:** 15 minutes  
**Difficulty:** Easy (3 manual steps + Railway auto-deploy)

---

## Your Action Checklist (Copy-Paste Ready)

### ✅ Step 1: Merge PR to Main (5 min)

**In GitHub:**

1. Go to: https://github.com/jpelaezcardenas/antigravity-app/pulls
2. Find PR: `feature/agent-operations-multitenant-security`
3. Click: **"Merge pull request"**
4. ✅ **Merged to main** (Railway webhook auto-triggers)

---

### ✅ Step 2: Set Railway Env Var (2 min)

🚨 **CRITICAL — Without this step, deployment will FAIL**

**Get the key:**
```
Go to: https://app.supabase.com/project/[your-project]/settings/api
Look for: "Service Role Secret" (long string starting with eyJ...)
Copy it.
```

**Set in Railway:**
```
Go to: https://railway.app/[your-project]/settings
Tab: "Environment"
Add new variable:
  KEY:   SUPABASE_SERVICE_ROLE_KEY
  VALUE: [paste the key from above]
Click: Save
```

✅ **Done**

---

### ✅ Step 3: Wait for Deploy (2-3 min)

**Monitor in Railway:**

```
Go to: https://railway.app/[your-project]/deployments
Look for: Latest deployment (timestamp from ~now)
Wait until: Status is 🟢 GREEN "Running"
```

---

### ✅ Step 4: Quick Verify (2 min)

**In browser console (while logged into PWA):**

```javascript
// Open DevTools (F12) → Console
// Send WebSocket message:
{
  "type": "agent_invoke",
  "agent": "pulso",
  "params": {}
}

// Look for response with:
// - "cost": 0.005  ← NEW
// - "session_cost": 0.005  ← NEW
```

If you see those fields → ✅ **Success!**

---

## What Just Deployed

✅ **Multi-tenant access control** — Users gated by tenant membership  
✅ **Audit logging** — Every invocation recorded in agent_operations table  
✅ **Cost tracking** — $0.005-$0.025 per operation, accumulated per session  
✅ **RLS isolation** — Users can't see other tenant's operations  

---

## If Anything Goes Wrong

| Issue | Fix | Time |
|-------|-----|------|
| "Access denied" (all users blocked) | SUPABASE_SERVICE_ROLE_KEY not set in Railway | Add it (2 min) |
| Deploy stuck "Building" | Check Railway logs for errors | Revert to previous version (1 min) |
| No `cost` field in response | Restart Railway deploy | 2 min |
| DB query returns 0 rows | RLS too strict — contact support | — |

---

## Full Documentation

If you need details:

| What | Where |
|------|-------|
| How to test manually | `testing/manual-testing-step8.md` |
| Full deploy checklist | `reports/2026-06-24-pre-deployment-status.md` |
| Post-deploy verification | `reports/2026-06-24-post-deployment-verification.md` |
| What was built | `COMPLETION_STATUS.md` |
| Architecture decisions | `design.md` |

---

## Timeline

```
Now:           You merge PR (GitHub)
+2 min:        You set env var (Railway)
+2 min:        Railway auto-deploys (~2 min to build)
+1 min:        Backend running
+2 min:        You verify (quick test)
──────
15 min total:  Phase 5 LIVE in production ✅
```

---

## Success Indicators

- ✅ Railway shows "Running" (green)
- ✅ WebSocket response includes `cost` and `session_cost` fields
- ✅ agent_operations table has new rows with `status=success`
- ✅ Blocked users get `status=error, message="Access denied"`
- ✅ No errors in Railway logs

---

## Next (Optional)

After deploy, you can:
- Monitor logs: `railway logs --follow`
- Query DB: Check agent_operations table in Supabase
- Run full E2E tests: Set RUN_AGENT_OPS=1, run pytest
- Share access: Governance is now transparent to users

---

**Ready? Start with Step 1 (GitHub merge).** 🚀

If you get stuck, check the full documentation files listed above.
