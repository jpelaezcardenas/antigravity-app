# Implementer report — hermes-task-queue-tenant-scoping, Tasks 1-6

- Date: 2026-07-23
- Branch: `feature/hermes-task-queue-tenant-scoping`
- Scope: Tasks 1-6 only (service-layer TDD, endpoint-layer TDD, existing-test review, unit
  test + DB-state verification report). Tasks 0 and 7-11 intentionally untouched.

## What changed

### `apps/backend/core/tenant_context.py` (additive only)
- Added `tenant_exists(client, tenant_id) -> bool`, using `.maybe_single()` (matching the idiom
  already used in `crm_service.py` for 0-row-safe single lookups) so a missing tenant returns
  `False` instead of raising `PGRST116`.
- `resolve_cliente_cero_tenant_id` — untouched, per the ownership boundary with
  `hermes-multi-tenant-wrapper`.

### `apps/backend/services/operator_task_service.py`
- `create_task(task_type, payload, tenant_id=None)`: side-effecting/unknown-type rejection
  unchanged and still first. When `tenant_id` is supplied, validates via `tenant_exists` and
  rejects with `"tenant {id} not found"` (no insert) on failure, otherwise stamps it directly
  (Cliente Cero resolver never called). When omitted, falls back to
  `_resolve_cliente_cero_tenant_id` + `logger.warning(...)`; if the resolver also returns `None`,
  rejects with an explicit error and no insert.
- `list_pending_tasks(tenant_id=None)`: replaced `select("*")` with the explicit projection
  `"id, tenant_id, task_type, payload, status, created_at"`; adds `.eq("tenant_id", tenant_id)`
  only when a value is passed.
- `dispatch_campaign_package`: derives `tenant_id` from `getattr(decision, "tenant_id", None)`;
  falls back to the Cliente Cero resolver + `logger.warning(...)` only when that's falsy.

### `apps/backend/config.py`
- Added `HERMES_BRIDGE_TOKEN: Optional[str] = None` (imported `Optional` from `typing`, not
  previously imported in this file).

### `apps/backend/presentation/sell_machine_endpoints.py`
- New `require_hermes_bridge_token` dependency: reads `settings.HERMES_BRIDGE_TOKEN` at call
  time (not import time), no-op when unset, `hmac.compare_digest` constant-time bearer check,
  401 on missing/malformed header or mismatch.
- Attached `dependencies=[Depends(require_hermes_bridge_token)]` to exactly the 5 operator-task
  routes (`GET /tasks/pending`, `POST /tasks`, `POST /campaigns/{id}/dispatch`,
  `POST /tasks/{id}/status`, `POST /tasks/{id}/result`) — no other route in the file touched.
- `CreateTaskRequest` gains `tenant_id: Optional[str] = None`; `list_pending_tasks_endpoint`
  gains `tenant_id: Optional[str] = Query(default=None)`; both forwarded to the service.
- `create_task_endpoint`, `task_status_endpoint`, `task_result_endpoint` converted to `async def`
  (`dispatch_campaign_endpoint` was already async). All 4 mutating endpoints now call
  `await agent_operations_logger.record(...)` after a successful service call, with
  `agent_name="hermes-bridge"`, `user_id="machine:hermes"`, a route-specific `operation_type`
  (`create_task` / `dispatch_campaign` / `mark_dispatched` / `report_result`), and a
  `duration_ms` measured with `time.monotonic()`. The poll endpoint (`GET /tasks/pending`) does
  not record.

### Tests
- New `apps/backend/tests/test_tenant_context.py` (2 tests: `tenant_exists` true/false cases).
- Extended `apps/backend/tests/test_operator_task_service.py`: 4 new `TestCreateTask` cases, 3
  new `TestListPendingTasks` cases, 2 new `TestDispatchCampaignPackage` cases. `_fake_decision()`
  now takes an explicit `tenant_id=None` parameter (documented in its docstring) so every
  existing call site avoids the MagicMock-truthiness trap without having to touch every call
  site individually — functionally equivalent to setting it explicitly at each site, and every
  pre-existing dispatch test still exercises the Cliente-Cero-fallback path as before.
