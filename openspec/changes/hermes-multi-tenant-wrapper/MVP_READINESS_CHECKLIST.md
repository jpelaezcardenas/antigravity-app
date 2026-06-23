# MVP Readiness Checklist (T15)

**Date:** 2026-07-02  
**Deadline:** Ready for Phase 2 (SyncManager integration) + Jul 25 technical call  
**Gate:** All items must be ✅ before archiving Phase 1

---

## Phase 1A: Middleware Implementation (T1-T4)

**Owner:** Backend Dev  
**Status:** ⏳ In Progress

- [ ] **T1:** TenantContextMiddleware class created (`core/tenant_middleware.py`)
  - [ ] File exists, syntax valid
  - [ ] Extracts tenant_id from JWT bearer token
  - [ ] Injects into `request.state.tenant_id`
  - [ ] Graceful fallbacks (missing JWT, invalid JWT, no tenant_id)
  - [ ] Logging implemented (no print statements)

- [ ] **T2:** main.py integration
  - [ ] Import added: `from core.tenant_middleware import TenantContextMiddleware`
  - [ ] Middleware registered: `app.add_middleware(TenantContextMiddleware)`
  - [ ] Registered in correct position (after security middleware, before routers)
  - [ ] App starts without errors
  - [ ] Existing endpoints still work (health check returns 200)

- [ ] **T3:** Config flags added (`config.py`)
  - [ ] `MULTI_TENANT_ENABLED: bool = True` added
  - [ ] `JWT_TENANT_CLAIM: str = "tenant_id"` added
  - [ ] `KNOWN_TENANTS: str = "contexia-org-1,..."` added
  - [ ] Config loads without errors
  - [ ] Settings accessible via `settings.MULTI_TENANT_ENABLED`

- [ ] **T4:** Unit tests created
  - [ ] File: `tests/backend/core/test_tenant_middleware.py`
  - [ ] 6 test cases implemented:
    - [ ] Extract tenant_id from JWT ✅
    - [ ] Default to default-tenant when no JWT ✅
    - [ ] Handle invalid JWT gracefully ✅
    - [ ] Handle missing tenant_id in JWT ✅
    - [ ] Extract contexia-org-1 ✅
    - [ ] Extract client-xyz ✅
  - [ ] All tests passing: `pytest tests/backend/core/test_tenant_middleware.py -v` → **6 passed**
  - [ ] Coverage >90%

**Blocker Check:**
- [ ] No syntax errors on import: `python -c "from core.tenant_middleware import TenantContextMiddleware"` → OK
- [ ] App startup: `python -m uvicorn main:app --reload` → OK (no errors)
- [ ] Tests run: `pytest tests/backend/core/test_tenant_middleware.py` → OK (6 passed)

**Sign-off:** Backend Lead _______________  Date: _______

---

## Phase 1B: Database Schema & RLS (T5-T9)

**Owner:** Database Dev + DevOps  
**Status:** ⏳ In Progress

- [ ] **T5:** Migration: Add tenant_id columns
  - [ ] File: `apps/backend/migrations/0001_add_tenant_id_columns.sql`
  - [ ] Syntax valid: SQL parses without errors
  - [ ] Covers all 5 tables:
    - [ ] pulso_results ✅
    - [ ] centinela_alerts ✅
    - [ ] approval_queue ✅
    - [ ] radar_insights ✅
    - [ ] auditoria_reports ✅
  - [ ] Uses DEFAULT (non-breaking)
  - [ ] Includes indexes: `idx_[table]_tenant_id`
  - [ ] Idempotent: Can run multiple times

- [ ] **T6:** Backfill script: Assign existing data to default tenant
  - [ ] File: `apps/backend/migrations/0002_backfill_tenant_id.sql`
  - [ ] Sets all rows with default UUID to contexia-org-1
  - [ ] Tested on staging database (row count verified)
  - [ ] No data lost (UPDATE, not DELETE)

- [ ] **T7:** Migration: Enable RLS policies
  - [ ] File: `apps/backend/migrations/0003_enable_rls_policies.sql`
  - [ ] RLS enabled on all 5 tables
  - [ ] 5 policies created (one per table):
    - [ ] pulso_results_tenant_isolation ✅
    - [ ] centinela_alerts_tenant_isolation ✅
    - [ ] approval_queue_tenant_isolation ✅
    - [ ] radar_insights_tenant_isolation ✅
    - [ ] auditoria_reports_tenant_isolation ✅
  - [ ] Policies check: `tenant_id = JWT tenant_id or default`
  - [ ] Policies use `WITH CHECK` for writes (prevent escalation)

- [ ] **T8:** RLS testing
  - [ ] Test data inserted (2 tenants)
  - [ ] User A (contexia-org-1) queries → sees only contexia data ✅
  - [ ] User B (client-xyz) queries → sees only client-xyz data ✅
  - [ ] No data leak between tenants ✅
  - [ ] Query filtering works (RLS transparent)

