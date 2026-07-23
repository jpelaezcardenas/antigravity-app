# Tasks: hermes-task-queue-tenant-scoping

## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/hermes-task-queue-tenant-scoping` from updated `main`
- [x] 0.2 Verify branch creation and current branch status (`git branch --show-current`)

## 1. Backend: Service-Layer Tests (TDD)

- [ ] 1.1 `core/tenant_context.py`: add test(s) for new `tenant_exists(client, tenant_id)` helper
      (mocked client, exists=True/False cases) — additive file, do not touch
      `resolve_cliente_cero_tenant_id`
- [ ] 1.2 `tests/test_operator_task_service.py` — `TestCreateTask`: explicit valid `tenant_id` is
      stamped directly (Cliente Cero resolver NOT called); unknown `tenant_id` → rejected, no
      insert; omitted `tenant_id` → Cliente Cero fallback + `caplog` WARNING assertion; omitted
      `tenant_id` AND resolver returns `None` → explicit error, no insert
- [ ] 1.3 `TestListPendingTasks`: assert explicit column projection (not `"*"`); `tenant_id` filter
      applied when passed / absent when omitted
- [ ] 1.4 `TestDispatchCampaignPackage` — FIRST fix the `_fake_decision()` MagicMock truthiness
      trap: every existing test must explicitly set `decision.tenant_id = None` unless it's
      testing the real-tenant path (a bare Mock auto-attribute is truthy and would silently start
      exercising the wrong branch otherwise). THEN add: real `decision.tenant_id` → stamped
      directly, resolver not called; `decision.tenant_id = None` → resolver called + WARNING
      logged

## 2. Backend: Service-Layer Implementation

- [ ] 2.1 `core/tenant_context.py`: add `tenant_exists(client, tenant_id) -> bool`
- [ ] 2.2 `operator_task_service.create_task()`: add optional `tenant_id` param; validate via
      `tenant_exists` when provided (reject with `"tenant {id} not found"` on failure — routes
      through the existing `_raise_for_error` 404 mapping); fall back to
      `_resolve_cliente_cero_tenant_id` + `logger.warning(...)` when omitted; explicit error when
      the resolver also returns `None`
- [ ] 2.3 `operator_task_service.list_pending_tasks()`: add optional `tenant_id` param
      (conditional `.eq("tenant_id", ...)`); replace `select("*")` with explicit projection
      `"id, tenant_id, task_type, payload, status, created_at"`
- [ ] 2.4 `operator_task_service.dispatch_campaign_package()`: derive tenant from
      `getattr(decision, "tenant_id", None)`; fall back to `_resolve_cliente_cero_tenant_id` +
      `logger.warning(...)` only when falsy
- [ ] 2.5 Run 1.1-1.4 tests green

## 3. Backend: Endpoint-Layer Tests (TDD)

- [ ] 3.1 `tests/test_operator_task_endpoints.py`: `POST /tasks` with `tenant_id` in body →
      service called with that value; omitted → service called with `tenant_id=None`
- [ ] 3.2 `GET /tasks/pending?tenant_id=x` → service called with `tenant_id="x"`
- [ ] 3.3 New `TestHermesBridgeToken`: `HERMES_BRIDGE_TOKEN` unset → all 5 endpoints behave as
      today (open); set (monkeypatch settings) → missing header 401, wrong token 401, correct
      `Bearer <token>` → normal success status
- [ ] 3.4 New `TestAuditRecording`: patch `agent_operations_logger.record` (AsyncMock) → assert
      called once per successful mutating endpoint (`POST /tasks`, `/dispatch`, `/status`,
      `/result`) with `agent_name="hermes-bridge"` and the row's `tenant_id`; assert NOT called
      for `GET /tasks/pending`

## 4. Backend: Endpoint-Layer Implementation

- [ ] 4.1 `config.py`: add `HERMES_BRIDGE_TOKEN: Optional[str] = None`
- [ ] 4.2 `sell_machine_endpoints.py`: add `require_hermes_bridge_token` dependency (reads
      `settings.HERMES_BRIDGE_TOKEN` at call time, no-op when unset, `hmac.compare_digest` bearer
      check, 401 on mismatch/missing); attach to exactly the 5 operator-task routes only
- [ ] 4.3 `CreateTaskRequest` gains `tenant_id: Optional[str] = None`; `list_pending_tasks_endpoint`
      gains `tenant_id: Optional[str] = Query(default=None)`; both forwarded to the service
- [ ] 4.4 Convert the 4 mutating endpoints to `async def`; after a successful service call, call
      `agent_operations_logger.record(tenant_id=row["tenant_id"], agent_name="hermes-bridge",
      user_id="machine:hermes", operation_type=<route name>, status="success", duration_ms=<measured>,
      cost=Decimal("0"))` — best-effort, already fails closed internally; do NOT add to the poll
      endpoint
- [ ] 4.5 Run 3.1-3.4 tests green

## 5. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [ ] 5.1 Re-run the full pre-existing `test_operator_task_service.py` and
      `test_operator_task_endpoints.py` suites; confirm no test broken by the signature changes
      beyond the intentional `_fake_decision.tenant_id` fix in Task 1.4