- Extended `apps/backend/tests/test_operator_task_endpoints.py`: added an autouse fixture that
  patches `agent_operations_logger.record` globally in this module (all 4 mutating endpoints now
  call it); added `tenant_id`-forwarding tests for `POST /tasks` and `GET /tasks/pending`; added
  `TestHermesBridgeToken` (4 tests covering unset/missing/wrong/correct across all 5 routes,
  looping over route definitions with a fresh `httpx.AsyncClient` per request since the shared
  fixture's client can only be opened once); added `TestAuditRecording` (5 tests: one per
  mutating endpoint asserting `record()` was called once with the right `agent_name`/`tenant_id`,
  plus one asserting the poll endpoint never calls it). Pre-existing `fake_row` fixtures in
  `TestCreateTaskEndpoint`, `TestDispatchCampaignEndpoint`, `TestTaskStatusEndpoint`, and
  `TestTaskResultEndpoint` were updated to include `tenant_id` — needed because the new audit
  call reads `row["tenant_id"]`, and production rows always carry that column.

## Test results

- `pytest tests/test_tenant_context.py tests/test_operator_task_service.py
  tests/test_operator_task_endpoints.py -v` → **47 passed, 0 failed**.
- `pytest tests/test_operator_tasks_schema.py -v` → **4 skipped** (env-gated,
  `RUN_OPERATOR_TASKS=1` + service-role key not present locally — expected, per design).
- Full backend suite (`pytest -q`, excluding 3 pre-existing collection errors unrelated to this
  change — see report below) → **628 passed, 40 failed, 109 skipped**. All 40 failures are in
  modules this change never touched (Shadow GL CSV parsing, approval-rules acceptance checks,
  wizard endpoint, centinela alerts endpoint, secure-LLM anonymization, cloud-only model
  selector) — pre-existing, not introduced by Tasks 1-5.
- Full detail: `openspec/changes/hermes-task-queue-tenant-scoping/reports/2026-07-23-step-6-unit-test-and-db-verification.md`.

## Deviations from the brief (with rationale)

- The brief's exact `logger.warning` format string for `create_task` was followed verbatim; the
  `dispatch_campaign_package` warning format was also followed verbatim.
- For `TestHermesBridgeToken`, rather than reusing the shared `sm_client` fixture across a loop
  over 5 routes (which fails — `httpx.AsyncClient` can only be opened once per instance), a
  `_fresh_client()` helper builds a new isolated app/client per request. Functionally identical
  coverage to what the brief asked for, just structured to avoid a real (not merely
  spec'd-around) httpx limitation.
- `_fake_decision()` gained an explicit `tenant_id=None` **parameter** with a documented default,
  rather than mechanically inserting `decision.tenant_id = None` at every one of the ~7 existing
  call sites. This satisfies the brief's intent (no call site is left exposed to the MagicMock
  truthiness trap) with less duplication; every pre-existing test's behavior is unchanged and
  verified green.
- Pre-existing `fake_row` fixtures in the endpoint test file needed a `tenant_id` key added
  (not explicitly called out in the brief, but required once the audit-recording feature reads
  `row["tenant_id"]`) — this is exactly the kind of "test broken by the signature/behavior
  change" Task 5.1 asks to review and fix.

## Files touched

- `apps/backend/core/tenant_context.py`
- `apps/backend/services/operator_task_service.py`
- `apps/backend/config.py`
- `apps/backend/presentation/sell_machine_endpoints.py`
- `apps/backend/tests/test_tenant_context.py` (new)
- `apps/backend/tests/test_operator_task_service.py`
- `apps/backend/tests/test_operator_task_endpoints.py`
- `openspec/changes/hermes-task-queue-tenant-scoping/tasks.md` (checked off Tasks 1-6)
- `openspec/changes/hermes-task-queue-tenant-scoping/reports/2026-07-23-step-6-unit-test-and-db-verification.md` (new)

## Commits

1. `feat(hermes-task-queue-tenant-scoping): tenant-scope operator-task service layer` — Tasks 1-2
2. `feat(hermes-task-queue-tenant-scoping): tenant-scope + audit + optional auth for operator-task bridge` — Tasks 3-5
3. (this commit, pending) — Task 6 report + tasks.md checkboxes + this progress report
