# Implementer report — Tasks 7 & 8, hermes-task-queue-tenant-scoping

- Date: 2026-07-23
- Branch: `feature/hermes-task-queue-tenant-scoping` (verified via `git branch --show-current`
  before and after edits)
- Scope: Task 7 (manual curl testing) + Task 8 (documentation updates) only. Tasks 0-6
  untouched (already `[x]`); Tasks 9-11 untouched (deploy/review/archive, separate step).

## Task 7 — Manual endpoint testing with curl

Full transcript + analysis in
`openspec/changes/hermes-task-queue-tenant-scoping/reports/2026-07-23-step-7-curl-testing.md`.

Summary:
- Started local backend twice from `apps/backend`:
  `SELL_MACHINE_CANONICAL=true python -m uvicorn main:app --port 8000` (no token), then
  `SELL_MACHINE_CANONICAL=true HERMES_BRIDGE_TOKEN=test-token-123 python -m uvicorn main:app --port 8001`
  (token set). `HERMES_BRIDGE_TOKEN` was only ever passed inline to the second invocation, never
  exported to the persistent shell — nothing needed restoring afterward (confirmed empty via
  `echo "$HERMES_BRIDGE_TOKEN"`).
- 7.2: `GET /tasks/pending` with no token, `HERMES_BRIDGE_TOKEN` unset → `500`, log traceback
  shows the request reached `operator_task_service.list_pending_tasks` (new explicit projection,
  line 95-96) before failing on `supabase.client.SupabaseException: supabase_key is required` —
  proves open/fail-open behavior preserved, route + projection code path reached.
- 7.3: all 5 routes (`GET /tasks/pending`, `POST /tasks`, `POST /campaigns/{id}/dispatch`,
  `POST /tasks/{id}/status`, `POST /tasks/{id}/result`) tested with `HERMES_BRIDGE_TOKEN` set:
  - No header → `401 {"detail":"missing or malformed Authorization header"}` on all 5.
  - Wrong token → `401 {"detail":"invalid bridge token"}` on all 5.
  - Correct token → no route returned 401; each proceeded to service-layer logic (task-type
    validation, or the local Supabase credential gap).
- 7.4: `POST /tasks` with `tenant_id` + valid `task_type="research"` + correct token → `400
  {"detail":"supabase_key is required"}`, log confirms it reached
  `operator_task_service.create_task`, i.e. past auth, past pydantic body validation (including
  the new `tenant_id` field), past the `task_type` allow-list check.
- Both uvicorn processes killed via `taskkill //F //PID <pid>`; `netstat -ano | grep LISTENING`
  confirmed both ports free afterward.

All 5 sub-tasks (7.1-7.5) checked off `[x]` in tasks.md.

## Task 8 — Documentation updates

1. **`AGENTES.md`** (around line 324): kept the existing "Direct HTTP calls to agents: BYPASS
   governance" line as the general rule, and appended a scoped exception paragraph describing the
   Hermes operator-task bridge's new `HERMES_BRIDGE_TOKEN` gate (fail-open until set, linking
   design.md D5/D7), audit-parity logging (`agent_name="hermes-bridge"`), and write-time tenant
   validation — clarifies all other direct-HTTP agent routes remain fully ungoverned.
2. **`openspec/specs/bunker-pwa-auth/spec.md`**:
   - Appended an amendment note to the "Backend routers enforce authentication" requirement body
     (after the `/tasks/*` unguarded-bridge sentence) referencing the new optional
     `HERMES_BRIDGE_TOKEN` gate on `/tasks/*` and `/campaigns/{id}/dispatch` specifically, and
     confirming `/creative-loop/run` / `/telemetry/report` are unaffected/out of scope.
   - Amended the existing "Scenario: The Hermes bridge is unaffected" to specify it holds when
     `HERMES_BRIDGE_TOKEN` is unset (the default), and added a companion
     "Scenario: The Hermes bridge token gate, once configured, is independent of AUTH_ENFORCED"
     covering the 401 behavior across all 5 routes.
3. **`ARCHITECTURE.md`**: read the Contenedores table and Decisiones list (`grep` for
   Hermes/bridge/sell-machine/operator-task) — no settled-decision line describes the
   operator-task/Hermes bridge's auth status at this level of granularity (Decision #1 is about
   Hermes running local/on-prem, unrelated to route-level auth). **No edit made** —
   explicitly verified nothing needed changing, per the task's own instruction.

All 3 sub-tasks (8.1-8.3) checked off `[x]` in tasks.md.

## Files touched

- `openspec/changes/hermes-task-queue-tenant-scoping/reports/2026-07-23-step-7-curl-testing.md` (new)
- `openspec/changes/hermes-task-queue-tenant-scoping/tasks.md` (7.1-7.5, 8.1-8.3 checked off)
- `AGENTES.md` (line ~324, exception paragraph added)
- `openspec/specs/bunker-pwa-auth/spec.md` (requirement body amendment + 1 new scenario)
- `progress/impl_hermes-task-queue-tenant-scoping-7-8.md` (this file)

## Next step

Awaiting reviewer verdict before this task is considered fully done (per HARNESS.md protocol —
implementer does not self-approve). Tasks 9-11 (deploy/review-gate/archive) are out of scope for
this session.
