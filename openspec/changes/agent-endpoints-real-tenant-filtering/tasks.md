**IMPLEMENTATION DEFERRED.** As of 2026-07-23, all four hard prerequisites
(`approval-queue-tenant-scoping`, `centinela-tenant-scoped-alerts`, `taty-per-tenant-profiles`,
`hermes-task-queue-tenant-scoping`) are in active drafting in parallel worktrees on this
checkout — none archived or merged. **Do not start Stages 4-6 until the hard prerequisites
they name are archived.** Stages 1-3 have no seam dependency and MAY be pulled forward with
an explicit leader decision, but must still respect the harness's one-active-change invariant
(`feature_list.json`) before marking themselves `in_progress`.

## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [ ] 0.1 Verify prerequisites' actual merge state before starting any implementation stage:
      `git log main --oneline | grep -iE "approval-queue-tenant-scoping|centinela-tenant-scoped-alerts|taty-per-tenant-profiles|hermes-task-queue-tenant-scoping"` and check
      `openspec/changes/archive/` for each — record findings in the branch's first commit
      message or a progress note
- [ ] 0.2 Create feature branch `feature/agent-endpoints-real-tenant-filtering` from an
      updated `main` (or from the latest merged prerequisite branch if Stages 4-6 are
      starting and their base hasn't reached `main` yet)
- [ ] 0.3 Verify branch creation and current branch status (`git status`,
      `git branch --show-current`) — this checkout runs parallel sessions; re-verify the
      current branch before every commit

## 1. Backend: Auth-gate pure-LLM + demo + task-info routes (TDD) [UNGATED]

- [ ] 1.1 Write failing tests in `test_agents_endpoints_auth.py`: each of
      `/social/generate-content`, `/pulso/analyze`, `/centinela/monitor`, `/centinela/decide`,
      `/compliance/audit`, `/orchestrator/full-pipeline`, `/task-info/{task_type}` rejects a
      request with no valid token when `AUTH_ENFORCED=true`, and accepts one with a valid
      token; assert `/orchestrator/full-pipeline`'s response still contains `"mode": "demo"`
- [ ] 1.2 Add `user: dict = Depends(get_current_user)` to all 7 routes in
      `agents_endpoints.py` above; no tenant parameter threaded through
- [ ] 1.3 Run `pytest apps/backend/tests/test_agents_endpoints_auth.py -v` and confirm all pass

## 2. Backend: Stub endpoints switch to resolved tenant (TDD) [UNGATED]

- [ ] 2.1 Write failing tests in `test_agent_stub_endpoints_tenant.py`: `/summary`
      (`pulso_diario_endpoints.py`) and `/generate-draft` (`centinela_agents_endpoints.py`)
      require auth; a caller with a resolved tenant sees that tenant's UUID in the response;
      no response ever contains the literal string `"default-tenant"`
- [ ] 2.2 Add `user: dict = Depends(get_current_user)` to both routes and resolve tenant via
      whatever `core/tenant_context.py` helper exists at implementation time (see design.md's
      note on the emerging `resolve_request_tenant_scope`); remove the
      `getattr(request.state, "tenant_id", "default-tenant")` reads entirely
- [ ] 2.3 Run `pytest apps/backend/tests/test_agent_stub_endpoints_tenant.py -v` and confirm
      all pass

## 3. Backend: Deprecated /taty/ask auth gate only (TDD) [UNGATED]

- [ ] 3.1 Write a failing test: `agents_endpoints.py::/taty/ask` (the deprecated route)
      requires auth
- [ ] 3.2 Add `user: dict = Depends(get_current_user)` — full tenant-derivation for this
      route is Stage 4 territory once `taty-per-tenant-profiles` lands; this step only closes
      the anonymous-access gap
- [ ] 3.3 Run the targeted test and confirm it passes

## 4. Backend: Taty tenant-derived company context (TDD) [GATED: taty-per-tenant-profiles]

- [ ] 4.1 Confirm `TatyService.ask` accepts a `tenant_id` parameter per the merged sibling
      change; adjust this task's approach if the actual signature differs from design.md's
      seam contract
- [ ] 4.2 Write failing tests in `test_taty_endpoints_tenant_scoping.py`: a caller with a
      resolved tenant and no `company_id` gets the company derived from that tenant; a caller
      supplying a `company_id` belonging to another tenant gets HTTP 404
- [ ] 4.3 Update `taty_endpoints.py::/ask` and `agents_endpoints.py::/taty/ask` to derive
      company from the resolved tenant instead of trusting the client-supplied field
- [ ] 4.4 Run `pytest apps/backend/tests/test_taty_endpoints_tenant_scoping.py -v` and confirm
      all pass

## 5. Backend: Centinela evaluate/alerts tenant scoping (TDD) [GATED: centinela-tenant-scoped-alerts]

- [ ] 5.1 Confirm `CentinelaService.save_alerts` accepts a `tenant_id` parameter per the
      merged sibling change; adjust if the actual signature differs
- [ ] 5.2 Write failing tests in `test_centinela_endpoints_tenant_scoping.py`: alerts saved
      via `/evaluate` carry the caller's resolved tenant, not Cliente Cero; `GET
      /alerts/{company_id}` returns HTTP 404 for a company belonging to another tenant
- [ ] 5.3 Update `centinela_endpoints.py::/evaluate` and `/alerts/{company_id}` to pass/verify
      tenant_id
- [ ] 5.4 Run `pytest apps/backend/tests/test_centinela_endpoints_tenant_scoping.py -v` and
      confirm all pass

## 6. Backend: Approval queue list/enqueue/approve/reject (TDD) [GATED: approval-queue-tenant-scoping]

- [ ] 6.1 Confirm `ApprovalQueueService.enqueue_draft`/`approve_draft`/`reject_draft` accept
      `tenant_id` per the merged sibling change; adjust if the actual signature differs
- [ ] 6.2 Write failing tests in `test_approval_queue_tenant_scoping.py`: two tenants with
      their own drafts see disjoint `GET ""` results; an unresolved authenticated caller sees
      an empty list; an enqueued draft carries the caller's tenant; approve/reject on another
      tenant's draft returns HTTP 404
- [ ] 6.3 Update `approval_queue_endpoints.py`'s 4 routes to pass the resolved tenant_id
      through to the service layer
- [ ] 6.4 Run `pytest apps/backend/tests/test_approval_queue_tenant_scoping.py -v` and confirm
      all pass

## 7. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [ ] 7.1 Grep all existing test files that call any of the six in-scope endpoint functions
      directly (bypassing the new `Depends(get_current_user)`) and update them to pass a fake
      `user` dict, matching the pattern in `test_financials_endpoint_tenant_scoping.py`
- [ ] 7.2 Confirm no other production caller of the changed endpoint functions exists beyond
      what was already found in this session's exploration

## 8. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 8.1 Capture pre-test database baseline for any hermetic two-tenant fixture used
- [ ] 8.2 Run all targeted test files added/updated in Stages 1-7
- [ ] 8.3 Run the full backend suite (from `apps/backend/` as cwd) and compare
      pass/fail counts against the pre-change baseline — any new failure must be explained,
      not silently accepted
- [ ] 8.4 Verify post-test database state for hermetic fixtures (teardown leaves no residue)
- [ ] 8.5 Create report
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/YYYY-MM-DD-step-8-unit-test-and-db-verification.md`

## 9. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 9.1 Start the backend server locally
- [ ] 9.2 For each of the six in-scope files' routes: `curl` with no token (expect 401 under
      `AUTH_ENFORCED=true`), then with a valid session token (expect success); for the
      DB-touching routes, also curl a cross-tenant resource id (expect 404)
