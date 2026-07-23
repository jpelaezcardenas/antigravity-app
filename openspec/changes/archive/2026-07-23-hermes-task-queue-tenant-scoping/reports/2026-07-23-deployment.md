# Deployment Report — hermes-task-queue-tenant-scoping

- Date: 2026-07-23
- Change: hermes-task-queue-tenant-scoping
- Deploy branch: main
- Merge commit: `f944918..7b26638` (`main -> main`)
- Railway project: `elegant-success` (`27f4a1b4-1e46-4ad7-b08e-15e92817ffdd`), environment `production`
- Railway deployment: `2c33acc2-28de-4815-8370-0ee2e53b175c`, status **SUCCESS**, created 2026-07-23T06:38:01Z
- Backend URL: `https://antigravity-app-production-175a.up.railway.app`

## Pre-conditions confirmed live

- `SELL_MACHINE_CANONICAL=true` — the 5 operator-task routes are live and reachable.
- `AUTH_ENFORCED=true`.
- `HERMES_BRIDGE_TOKEN` **absent** from Railway variables — fail-open default preserved exactly as
  designed (design.md D5/D7). Activating it is the founder's follow-up task, not part of this
  deploy.

## Live verification (curl against production)

### 1. `GET /api/v1/sell-machine/tasks/pending` — tenant_id present in every row

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" https://antigravity-app-production-175a.up.railway.app/api/v1/sell-machine/tasks/pending
```
```
[{"id":"661d395f-...","tenant_id":"e2d30d09-6b96-4ebe-a79a-c6aff7a5df34","task_type":"post_content", ...}]
HTTP_STATUS:200
```
Confirmed: the pre-existing pending row (from `sell-machine-creative-swarm`'s Stage 11 smoke-test,
2026-07-19) now carries `tenant_id` in the response via the new explicit column projection.

### 2. `POST /tasks` with a real tenant UUID — 200 + stamped

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/sell-machine/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type":"research","payload":{"note":"Stage 11 live verification - hermes-task-queue-tenant-scoping - safe to delete"},"tenant_id":"e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"}'
```
```
{"id":"c8bae5d5-106d-4cc7-865b-087bd838eee6","tenant_id":"e2d30d09-6b96-4ebe-a79a-c6aff7a5df34","task_type":"research","status":"pending", ...}
HTTP_STATUS:200
```
Tenant correctly stamped from the request body (not silently defaulted to Cliente Cero via the
fallback path — the explicit-tenant branch was exercised).

### 3. `POST /tasks` with a nonexistent tenant UUID — 404

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/sell-machine/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type":"research","payload":{},"tenant_id":"00000000-0000-0000-0000-000000000000"}'
```
```
{"detail":"tenant 00000000-0000-0000-0000-000000000000 not found"}
HTTP_STATUS:404
```
Confirms `tenant_exists()` validation is live and rejects unknown tenants before any insert.

### 4. Audit parity — `agent_operations` row recorded

Queried via Supabase MCP immediately after test #2:
```sql
select id, tenant_id, agent_name, user_id, operation_type, status, created_at
from agent_operations where agent_name = 'hermes-bridge' order by created_at desc limit 5;
```
```
[{"id":"2107bdac-4b32-4c04-b7ab-c39258610e45","tenant_id":"e2d30d09-6b96-4ebe-a79a-c6aff7a5df34",
  "agent_name":"hermes-bridge","user_id":"machine:hermes","operation_type":"create_task",
  "status":"success","created_at":"2026-07-23 06:56:51.781889+00"}]
```
Confirmed: the `create_task` mutation recorded one `agent_operations` row with `agent_name="hermes-bridge"`,
`user_id="machine:hermes"`, matching the test's tenant.

## Database state restored

Test artifacts from #2 and #4 above were deleted via Supabase MCP after verification:
- `operator_tasks` row `c8bae5d5-106d-4cc7-865b-087bd838eee6` — deleted.
- `agent_operations` row `2107bdac-4b32-4c04-b7ab-c39258610e45` — deleted.

Verified 0 remaining rows for both ids post-delete. The original pending `operator_tasks` row from
the 2026-07-19 smoke-test was left untouched (not created by this session, not ours to delete).

## Outcome

- Deploy: **SUCCESS**
- Live behavior matches the specs delta exactly: tenant_id contractually present in poll payload,
  explicit-tenant stamping, unknown-tenant 404, Cliente-Cero-fallback path (exercised in local/unit
  tests, not re-triggered live to avoid an unnecessary Cliente Cero write), audit parity confirmed.
- `HERMES_BRIDGE_TOKEN` fail-open confirmed unchanged — no regression to the live, currently
  header-less Hermes poller.
- **Founder follow-up (design.md D7, out of this change's own scope):** activate
  `HERMES_BRIDGE_TOKEN` — update the Hermes-side poller (separate `hermes-workspace` repo) and its
  local `.env` with the `Authorization: Bearer` header **first**, then set `HERMES_BRIDGE_TOKEN` in
  Railway `production-175a`. Reversing this order would 401 the live poller until its side is
  updated.
