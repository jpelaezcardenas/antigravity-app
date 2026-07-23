# Step 7 Report - Manual Endpoint Testing with curl

- Date: 2026-07-23
- Change: hermes-task-queue-tenant-scoping
- Agent: implementer

## Setup

Local backend started from `apps/backend` with:

```
SELL_MACHINE_CANONICAL=true python -m uvicorn main:app --port 8000
```

(Task 7.2, run #1 — no `HERMES_BRIDGE_TOKEN` set.) Confirmed via `GET /api/v1/health` → `200`
and startup log showing `[STARTUP] ... Total API router routes: 72` before the sell-machine
router mounts (flag applied). Local `apps/backend/.env` has `SUPABASE_URL` but no
`SUPABASE_SERVICE_ROLE_KEY` / anon key configured for this local run, so any route that reaches
`infrastructure/supabase_client.py` raises `supabase.client.SupabaseException: supabase_key is
required` — this is the expected local credential gap referenced by tasks.md 7.2/7.4, and proves
the route + handler code was reached (not a 401/404 short-circuit).

Second run (7.3/7.4) restarted the server on port 8001 with:

```
SELL_MACHINE_CANONICAL=true HERMES_BRIDGE_TOKEN=test-token-123 python -m uvicorn main:app --port 8001
```

Both processes were started/stopped via the Bash tool's `run_in_background` + `taskkill //F //PID
<pid>`, confirmed via `netstat -ano | grep LISTENING` after each kill (port free both times).
`HERMES_BRIDGE_TOKEN` was set only as an inline prefix on the second uvicorn invocation (never
exported into the persistent shell/OS environment), so no restoration step was needed — confirmed
by `echo "$HERMES_BRIDGE_TOKEN"` printing empty in the working shell after the run.

## 7.2 — GET /tasks/pending, no token, HERMES_BRIDGE_TOKEN unset

```
$ curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://localhost:8000/api/v1/sell-machine/tasks/pending
{"detail":"Error interno del servidor"}
HTTP_STATUS:500
```

Server log for this request:

```
2026-07-23 01:01:03,829 - contexia-api - ERROR - [...] EXCEPTION | supabase_key is required | Time: 0.014s
2026-07-23 01:01:03,830 - contexia-api - ERROR - Global error: supabase_key is required
...
File "...\presentation\sell_machine_endpoints.py", line 152, in list_pending_tasks_endpoint
    return list_pending_tasks(tenant_id=tenant_id)
File "...\services\operator_task_service.py", line 95, in list_pending_tasks
    client.table("operator_tasks")
...
supabase.client.SupabaseException: supabase_key is required
```

**Result: PASS.** No 401 — open/fail-open behavior preserved with `HERMES_BRIDGE_TOKEN` unset.
The traceback shows the request reached `operator_task_service.list_pending_tasks` (the new
explicit-column-projection code path, line 95/96: `select("id, tenant_id, task_type, payload,
status, created_at")`) before failing on the Supabase client init, confirming the route +
projection code path were exercised, not skipped.

## 7.3 — All 5 routes, HERMES_BRIDGE_TOKEN=test-token-123 set

### GET /tasks/pending

```
$ curl -s -w "\nHTTP:%{http_code}\n" http://localhost:8001/api/v1/sell-machine/tasks/pending
{"detail":"missing or malformed Authorization header"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -H "Authorization: Bearer wrong-token" http://localhost:8001/api/v1/sell-machine/tasks/pending
{"detail":"invalid bridge token"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -H "Authorization: Bearer test-token-123" http://localhost:8001/api/v1/sell-machine/tasks/pending
{"detail":"Error interno del servidor"}
HTTP:500
```
Log for the correct-token call: `EXCEPTION | supabase_key is required` — past the auth check,
same expected credential gap. **PASS** (401/401/past-auth).

### POST /tasks

```
$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Content-Type: application/json" \
    -d '{"task_type":"test_task","payload":{}}' http://localhost:8001/api/v1/sell-machine/tasks
{"detail":"missing or malformed Authorization header"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer wrong-token" \
    -H "Content-Type: application/json" -d '{"task_type":"test_task","payload":{}}' \
    http://localhost:8001/api/v1/sell-machine/tasks
{"detail":"invalid bridge token"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer test-token-123" \
    -H "Content-Type: application/json" \
    -d '{"task_type":"test_task","payload":{},"tenant_id":"11111111-1111-1111-1111-111111111111"}' \
    http://localhost:8001/api/v1/sell-machine/tasks
{"detail":"unknown task_type 'test_task'"}
HTTP:400
```

The correct-token call with an invalid `task_type` ("test_task" is not in
`READ_ONLY_TASK_TYPES = {"research", "metrics_pull", "external_integration", "generate_doc"}`)
returned `400` from the pre-existing task-type validation in
`operator_task_service.create_task`, not a 401 — confirming the auth gate was passed and the
service layer's validation logic executed. Retested with a valid `task_type` to reach the DB
layer (see Task 7.4 below). **PASS** (401/401/past-auth).

### POST /campaigns/{decision_id}/dispatch

```
$ curl -s -w "\nHTTP:%{http_code}\n" -X POST http://localhost:8001/api/v1/sell-machine/campaigns/fake-decision-id/dispatch
{"detail":"missing or malformed Authorization header"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer wrong-token" \
    http://localhost:8001/api/v1/sell-machine/campaigns/fake-decision-id/dispatch
{"detail":"invalid bridge token"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer test-token-123" \
    http://localhost:8001/api/v1/sell-machine/campaigns/fake-decision-id/dispatch
{"detail":"Error interno del servidor"}
HTTP:500
```
Log: `EXCEPTION | supabase_key is required` — past the auth check (decision lookup hits Supabase
before the fake decision id can even be evaluated). **PASS** (401/401/past-auth).

### POST /tasks/{task_id}/status

```
$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Content-Type: application/json" \
    -d '{"status":"dispatched"}' http://localhost:8001/api/v1/sell-machine/tasks/fake-task-id/status
{"detail":"missing or malformed Authorization header"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer wrong-token" \
    -H "Content-Type: application/json" -d '{"status":"dispatched"}' \
    http://localhost:8001/api/v1/sell-machine/tasks/fake-task-id/status
{"detail":"invalid bridge token"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer test-token-123" \
    -H "Content-Type: application/json" -d '{"status":"dispatched"}' \
    http://localhost:8001/api/v1/sell-machine/tasks/fake-task-id/status
{"detail":"supabase_key is required"}
HTTP:400
```
Log: `services.operator_task_service - ERROR - operator_task_service.mark_dispatched error:
supabase_key is required` — past the auth check, reached `mark_dispatched`. **PASS**
(401/401/past-auth).

### POST /tasks/{task_id}/result

```
$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Content-Type: application/json" \
    -d '{"status":"completed","result":{}}' http://localhost:8001/api/v1/sell-machine/tasks/fake-task-id/result
{"detail":"missing or malformed Authorization header"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer wrong-token" \
    -H "Content-Type: application/json" -d '{"status":"completed","result":{}}' \
    http://localhost:8001/api/v1/sell-machine/tasks/fake-task-id/result
{"detail":"invalid bridge token"}
HTTP:401

$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer test-token-123" \
    -H "Content-Type: application/json" -d '{"status":"completed","result":{}}' \
    http://localhost:8001/api/v1/sell-machine/tasks/fake-task-id/result
{"detail":"supabase_key is required"}
HTTP:400
```
Log: `services.operator_task_service - ERROR - operator_task_service.report_result error:
supabase_key is required` — past the auth check, reached `report_result`. **PASS**
(401/401/past-auth).

## 7.4 — POST /tasks with tenant_id, correct bearer token, valid task_type

```
$ curl -s -w "\nHTTP:%{http_code}\n" -X POST -H "Authorization: Bearer test-token-123" \
    -H "Content-Type: application/json" \
    -d '{"task_type":"research","payload":{},"tenant_id":"11111111-1111-1111-1111-111111111111"}' \
    http://localhost:8001/api/v1/sell-machine/tasks
{"detail":"supabase_key is required"}
HTTP:400
```

Log: `services.operator_task_service - ERROR - operator_task_service.create_task error:
supabase_key is required`. **PASS** — this proves the request passed (a) the
`require_hermes_bridge_token` auth dependency, (b) the `CreateTaskRequest` pydantic body
validation (including the new `tenant_id` field), and (c) the `task_type` allow-list check in
`create_task`, before failing on the same local Supabase credential gap as every other DB-backed
call in this environment.

## Summary Table

| Route | No token | Wrong token | Correct token |
|---|---|---|---|
| GET /tasks/pending | 401 missing/malformed header | 401 invalid bridge token | 500 credential-gap (past auth) |
| POST /tasks (bad task_type) | 401 | 401 | 400 unknown task_type (past auth) |
| POST /tasks (valid task_type + tenant_id) | n/a | n/a | 400 credential-gap (past auth + validation) |
| POST /campaigns/{id}/dispatch | 401 | 401 | 500 credential-gap (past auth) |
| POST /tasks/{id}/status | 401 | 401 | 400 credential-gap (past auth) |
| POST /tasks/{id}/result | 401 | 401 | 400 credential-gap (past auth) |

All 5 routes: consistent 401 behavior for missing/wrong token, and consistent past-auth behavior
(reaching service-layer code, blocked only by the local Supabase credential gap) for the correct
token. No route returned a 401 with the correct token, and no route returned anything other than
401 for a missing/wrong token. `HERMES_BRIDGE_TOKEN` unset (7.2, port 8000) preserved fully open
behavior with no auth-related short-circuit at all.

## Cleanup

- Both uvicorn processes (`pid 32064` on :8000, `pid 20124` on :8001) killed via
  `taskkill //F //PID <pid>`; `netstat -ano | grep LISTENING` confirmed both ports free
  afterward.
- `HERMES_BRIDGE_TOKEN` was never exported to the persistent shell/OS environment (only passed
  inline to the second `uvicorn` invocation), so no explicit unset/restore step was required;
  confirmed empty via `echo "$HERMES_BRIDGE_TOKEN"` in the working shell post-test.

## Outcome

Step 7 status: **PASS**. All sub-tasks (7.1-7.5) verified against a live local server, using
real curl output (no fabricated responses). The local environment's missing
`SUPABASE_SERVICE_ROLE_KEY` produced the expected credential-gap errors documented above in place
of live DB results — consistent with the Step 6 report's finding that local `.env` has no
service-role key.
