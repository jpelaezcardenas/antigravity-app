**No prerequisites remain.** All 4 originally-blocking sibling changes are archived on `main`
(`openspec/changes/archive/2026-07-23-{approval-queue-tenant-scoping,
centinela-tenant-scoped-alerts, taty-per-tenant-profiles, hermes-task-queue-tenant-scoping}`).
This change's scope now includes reconciling the inconsistent tenant-resolution approaches they
independently shipped (see design.md) — that means Stages 4-6 below edit already-deployed,
tenant-security-critical production code, not just previously-anonymous routes. Treat every
edit to those 3 files with the same care as a security fix: full existing test suite green
before and after, no silent behavior change beyond the one documented 403→404 policy fix.

## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [ ] 0.1 `git fetch origin main && git rebase origin/main` — confirm all 4 sibling changes are
      present (`git log --oneline | grep -iE "approval-queue-tenant-scoping|
      centinela-tenant-scoped-alerts|taty-per-tenant-profiles|hermes-task-queue-tenant-scoping"`)
- [ ] 0.2 `git branch --show-current` — this checkout runs parallel sessions; re-verify the
      current branch before every commit in this change
- [ ] 0.3 Re-run the grep from design.md's Decision 2 (`grep -rn "resolve_caller_tenant"
      apps/backend`) to reconfirm `centinela_endpoints.py` is still the only caller before
      deleting the helper in Stage 4

## 1. Backend: Auth-gate pure-LLM + demo + task-info routes (TDD)

- [ ] 1.1 Write failing tests in `test_agents_endpoints_auth.py`: each of
      `/social/generate-content`, `/pulso/analyze`, `/centinela/monitor`, `/centinela/decide`,
      `/compliance/audit`, `/orchestrator/full-pipeline`, `/task-info/{task_type}` rejects a
      request with no valid token when `AUTH_ENFORCED=true`, and accepts one with a valid
      token; assert `/orchestrator/full-pipeline`'s response still contains `"mode": "demo"`
- [ ] 1.2 Add `user: dict = Depends(get_current_user)` to all 7 routes in
      `agents_endpoints.py`; no tenant parameter threaded through
- [ ] 1.3 Run `pytest apps/backend/tests/test_agents_endpoints_auth.py -v` and confirm all pass

## 2. Backend: Stub endpoints switch to resolved tenant (TDD)

- [ ] 2.1 Write failing tests in `test_agent_stub_endpoints_tenant.py`: `/summary`
      (`pulso_diario_endpoints.py`) and `/generate-draft` (`centinela_agents_endpoints.py`)
      require auth; a caller with a resolved tenant sees that tenant's UUID in the response;
      no response ever contains the literal string `"default-tenant"`
- [ ] 2.2 Add `user: dict = Depends(get_current_user)` to both routes; resolve tenant via
      `scope = resolve_request_tenant_scope(user, get_service_supabase()); tenant_id =
      scope.tenant_id if scope else None`; remove the
      `getattr(request.state, "tenant_id", "default-tenant")` reads entirely
- [ ] 2.3 Run `pytest apps/backend/tests/test_agent_stub_endpoints_tenant.py -v` and confirm
      all pass

## 3. Backend: Baseline the 3 already-shipped files' test suites before touching them (MANDATORY)

- [ ] 3.1 Run `pytest apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py
      apps/backend/tests/test_centinela_endpoint_tenant_scoping.py
      apps/backend/tests/test_taty_endpoints_tenant_scoping.py
      apps/backend/tests/test_tenant_context_helpers.py
      apps/backend/tests/test_tenant_scope_resolution.py -v` and record the full pass baseline
      — this is the regression net for Stages 4-6

## 4. Backend: Unify tenant-resolution helpers (TDD)

- [ ] 4.1 Write/update failing tests in `test_centinela_endpoint_tenant_scoping.py`: swap the
      monkeypatch target from `presentation.centinela_endpoints.resolve_caller_tenant` to
      `presentation.centinela_endpoints.resolve_request_tenant_scope`, returning a `TenantScope`
      instead of a bare string; existing assertions on the resolved `tenant_id` value and the
      unresolved-caller behavior must still pass
- [ ] 4.2 Update `centinela_endpoints.py`'s 2 call sites (lines ~120, ~195): replace
      `resolve_caller_tenant(user, get_service_supabase())` with
      `scope = resolve_request_tenant_scope(user, get_service_supabase()); tenant_id =
      scope.tenant_id if scope else None`; update the import
- [ ] 4.3 Write/update failing tests in `test_taty_endpoints_tenant_scoping.py`: swap whatever
      mocks Taty's inline resolution branch to mock `resolve_request_tenant_scope` instead;
      assertions on resolved `tenant_id` values and the `error_code="tenant_not_resolved"`
      unresolved-caller response must still pass
- [ ] 4.4 Update `taty_endpoints.py`'s `/ask` handler(s): replace the inline
      `if resolved_tenant_id / elif staging / else` ladder with
      `scope = resolve_request_tenant_scope(user, get_service_supabase())`, keeping the
      existing `tenant_not_resolved` structured response for `scope is None`; delete the
      now-unused file-local `_resolve_cliente_cero_tenant_id()` async helper and its import
- [ ] 4.5 Remove `resolve_caller_tenant` from `core/tenant_context.py`; delete its 3 dedicated
      tests in `test_tenant_context_helpers.py` (superseded by `test_tenant_scope_resolution.py`)
- [ ] 4.6 Run `pytest apps/backend/tests/test_centinela_endpoint_tenant_scoping.py
      apps/backend/tests/test_taty_endpoints_tenant_scoping.py
      apps/backend/tests/test_tenant_context_helpers.py -v` and confirm all pass; diff the
      pass/fail count against Stage 3's baseline — no unexplained change

## 5. Backend: Approval-queue 403 → 404 (TDD)

- [ ] 5.1 Update `test_approval_queue_endpoint_tenant_scoping.py`: rename and update
      `test_authenticated_unresolved_enqueue_returns_403_never_cliente_cero`,
      `test_approve_unresolved_returns_403`, `test_reject_unresolved_returns_403` to assert
      HTTP 404; update the docstring table (lines ~14-16) describing the 403 policy
- [ ] 5.2 In `approval_queue_endpoints.py`, change the 3 `HTTPException(status_code=403, ...)`
      call sites (enqueue, approve, reject) to `status_code=404`; update the inline comments at
      lines ~131/185 describing the old 403 policy
- [ ] 5.3 Run `pytest apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py -v` and
      confirm all pass; diff against Stage 3's baseline

## 6. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [ ] 6.1 Grep all existing test files that call any of the 6 in-scope endpoint functions
      directly (bypassing `Depends(get_current_user)`) and update them to pass a fake `user`
      dict, matching the pattern in `test_financials_endpoint_tenant_scoping.py`
- [ ] 6.2 Grep the full repo (not just `apps/backend/tests/`) for any other caller of
      `resolve_caller_tenant` or Taty's deleted `_resolve_cliente_cero_tenant_id` that Stage 0.3
      and Stage 4.5 might have missed

## 7. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 7.1 Capture pre-test database baseline for any hermetic two-tenant fixture used
- [ ] 7.2 Run all targeted test files added/updated in Stages 1-6
- [ ] 7.3 Run the full backend suite (from `apps/backend/` as cwd) and compare pass/fail counts
      against Stage 3's baseline — any new failure must be explained, not silently accepted
- [ ] 7.4 Verify post-test database state for hermetic fixtures (teardown leaves no residue)
- [ ] 7.5 Create report
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/YYYY-MM-DD-step-7-unit-test-and-db-verification.md`

