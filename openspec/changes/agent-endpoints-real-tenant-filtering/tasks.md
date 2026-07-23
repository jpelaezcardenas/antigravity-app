**No prerequisites remain.** All 4 originally-blocking sibling changes are archived on `main`
(`openspec/changes/archive/2026-07-23-{approval-queue-tenant-scoping,
centinela-tenant-scoped-alerts, taty-per-tenant-profiles, hermes-task-queue-tenant-scoping}`).
This change's scope now includes reconciling the inconsistent tenant-resolution approaches they
independently shipped (see design.md) — that means Stages 4-6 below edit already-deployed,
tenant-security-critical production code, not just previously-anonymous routes. Treat every
edit to those 3 files with the same care as a security fix: full existing test suite green
before and after, no silent behavior change beyond the one documented 403→404 policy fix.

## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Rebased onto `origin/main`; confirmed all 4 sibling changes archived
      (`openspec/changes/archive/2026-07-23-{approval-queue-tenant-scoping,
      centinela-tenant-scoped-alerts,taty-per-tenant-profiles,hermes-task-queue-tenant-scoping}`)
- [x] 0.2 `git branch --show-current` = `feature/agent-endpoints-real-tenant-filtering`,
      re-verified before each commit
- [x] 0.3 Grep confirmed `centinela_endpoints.py` was the only production caller of
      `resolve_caller_tenant` before Stage 4 deleted it

## 1. Backend: Auth-gate pure-LLM + demo + task-info routes (TDD)

- [x] 1.1 Failing tests written in `test_agents_endpoints_auth.py`: signature-inspects each of
      the 7 routes for a `user: dict = Depends(get_current_user)` parameter, plus a
      direct-call assertion that `/orchestrator/full-pipeline` still returns `"mode": "demo"`
- [x] 1.2 Added `user: dict = Depends(get_current_user)` to all 7 routes in
      `agents_endpoints.py`; no tenant parameter threaded through
- [x] 1.3 `pytest tests/test_agents_endpoints_auth.py -v` — 2/2 passed

## 2. Backend: Stub endpoints switch to resolved tenant (TDD)

- [x] 2.1 Failing tests written in `test_agent_stub_endpoints_tenant.py` (both auth-signature
      and tenant-resolution scenarios, incl. never-"default-tenant")
- [x] 2.2 Both routes now take `user: dict = Depends(get_current_user)` and resolve via
      `scope = resolve_request_tenant_scope(user, get_service_supabase())`; the
      `getattr(request.state, "tenant_id", "default-tenant")` reads are gone
- [x] 2.3 `pytest tests/test_agent_stub_endpoints_tenant.py -v` — 6/6 passed

## 3. Backend: Baseline the 3 already-shipped files' test suites before touching them (MANDATORY)

- [x] 3.1 Baseline recorded: 36/36 passed across the 5 files before touching them

## 4. Backend: Unify tenant-resolution helpers (TDD)