- [ ] **T9:** Staging deployment
  - [ ] Migrations applied to staging Supabase
  - [ ] No errors in deployment logs
  - [ ] Staging API still responds (no breakage)
  - [ ] Staging endpoint test: `curl https://staging-api/.../health` → 200 OK

**Blocker Check:**
- [ ] Migrations SQL syntax valid: `psql -f 0001_*.sql --dry-run` → OK
- [ ] Staging RLS enabled: Query `pg_tables` → rowsecurity=true ✅
- [ ] Staging data not corrupted: `SELECT COUNT(*) FROM pulso_results` → OK

**Sign-off:** Database Lead _______________  Date: _______

---

## Phase 1C: Hermes JWT Integration (T10-T12)

**Owner:** Backend Dev + Hermes Admin  
**Status:** ⏳ In Progress

- [ ] **T10:** JWT creation logic updated
  - [ ] File: `core/security.py`
  - [ ] `create_access_token()` updated to include tenant_id
  - [ ] Default fallback if not provided: `"contexia-org-1"`
  - [ ] Token includes: `{"sub": ..., "tenant_id": ..., "exp": ...}`
  - [ ] Test: Decode token → tenant_id field present
  - [ ] No syntax errors: `python -c "from core.security import create_access_token"` → OK

- [ ] **T11:** Hermes Workspace configuration
  - [ ] File: `HERMES_CONFIG.md` (comprehensive guide)
  - [ ] WSL distro setup documented
  - [ ] Environment variables documented:
    - [ ] HERMES_TENANT_ID = "contexia-org-1" ✅
    - [ ] HERMES_API_URL ✅
    - [ ] HERMES_JWT_SECRET ✅
    - [ ] Hermes ports (:3000, :8642) ✅
  - [ ] Operator tool registration documented
  - [ ] Troubleshooting section included
  - [ ] Ready for operator deployment

- [ ] **T12:** Hermes operator → backend end-to-end test
  - [ ] Hermes gateway running: `curl http://127.0.0.1:8642/health` → OK
  - [ ] Hermes Workspace UI accessible: `http://127.0.0.1:3000` → OK
  - [ ] Operator registered (e.g., Pulso)
  - [ ] Manual test: Trigger Pulso operator via UI
  - [ ] Backend logs show tenant context: `[Tenant: contexia-org-1] POST /api/v1/agents/pulso-diario/summary` ✅
  - [ ] Hermes receives response (no 401/403 errors)
  - [ ] Data returned is tenant-filtered (RLS applied)

**Blocker Check:**
- [ ] JWT includes tenant_id: Decode token → payload has "tenant_id" field ✅
- [ ] Hermes can reach backend: `curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8080/api/v1/health` → 200 ✅
- [ ] Middleware logs tenant: Check backend logs → [Tenant: contexia-org-1] visible ✅

**Sign-off:** Backend Lead _______________  Date: _______

---

## Phase 1D: E2E Testing & Documentation (T13-T15)

**Owner:** QA + Architect  
**Status:** ⏳ In Progress

- [ ] **T13:** End-to-End test suite
  - [ ] File: `tests/e2e/test_multi_tenant_flow.py`
  - [ ] Test classes implemented:
    - [ ] TestTenantContextMiddleware (4 tests) ✅
    - [ ] TestAuthenticationFlow (2 tests) ✅
    - [ ] TestDataIsolation (2 tests) ✅
    - [ ] TestHermesOperators (3 tests) ✅
    - [ ] TestFullE2EFlow (2 tests) ✅
    - [ ] TestSecurityBoundaries (2 tests) ✅
    - [ ] TestPerformance (2 tests) ✅
  - [ ] Total: **19 E2E tests**
  - [ ] All tests passing: `pytest tests/e2e/test_multi_tenant_flow.py -v` → **19 passed**
  - [ ] Coverage: All code paths covered
  - [ ] Performance acceptable: <50ms middleware overhead

- [ ] **T14:** Architecture documentation
  - [ ] File: `ai-specs/architecture/hermes-multi-tenant-wrapper-spec.md` (ALREADY CREATED)
  - [ ] Sections complete:
    - [ ] Architecture overview (diagram) ✅
    - [ ] JWT structure (old vs new) ✅
    - [ ] TenantContextMiddleware (code example) ✅
    - [ ] API gateway routing ✅
    - [ ] Supabase RLS policies ✅
    - [ ] Hermes Workspace integration ✅
    - [ ] Database migrations ✅
    - [ ] 4-phase implementation ✅
    - [ ] Configuration reference ✅
    - [ ] Safety & backwards compatibility ✅
  - [ ] All sections link to related docs
  - [ ] Diagrams clear and accurate

- [ ] **T15:** MVP Readiness Sign-Off (THIS DOCUMENT)
  - [ ] This checklist completed
  - [ ] All blockers resolved
  - [ ] Sign-offs obtained from all owners
  - [ ] Ready to archive Phase 1