## 8. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 8.1 Start the backend server locally
- [ ] 8.2 For each of the 6 in-scope files' routes: `curl` with no token (expect 401 under
      `AUTH_ENFORCED=true`), then with a valid session token (expect success)
- [ ] 8.3 For `approval_queue_endpoints.py` (`/enqueue`, `/approve`, `/reject`): curl with a
      token whose tenant is unresolved and confirm 404 (was 403)
- [ ] 8.4 For `centinela_endpoints.py` and `taty_endpoints.py`: curl with a token whose tenant
      is unresolved and confirm the observable response is unchanged from the pre-migration
      baseline (empty alerts / `error_code="tenant_not_resolved"`)
- [ ] 8.5 Restore any database state altered during manual testing
- [ ] 8.6 Document all curl commands and responses in
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/YYYY-MM-DD-step-8-curl-verification.md`

## 9. Documentation (MANDATORY)

- [ ] 9.1 Update `AGENTES.md:324` from "Direct HTTP calls to agents: BYPASS governance" to
      reflect that direct HTTP is now authenticated + tenant-scoped through one canonical
      helper, but still not cost-governed (per design.md's governance-limitation section)
- [ ] 9.2 Update `ARCHITECTURE.md` Decision #15 to mark the two-helper reconciliation done,
      citing this change
- [ ] 9.3 Update `docs/API_REFERENCE.md` (or equivalent) to document the auth requirement on
      the 2 previously-anonymous files' routes and the 404 (was 403) policy on approval-queue
- [ ] 9.4 Confirm no other `ARCHITECTURE.md` change is needed — no new container, no new
      external dependency — and record that determination

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