- [ ] 9.3 Restore any database state altered during manual testing
- [ ] 9.4 Document all curl commands and responses in
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/YYYY-MM-DD-step-9-curl-verification.md`

## 10. Documentation (MANDATORY)

- [ ] 10.1 Update `AGENTES.md:324` from "Direct HTTP calls to agents: BYPASS governance" to
      reflect that direct HTTP is now authenticated + tenant-scoped, but still not
      cost-governed (per design.md's governance-limitation section)
- [ ] 10.2 Update `docs/API_REFERENCE.md` (or equivalent) to document the new auth
      requirement on all six presentation files' routes
- [ ] 10.3 Confirm no `ARCHITECTURE.md` change is needed — no new container, no new external
      dependency — and record that determination

## 11. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 11.1 git commit + push (classifier may block a direct push to `main` — hand off to the
      founder if so)
- [ ] 11.2 Railway deploy active and green
- [ ] 11.3 Smoke-test at least one newly-gated route in production with a real session token
      (expect success) and with no token (expect 401)
- [ ] 11.4 Create report:
      `openspec/changes/agent-endpoints-real-tenant-filtering/reports/YYYY-MM-DD-deployment.md`

## 12. Review Gate

- [ ] 12.1 `reviewer` agent validates against all three spec deltas in `specs/`, `design.md`'s
      decisions (especially the 404-vs-403 policy and the demo-pipeline preservation), no
      hardcoded secrets, English-only, no scope creep into `sell_machine_endpoints.py` or
      `services/operator_task_service.py`
- [ ] 12.2 `RUN_TESTS=1 bash init.sh` green before marking ready to archive