- [x] 4.1 Updated `test_centinela_endpoint_tenant_scoping.py`: added an autouse fixture
      stubbing `resolve_cliente_cero_tenant_id` (called unconditionally by
      `resolve_request_tenant_scope`, unlike the removed helper — a real behavior difference
      documented in the file's own docstring), confirmed red before the endpoint migration
- [x] 4.2 Migrated `centinela_endpoints.py`'s 2 call sites to
      `scope = resolve_request_tenant_scope(...); tenant_id = scope.tenant_id if scope else None`
- [x] 4.3 Updated `test_taty_endpoints_tenant_scoping.py` the same way (autouse stub for
      `resolve_cliente_cero_tenant_id`); confirmed red (real Supabase call attempted) before
      the migration
- [x] 4.4 Migrated `taty_endpoints.py`'s `/ask` handler to `resolve_request_tenant_scope`;
      deleted the file-local async `_resolve_cliente_cero_tenant_id()` and its now-unused
      `_STAGING_USER` import
- [x] 4.5 Removed `resolve_caller_tenant` from `core/tenant_context.py`; deleted its 3
      dedicated tests from `test_tenant_context_helpers.py`; corrected a stale comment in
      `test_tenant_stamping.py` that still named the removed helper as future work
- [x] 4.6 `pytest tests/test_centinela_endpoint_tenant_scoping.py
      tests/test_taty_endpoints_tenant_scoping.py tests/test_tenant_context_helpers.py
      tests/test_tenant_scope_resolution.py tests/test_tenant_stamping.py -v` — 24/24 passed,
      no unexplained change vs Stage 3's baseline

## 5. Backend: Approval-queue 403 → 404 (TDD)

- [x] 5.1 Renamed/updated the 3 tests to assert HTTP 404; updated the docstring table
      describing the policy; confirmed red (403 != 404) before the code change
- [x] 5.2 Changed the 3 `HTTPException(status_code=403, ...)` call sites (enqueue, approve,
      reject) to `status_code=404`; updated the inline docstring comments
- [x] 5.3 `pytest tests/test_approval_queue_endpoint_tenant_scoping.py -v` — 14/14 passed

## 6. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 6.1 Grepped all test files touching the 6 in-scope modules — only the 4 already-updated
      files call them directly; no other test bypasses the new `Depends`
- [x] 6.2 Grepped the full repo for `resolve_caller_tenant` (none remain outside comments
      referencing the removal) and for the deleted Taty helper (none remain)

## 7. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [x] 7.1 N/A — no hermetic DB fixtures in this change's scope (see report)
- [x] 7.2 All targeted files green
- [x] 7.3 Full suite: 40 failed/671 passed/112 skipped/13 errors, vs baseline (unmodified code)
      40 failed/666 passed/112 skipped/13 errors — **identical failure/error sets**, +5 passes
      fully explained by net new/removed tests
- [x] 7.4 N/A — no hermetic fixtures used
- [x] 7.5 Report:
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/2026-07-23-step-7-unit-test-and-db-verification.md`

## 8. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [x] 8.1 Backend started locally (`uvicorn`, zero Supabase credentials, `AUTH_ENFORCED=False`)
- [x] 8.2 Verified for the 2 auth-gate-only routes reachable without real credentials
      (`task-info`, `orchestrator/full-pipeline`) — both `200`, demo payload unchanged
- [ ] 8.3 **DEFERRED to Stage 10** — requires a real Supabase-issued JWT + `AUTH_ENFORCED=true`,
      unavailable in this credential-less local checkout (same precedent as
      `taty-per-tenant-profiles` tasks 8.3-8.5)
- [ ] 8.4 **DEFERRED to Stage 10** — same reason as 8.3
- [x] 8.5 No database state was altered (all local calls either succeeded read-only or 500'd
      before any write)
- [x] 8.6 Report:
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/2026-07-23-step-8-curl-verification.md`
      — also documents the confirmed-pre-existing local `SupabaseException: supabase_url is
      required` gap affecting every `resolve_request_tenant_scope` call site, old and new

## 9. Documentation (MANDATORY)

- [x] 9.1 `AGENTES.md:324` updated: "BYPASS governance" → authenticated + tenant-scoped via one
      canonical helper, still not cost-governed
- [x] 9.2 `ARCHITECTURE.md` Decision #15 updated (helper migrated, reconciliation done); new
      Decision #16 records the unification + 403→404 alignment
- [x] 9.3 `docs/API_REFERENCE.md` given an accurate current-state note (the pre-existing doc
      body predates this and several other changes and was not fully resynced — flagged
      explicitly rather than silently trusted)
- [x] 9.4 No new container/external dependency — recorded via Decision #16, no further
      `ARCHITECTURE.md` change needed

## 10. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 10.1 git commit + push (classifier may block a direct push to `main` — hand off to the
      founder if so)
- [ ] 10.2 Railway deploy active and green
- [ ] 10.3 Smoke-test in production: one newly-gated route (expect 401 with no token, success
      with one); one of the 3 migrated routes (approval-queue enqueue with an unresolved-tenant
      token, expect 404)
- [ ] 10.4 Create report:
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/YYYY-MM-DD-deployment.md`

## 11. Review Gate

- [ ] 11.1 `reviewer` agent validates against all 4 spec deltas in `specs/`, `design.md`'s
      decisions (especially the helper unification and 403→404 policy), no hardcoded secrets,
      English-only, no scope creep into `sell_machine_endpoints.py` or
      `services/operator_task_service.py`
- [ ] 11.2 `RUN_TESTS=1 bash init.sh` green before marking ready to archive