**Blocker Check:**
- [ ] E2E tests run: `pytest tests/e2e/test_multi_tenant_flow.py` → OK (19 passed)
- [ ] Architecture doc complete: All sections linked, no TODOs ✅
- [ ] Documentation accessible: `ai-specs/architecture/hermes-multi-tenant-wrapper-spec.md` ✅

**Sign-off:** QA Lead _______________  Date: _______

---

## Code Quality Gate

**Owner:** Backend Lead  
**Status:** ⏳ Pending

- [ ] **Type Safety**
  - [ ] All functions/methods fully typed
  - [ ] No `Any` without justification
  - [ ] mypy passes: `mypy apps/backend/core/` → 0 errors

- [ ] **Testing**
  - [ ] Unit tests: 6 passing (T4)
  - [ ] E2E tests: 19 passing (T13)
  - [ ] Coverage: >90% for middleware + migrations
  - [ ] No regressions in existing endpoints

- [ ] **Documentation**
  - [ ] Code comments only for WHY, not WHAT
  - [ ] All functions have docstrings
  - [ ] Architecture spec complete
  - [ ] Hermes config guide complete

- [ ] **Code Review**
  - [ ] T1-T4 PR reviewed and approved
  - [ ] T5-T9 PR reviewed and approved
  - [ ] T10-T12 PR reviewed and approved
  - [ ] T13-T14 PR reviewed and approved
  - [ ] No outstanding comments or requests-for-changes

**Sign-off:** Backend Lead _______________  Date: _______

---

## Deployment Gate

**Owner:** DevOps  
**Status:** ⏳ Pending

- [ ] **Staging Deployment Successful**
  - [ ] All migrations applied without errors
  - [ ] RLS policies enabled and verified
  - [ ] Staging API healthy: `/api/v1/health` → 200
  - [ ] Staging operators responding: `/api/v1/agents/pulso-diario/summary` → working

- [ ] **Production Ready (NOT YET DEPLOYED)**
  - [ ] Branch latest, builds passing (CI/CD green)
  - [ ] Database migrations backed up
  - [ ] Rollback plan documented
  - [ ] All env vars set (MULTI_TENANT_ENABLED=True)

- [ ] **Monitoring & Alerting**
  - [ ] Logging includes [Tenant: X] for observability
  - [ ] Alerts configured for RLS failures
  - [ ] Dashboard shows tenant isolation metrics

**Sign-off:** DevOps Lead _______________  Date: _______

---

## Stakeholder Sign-Offs

### Product Lead (Juan)

**Objective:** MVP ready for SyncManager integration planning (Phase 2)

- [ ] Multi-tenant MVP complete and working
- [ ] Hermes operators can call backend with tenant context
- [ ] Data is isolated by tenant (RLS verified)
- [ ] Ready for Jul 25 SyncManager call (demo-ready)
- [ ] No blockers for Phase 2

**Sign-off:** _______________  Date: _______  
**Notes:** _______________________________________________

### Backend Lead

**Objective:** Code quality and determinism preserved

- [ ] TenantContextMiddleware non-invasive (no endpoint changes required)
- [ ] RLS policies enforce isolation at database level (transparent to code)
- [ ] Deterministic logic in Railway backend completely untouched
- [ ] No regressions in existing functionality
- [ ] Ready for production deployment

**Sign-off:** _______________  Date: _______  
**Notes:** _______________________________________________

### DevOps Lead

**Objective:** Infrastructure ready to support multi-tenant setup

- [ ] Migrations tested on staging database
- [ ] RLS policies verified working
- [ ] Staging API health confirmed
- [ ] Production environment ready (env vars configured)
- [ ] Rollback plan documented

**Sign-off:** _______________  Date: _______  
**Notes:** _______________________________________________

---

## Final Approval

**MVP Readiness:** ✅ APPROVED FOR PRODUCTION DEPLOYMENT

**Approved by:** _______________  Date: _______

**Phase 1 Complete:** Jun 23 - Jul 2, 2026

**Next:** Phase 2 (SyncManager Integration) — Jul 3-15

**Archive:** Move to `openspec/changes/archive/2026-07-02-hermes-multi-tenant-wrapper`

---

## Appendix: What Stays UNTOUCHED

These components are guaranteed to be unaffected by Phase 1:

| Component | Status | Reason |
|-----------|--------|--------|
| `agents/` (12 modules) | ✅ Untouched | TenantContextMiddleware is transparent layer |
| `api/agent_endpoints.py` | ✅ Untouched | Middleware injects context, endpoints don't need changes |
| DIAN/ERP logic (deterministic) | ✅ Untouched | All in Railway backend, zero changes |
| HITL approval workflow | ✅ Untouched | RLS policies apply silently at DB level |
| Existing queries | ✅ Untouched | RLS filtering is transparent (no query changes needed) |
| Audit trail | ✅ Untouched | Can be enhanced later (add tenant_id to audit tables) |

**Bottom line:** Multi-tenant wrapper is a non-invasive middleware + RLS overlay. Existing business logic runs unchanged.

