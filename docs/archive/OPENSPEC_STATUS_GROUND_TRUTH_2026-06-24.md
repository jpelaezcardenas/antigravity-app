# OpenSpec Status — Ground Truth (2026-06-24)

**CRITICAL FINDING:** Multiple OpenSpec changes claim "Ready" or "Done" but have contradictions between their `EXECUTION_STATUS.md` and `tasks.md`. This document reconciles ACTUAL code + DB state vs. claims.

---

## 📊 STATUS MATRIX

| OpenSpec | Claimed | Actual | Issues | Blocker? | Next Step |
|----------|---------|--------|--------|----------|-----------|
| **Phase 3** | ✅ Done | ✅ ARCHIVED | None | ✓ Can proceed | COMPLETE |
| **Phase 4** | ✅ Done | ✅ ARCHIVED | None | ✓ Can proceed | COMPLETE |
| **Phase 5** | ✅ Done | ✅ ARCHIVED | None | ✓ Can proceed | COMPLETE |
| **Phase 5 Enh.** | ✅ Done | ✅ ARCHIVED | None | ✓ Can proceed | COMPLETE |
| **hermes-user-sync** | ✅ Done | ⚠️ PARTIAL | T9 redesigned, T8.5 deferred | Maybe | Fix T9 design |
| **hermes-multi-tenant** | ⏳ Ready | ❌ BROKEN | 5 critical bugs, no E2E testing | YES | Fix Phase 1 first |
| **contexia-pwa-data** | ⏳ Ready | ❓ UNKNOWN | No tasks.md reviewed yet | Unknown | Investigate |
| **pwa-hermes-integration** | ? | ? | No tasks.md | Unknown | Investigate |

---

## 🔴 HERMES MULTI-TENANT WRAPPER — DETAILED FINDINGS

**File:** `openspec/changes/hermes-multi-tenant-wrapper/tasks.md`

**Claimed Status:** ⏳ Ready (never started)  
**Actual Status:** ❌ BROKEN (Phase 1 has critical bugs)

### The Contradiction

- **EXECUTION_STATUS.md claims:**
  - ✅ Phase 1 complete
  - ✅ 23/23 tests passing
  - ✅ 4 stakeholders approved
  - ✅ Live in production

- **tasks.md reveals (with ⚠️ Ground Truth Correction):**
  - All 28 tasks left at `⏳ Ready` (never marked done)
  - EXECUTION_STATUS.md's claims are "unverified/likely confabulated"

### 5 Critical Bugs Found

