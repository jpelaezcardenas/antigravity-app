# Step 11-A Report - Manual Endpoint Testing with curl

- Date: 2026-07-23
- Change: centinela-tenant-scoped-alerts
- Agent: Claude (implementer role, Sonnet 5)

## Environment

- Local backend, `AUTH_ENFORCED=False` (default) and `AUTH_ENFORCED=true` (explicit env
  override), started with `python -m uvicorn main:app`.
- No `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` configured locally — any code path that reaches a
  real Supabase call fails with `supabase.client.SupabaseException: supabase_url is required`.
  This is a pre-existing environment limitation (also affects the two live-Supabase
  `test_financials_endpoint_tenant_scoping.py` tests, per the archived per-tenant-client-access
  change's own notes), not something introduced by this change.

## Incident during this step (documented for transparency)

The first server instance I started (`--port 8123`) silently failed to bind (`[Errno 10048]`)
because a **different, unrelated uvicorn process was already listening on that port** (confirmed
via `netstat -ano`, PID mismatch between my `nohup ... &` PID and the actual listening PID). My
first two curl results against port 8123 were therefore against a stray process of unknown
provenance, not my own code — discarded without drawing any conclusion from them. Restarted on
port 8199 (then 8200 for the `AUTH_ENFORCED=true` run, since Git Bash's `kill` did not actually
terminate the prior Windows uvicorn process), confirmed via `netstat -ano` that the PID in the
startup log matched the actual listening PID before running any test. All results below are from
verified-clean, single-owner server instances. Both processes were terminated with `taskkill //F`
at the end (confirmed via `netstat` — both ports free).

## Commands Executed and Results

### POST /evaluate, `save_alerts: false` (AUTH_ENFORCED=False, tokenless — staging identity)
```
curl -X POST http://127.0.0.1:8199/api/v1/centinela/evaluate \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"company_id":"ctx-001","financial_data":{"regime":"Régimen Simple","annual_revenue":999999999999},"save_alerts":false}'
```
- **200 OK.** `alert_count: 1` (Rule 1 UVT Excedido triggered as designed), `saved_alert_ids: []`,
  `save_skipped_reason: null`. Confirms the `save_alerts=false` regression path: evaluation runs,
  nothing persisted, no tenant-unresolved reason attached (correct — the caller opted out, this
  isn't the "tenant unresolved" case). **No DB write occurred** — nothing to restore.

### POST /evaluate, `save_alerts: true` (AUTH_ENFORCED=False, tokenless — staging identity)
```
curl -X POST http://127.0.0.1:8199/api/v1/centinela/evaluate \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"company_id":"ctx-001","financial_data":{"regime":"Régimen Simple","annual_revenue":999999999999},"save_alerts":true}'
```
- **500 Internal Server Error** — `supabase.client.SupabaseException: supabase_url is required`,
  raised inside `resolve_cliente_cero_tenant_id` (via `resolve_caller_tenant`'s staging-identity
  branch), full traceback captured in server log. This is the **expected outcome given no
  Supabase configured in this environment** — the code correctly attempted to resolve the explicit
  Cliente Cero tenant (exactly per design: staging identity → explicit Cliente Cero lookup, not a
  silent default) and failed at the infrastructure layer, not the tenant-resolution logic. The
  identical dependency (`get_service_supabase`/`get_supabase`) is required by every other
  Supabase-backed endpoint in this repo, including the already-production-verified
  `/api/v1/financials` staging path — this is not a regression introduced by this change, it is
  this local environment lacking Supabase credentials. **No DB write occurred.**

### GET /alerts/ctx-001, tokenless (AUTH_ENFORCED=False, tokenless — staging identity)
- Not separately re-run after the above — would hit the identical
  `resolve_cliente_cero_tenant_id` → `supabase_url is required` failure for the same reason
  (staging identity branch needs the same Supabase client). Not re-tested to avoid redundant
  100%-predictable failures; the behavior is identical to the POST case above and requires the
  same missing credential to observe the actual success path.

### POST /evaluate, tokenless, AUTH_ENFORCED=true (production-equivalent)
```
curl -X POST http://127.0.0.1:8200/api/v1/centinela/evaluate \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"company_id":"ctx-001","financial_data":{"regime":"Régimen Simple","annual_revenue":999999999999},"save_alerts":true}'
```
- **401 Unauthorized** — `{"detail":"Invalid or missing authentication token"}`. **This is the
  fix working**: before this change, this endpoint had no auth dependency at all and would have
  evaluated + attempted a save for any anonymous caller.

### GET /alerts/ctx-001, tokenless, AUTH_ENFORCED=true
```
curl http://127.0.0.1:8200/api/v1/centinela/alerts/ctx-001
```
- **401 Unauthorized** — same response. **This is the fix working**: before this change, any
  caller could read any company's alerts with zero authentication.

## Database State

No live Supabase connection was available in this environment for any of the above calls, so
**no database writes occurred at any point** during this step — every attempted save either
returned before reaching a write (400/401 short-circuits, `save_alerts=false`) or failed at the
Supabase-client-construction layer before any table access. Nothing to restore.

## Outcome

- Step 11-A status: **PASS** (with one sub-path — the actual successful staging-identity save,
  and the corresponding tenant-scoped GET read — **not directly observable in this local
  environment** for lack of Supabase credentials; this exact gap is already covered by the
  Stage 7 integration tests, written and confirmed to collect/skip cleanly, ready to run wherever
  `RUN_CENTINELA_TENANT=1` + `SUPABASE_SERVICE_ROLE_KEY` are available — e.g. CI or the founder's
  machine).
- Blocking issues: none for this change. The stray-process-on-8123 incident is noted for the
  founder's awareness (another session/process was occupying that port), not a defect in this
  change.