- [ ] 5.2 Grep for any other caller of `create_task`, `list_pending_tasks`, or
      `dispatch_campaign_package` in the backend to confirm none break on the new optional params
      (all existing calls should remain valid — new params are additive/optional)

## 6. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 6.1 Capture pre-test baseline: row count of `operator_tasks`, `agent_operations` (no live DB
      credentials in local `.env` — document the expected credential-gap traceback instead if
      integration tests can't reach Supabase locally)
- [ ] 6.2 Run targeted tests: `pytest tests/test_operator_task_service.py
      tests/test_operator_task_endpoints.py tests/test_operator_tasks_schema.py -v`
      (schema test skipped locally unless `RUN_OPERATOR_TASKS=1` + service-role key present)
- [ ] 6.3 Run the broader backend suite; note baseline pre-existing failures vs. any newly
      introduced ones
- [ ] 6.4 Verify no unintended DB mutations (local run should not touch live Supabase without
      credentials)
- [ ] 6.5 Create report
      `openspec/changes/hermes-task-queue-tenant-scoping/reports/YYYY-MM-DD-step-6-unit-test-and-db-verification.md`

## 7. Backend: Manual Endpoint Testing with curl (MANDATORY — AGENT MUST EXECUTE)

- [ ] 7.1 Start local backend with `SELL_MACHINE_CANONICAL=true`
- [ ] 7.2 `curl GET /api/v1/sell-machine/tasks/pending` (no token, `HERMES_BRIDGE_TOKEN` unset) →
      verify open behavior preserved (expect a Supabase credential-gap traceback locally — document
      it as proof the route + new projection code path was reached, not a failure)
- [ ] 7.3 Set `HERMES_BRIDGE_TOKEN` locally, restart server: verify missing-header → 401 and
      wrong-token → 401 on all 5 routes (these precede any DB call — fully verifiable locally with
      no Supabase credentials)
- [ ] 7.4 `curl POST /tasks` with a `tenant_id` in body, correct bearer token → verify request
      reaches the service layer (expect the same credential-gap traceback past the token check)
- [ ] 7.5 Document all curl commands + responses in the Step 6 report or a dedicated
      `reports/YYYY-MM-DD-step-7-curl-testing.md`

## 8. Documentation Updates (MANDATORY)

- [ ] 8.1 `AGENTES.md:324`: replace the flat "Direct HTTP calls to agents: BYPASS governance" note
      — bypass remains true for agent HTTP generally, but the Hermes operator-task path now has
      optional machine-token auth + audit parity + write-time tenant validation; link this change
- [ ] 8.2 `openspec/specs/bunker-pwa-auth/spec.md:38-40`: amend the "unguarded machine-to-machine
      bridge" note to reference the new optional `HERMES_BRIDGE_TOKEN`
- [ ] 8.3 `ARCHITECTURE.md`: touch only if a settled-decision line about the bridge needs updating
      (likely no change needed — verify)

## 9. Stage 11. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app
- Verified live pre-conditions: `SELL_MACHINE_CANONICAL=true`, `AUTH_ENFORCED=true` in Railway
  `production-175a` — the 5 operator-task routes ARE live and reachable, so live curl verification
  is possible (not just a build/health check)

Tasks:
- [ ] 9.1 `git branch --show-current` verification, commit, push branch, open PR or hand the
      `git push origin main` command to the founder if the commit classifier blocks agent pushes
- [ ] 9.2 Railway `production-175a` build/deploy green (~80s startup window)
- [ ] 9.3 Live verification: `GET /api/v1/sell-machine/tasks/pending` → every row includes
      `tenant_id`; `POST /tasks` with a real tenant UUID → 200 + stamped row, then DELETE it to
      restore state; `POST /tasks` with a random UUID → 404; confirm `HERMES_BRIDGE_TOKEN` is
      still unset in prod (fail-open, unchanged behavior) — token activation is D7's founder
      follow-up, not part of this stage
- [ ] 9.4 Confirm one `agent_operations` row appears with `agent_name='hermes-bridge'` after the
      live `POST /tasks` test in 9.3
- [ ] 9.5 Create report
      `openspec/changes/hermes-task-queue-tenant-scoping/reports/YYYY-MM-DD-deployment.md`

## 10. Review Gate

- [ ] 10.1 `reviewer` agent validates the full change against
      `specs/hermes-manus-execution-bridge/spec.md` (delta), `ARCHITECTURE.md`,
      `DEPLOYMENT_STAGE/CHECKPOINTS.md`: no hardcoded secrets, English-only artifacts, symlink
      integrity untouched, `tenant_context.py` edits are additive-only
- [ ] 10.2 `RUN_TESTS=1 bash init.sh` green before marking the change ready to archive

## 11. Sync Specs and Archive

- [ ] 11.1 Sync this change's specs delta into `openspec/specs/hermes-manus-execution-bridge/spec.md`
- [ ] 11.2 Archive the change to `openspec/changes/archive/YYYY-MM-DD-hermes-task-queue-tenant-scoping/`
- [ ] 11.3 Update `feature_list.json`: flip `hermes-task-queue-tenant-scoping` to `"status": "done"`