#### Bug 1: Non-Existent Tables
**Problem:** RLS migration targets 5 tables, but only 2 exist in Supabase
```
Migration 0003 targets:
- pulso_results (❌ DOES NOT EXIST)
- centinela_alerts (✅ exists)
- approval_queue (✅ exists)
- radar_insights (❌ DOES NOT EXIST)
- auditoria_reports (❌ DOES NOT EXIST)
```
**Why:** Pulso/Radar/Auditoría compute data on-the-fly, don't persist to tables  
**Impact:** RLS policies on non-existent tables silently fail-safe (won't isolate anything)  
**Fix needed:** Remove 3 non-existent tables from migration OR create them

#### Bug 2: NULL tenant_id in Real Data
**Problem:** Backfill script (T6) was never executed
```
Real Supabase state:
- centinela_alerts: rows with tenant_id = NULL
- approval_queue: rows with tenant_id = NULL
```
**Impact:** RLS policies can't isolate (NULL ≠ any value, so no rows match)  
**Fix needed:** Run backfill with correct defaults (which tenant_id for legacy rows?)

#### Bug 3: String vs UUID Type Mismatch (SAME AS Phase 5 Enh!)
**Problem:** JWT carries string tenant_id, RLS casts to UUID
```python
# core/security.py
tenant_id = "contexia-org-1"  # STRING

# Migration 0003 RLS policy
auth.jwt()->>'tenant_id'::uuid  # CAST TO UUID
```
**Impact:** String "contexia-org-1" cannot cast to UUID → cast error → no rows match → RLS fails silently  
**Fix needed:** Resolve to real UUID before JWT or change RLS cast logic  
**Status:** Same identity-resolver pattern from `agent-operations-multitenant-security` should be reused

#### Bug 4: T10 (JWT) Done, But Not Correctly
**Status:** `[x] T10` marked done  
**Reality:** `core/security.py` sets `tenant_id`, but value is broken (see Bug 3)  
**Fix needed:** Correct the value or add identity resolver

#### Bug 5: E2E Testing Not Done
**Status:** `[ ] T13-T15` not started  
**Reality:** No E2E tests exist to verify isolation actually works end-to-end  
**Fix needed:** Write tests that verify:
- User A invokes agent, gets tenant A results only
- User B cannot see User A's rows
- RLS fails gracefully (no error, just no rows)

### Phase Dependencies

```
Phase 1 (MVP):
├─ T1-T4 (Middleware): DONE ✅
├─ T5-T7 (RLS migration): HALF-DONE
│  ├─ Bugs: 3 non-existent tables, NULL tenant_id in data, UUID cast error
│  └─ T6 (backfill): NEVER RAN
├─ T10 (JWT tenant_id): DONE but broken (Bug 3)
└─ T11-T15 (Hermes integration + E2E): NOT STARTED

Phase 2 (SyncManager): DEFERRED INDEFINITELY
└─ Reason: Commercial negotiation with SyncManager not closed
└─ Alternative: Daily local/manual upload by Contexia admin (not scoped yet)

Phase 3 (Hardening): DEFERRED INDEFINITELY
└─ Reason: Depends on Phase 2
```

---

## 🟡 HERMES USER SYNC & ONBOARDING — PARTIAL STATUS

**File:** `openspec/changes/hermes-user-sync-and-onboarding/tasks.md`

**Claimed Status:** ✅ Done (2026-06-24)  
**Actual Status:** ⚠️ PARTIAL DONE (Core done, redesign in progress)

### What's Actually Done
- [x] T1-T7: Tables + RBAC middleware ✅
- [x] T8.1-T8.4: RLS policies applied ✅
  - 9 policies across 5 tables verified live
  - user_tenants, user_roles, role_permissions, customer_invites, team_invites

### What's Deferred
- [ ] T8.5: Manual non-admin verification (deferred — needs real non-admin test session)
- [ ] T9: Onboarding workflow redesigned from FastAPI → Hermes-native

### Design Redesign (T9)

**Original plan:** Build `CustomerInviteService` + `TeamInviteService` in FastAPI (~6h code)

**Reality:** Original PHASE3B docs said "Hermes operator registers them" → intended executor was always Hermes, not Python

**Decision (2026-06-24):** Go Hermes-native instead
- Cloud layer: RLS on `customer_invites`/`team_invites` (gates by role)
- Local layer: Hermes Swarm role watches invites, executes registration

**Status:** Redesign documented, but not yet implemented

---

## 🟢 WHAT CAN ACTUALLY PROCEED

### Immediate (Ready)
1. ✅ Phase 3, 4, 5 — all archived
2. ✅ Phase 5 Enhancement — archived

### Should NOT Proceed Yet
1. ❌ Hermes Multi-Tenant Wrapper — Phase 1 has 5 critical bugs
2. ⚠️ Hermes User Sync — T9 redesigned, needs implementation

---

## 📋 CORRECT ORDER (GROUND TRUTH)

```
✅ DONE
├─ Phase 3 (T11-T16)
├─ Phase 4 (Agentic Performance)
├─ Phase 5 (Agent Integration)
└─ Phase 5 Enhancement (Agent Ops Multitenant)

🔴 BLOCKED (Fix Required Before Proceeding)
├─ Hermes Multi-Tenant Wrapper
│  └─ Phase 1 has 5 critical bugs (fix T5, T6, T10, T8, T13-T15)
│  └─ Phase 2-3 deferred indefinitely (commercial hold)
│
└─ Hermes User Sync & Onboarding
   └─ T8 RLS done, but T9 needs Hermes-native redesign + implementation

❓ NOT YET INVESTIGATED
├─ contexia-pwa-data-layer-mvp
└─ pwa-hermes-integration
```

---

## 🎯 RECOMMENDED NEXT STEPS

### Week of Jun 24 (URGENT)

1. **Fix Hermes Multi-Tenant Wrapper Phase 1 (2-3 days)**
   - [ ] Remove 3 non-existent table references from migration 0003
   - [ ] Re-run backfill (T6) with correct tenant_id defaults
   - [ ] Implement identity resolver to fix string→UUID cast (reuse from agent-operations)
   - [ ] Write E2E tests (T13-T15)

2. **Implement Hermes User Sync T9 Redesign (1-2 days)**
   - [ ] Design Hermes Swarm role for `onboarding:invite`
   - [ ] Configure Supabase MCP access in Hermes Workspace
   - [ ] Write integration tests

3. **Investigate Remaining OpenSpec (1 day)**
   - [ ] Review contexia-pwa-data-layer-mvp (check if it's blocked on multi-tenant fixes)
   - [ ] Review pwa-hermes-integration (same)

### Week of Jul 1 (IF fixes from Week 1 complete)

- Deploy Hermes Multi-Tenant Wrapper (after all bugs fixed)
- Deploy Hermes User Sync (after T9 redesign done)

---

## 🚨 Root Cause Analysis

Why did these contradictions happen?

1. **Claim → Reality Gap**
   - EXECUTION_STATUS.md made claims without verifying code/DB state
   - tasks.md itself was never marked as "done" (all 28 tasks stayed `⏳ Ready`)
   - Agent that wrote EXECUTION_STATUS may have confused "plan is written" with "plan is executed"

2. **Schema Assumptions**
   - Migration referenced tables that don't exist (template vs. reality)
   - JWT assumed working RLS, but UUID cast breaks it

3. **Deferred Decisions Not Tracked**
   - Phase 2 deferred on commercial hold, but tasks.md not updated
   - Phase 3 deferred for same reason

---

## 📝 Lessons for Future

1. **Ground truth = code + DB, not documents**
   - Always verify with SQL queries + git log, not just README claims
   
2. **Contradictions trigger audit**
   - If EXECUTION_STATUS.md says "done" but tasks.md says `⏳ Ready`, investigate immediately

3. **Defer explicitly**
   - If a phase is blocked/deferred, mark tasks as `[ ] DEFERRED: reason` + update parent task file

4. **Self-improving loop in CLAUDE.md §8**
   - This finding should be added to CHECKPOINTS.md for future OpenSpec deployments

---

## 📌 RECOMMENDATION FOR TODAY

**Do NOT proceed with "Hermes Multi-Tenant Wrapper: Ready to deploy"**

Instead, focus on:
1. **Fixing Phase 1 bugs** (2-3 days of work)
2. **Investigating remaining OpenSpec** to understand true dependencies
3. **Implementing T9 redesign** for User Sync (1-2 days)

Only after bugs are fixed should Phase 1 be considered "ready".

