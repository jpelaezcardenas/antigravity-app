# Step 8 — Manual Endpoint Testing with curl

Date: 2026-07-23
Branch: `feature/taty-per-tenant-profiles`
Server under test: `apps/backend/main.py` via `python -m uvicorn main:app --host 127.0.0.1 --port 8000`
(Windows local worktree, Python 3.11.9, no `SUPABASE_URL`/`SUPABASE_KEY` set — confirmed by
task 7's report and independently reconfirmed here.)

## 8.1 Start local backend server

Command:

```
cd apps/backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Server booted cleanly with **no crash**, despite missing Supabase credentials — this confirms
task 7/8's expectation that the app boots in a degraded-but-alive mode rather than refusing to
start. Full boot log:

```
⚠️  JWT_SECRET not set — using auto-generated secret for development. This will change on every restart. Set JWT_SECRET in .env for persistence.
2026-07-23 01:50:51,891 - contexia-api - INFO - CORS middleware applied
2026-07-23 01:50:51,891 - contexia-api - INFO - Rate limiter applied (30 requests/minute per IP)
2026-07-23 01:50:51,891 - contexia-api - INFO - Request logging middleware applied
2026-07-23 01:50:51,891 - contexia-api - INFO - Global exception handler applied
[INFO] CORS enabled for origins: ['http://localhost:3001', 'http://localhost:3002', 'http://localhost:5173', 'http://localhost:3000']
[STARTUP] Loading routers...
[STARTUP] Health router loaded
[STARTUP] Metrics router loaded - /api/v1/monitoring/metrics
2026-07-23 01:50:51,938 - contexia-api - INFO - Secrets router registered successfully
[STARTUP] Attempting WebSocket router...
[STARTUP] WebSocket router SUCCESS
2026-07-23 01:50:52,006 - contexia-api - INFO - WebSocket router registered successfully
2026-07-23 01:50:52,042 - contexia-api - INFO - Agent router imported. Routes count: 8
2026-07-23 01:50:52,048 - contexia-api - INFO - Agent endpoints router registered successfully. Total API router routes: 60
2026-07-23 01:50:52,055 - contexia-api - INFO - Approval queue router registered successfully
INFO:     Started server process [15344]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Readiness confirmed via:

```
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/v1/health
→ 200
```

## 8.2 `GET /api/v1/agents/ask` unauthenticated (staging path)

Confirmed first (per task instructions) that `AUTH_ENFORCED` defaults to `False` locally:
`apps/backend/config.py:31` — `AUTH_ENFORCED: bool = False`. So an unauthenticated request hits
`core.deps.get_current_user`'s permissive staging identity (`_STAGING_USER`), which
`taty_endpoints.ask_taty` then routes to `_resolve_cliente_cero_tenant_id()`.

Command:

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" \
  "http://127.0.0.1:8000/api/v1/agents/ask?question=%C2%BFCu%C3%A1l%20es%20el%20UVT%202026%3F&channel=dashboard"
```

Actual response:

```
{"detail":"Error calling Taty service"}
HTTP_STATUS:500
```

Server-side traceback (from uvicorn log):

```
2026-07-23 01:51:09,160 - presentation.taty_endpoints - ERROR - Error in ask_taty: supabase_url is required
Traceback (most recent call last):
  File ".../presentation/taty_endpoints.py", line 178, in ask_taty
    tenant_id = await _resolve_cliente_cero_tenant_id()
  File ".../presentation/taty_endpoints.py", line 30, in _resolve_cliente_cero_tenant_id
    supabase.table("tenants")
  File ".../infrastructure/supabase_client.py", line 15, in _ensure_initialized
    self._client = create_client(settings.SUPABASE_URL, key)
  File ".../supabase/client.py", line 47, in __init__
    raise SupabaseException("supabase_url is required")
supabase.client.SupabaseException: supabase_url is required
```

**Finding (not a code bug introduced by this change, but a real and useful signal):** the
"never raises, always returns a response dict" contract (`_error_response`) belongs to
`TatyAgentService.ask()` / `_get_tenant_profile()`, per design D1/D3 — it is NOT extended to
`taty_endpoints._resolve_cliente_cero_tenant_id()`, which is the resolution step that runs
*before* `ask()` is ever called for the staging/Cliente-Cero path. With no live Supabase, that
resolution step raises a raw `SupabaseException`, which the outer `try/except Exception` in
`ask_taty()` catches and converts into a generic `HTTP 500 "Error calling Taty service"` — not
a graceful in-band `TatyAskResponse`.

This is the same pre-existing environment limitation task 7 already documented (no Supabase
credentials in this worktree) — it is not something this change's diff regressed, since
`_resolve_cliente_cero_tenant_id()` is a straight port of the same pattern already used by
`financials_endpoints.py` (per design D3). **8.2 could not be verified as "200, Cliente
Cero-scoped answer" in this environment** because that requires a live `tenants` table lookup.
The scenario IS confirmed to route through the intended code path (staging identity →
`_resolve_cliente_cero_tenant_id()`, never straight to `ask()` with a hardcoded profile) — the
only thing blocked by the environment is the final Supabase round-trip. Deferred to Stage 11
(11.8, Cliente Cero's Telegram chat verification against production) for full end-to-end
confirmation with live Supabase.

## 8.3-8.5 Provisioned client JWT / spoofed company_id / unresolved-tenant JWT scenarios

**Not executable in this local environment — documented, not fabricated.**

These three scenarios require a real Supabase-issued, asymmetrically-signed (ES256/JWKS per
`ARCHITECTURE.md` decision #13) JWT for:
- 8.3: a provisioned B2B client with an active `user_tenants` membership,
- 8.4: the same, plus a `company_id` in the request body belonging to a *different* tenant,
- 8.5: an authenticated user with zero `user_tenants` membership rows.

None of these can be minted locally: this worktree has no `SUPABASE_URL`/`SUPABASE_KEY`
(confirmed above and by task 7), so there is no live Supabase project to (a) query
`user_tenants`/`tenants` against, or (b) sign a real session JWT from. A locally-fabricated JWT
would not exercise `core/deps.py::_verify_supabase_token`'s real ES256/JWKS verification path
(ARCHITECTURE.md decision #13) and would produce a false-positive result — exactly the kind of
fabricated test output this task's instructions explicitly forbid.

**Deferred to Stage 11** (tasks.md items 11.6 and 11.7), where the founder supplies real
Bitwarden credentials for a provisioned production client and the endpoint is called against
Railway with `AUTH_ENFORCED=true`. This mirrors task 7's identical treatment of the same
environment constraint.

## 8.6 `POST /api/v1/agents/taty/ask` → expect 404 (route deleted, task 5)

Command:

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://127.0.0.1:8000/api/v1/agents/taty/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"test question here","company_id":"ctx-001"}'
```

Actual response:

```
{"detail":"Not Found"}
HTTP_STATUS:404
```

**PASS** — confirms task 5's route deletion; no auth/DB dependency, fully verified locally.

## 8.7 `POST /api/v1/agents/ask` with malformed body → expect 422

Two variants tested.

**a) `question` under min_length (5):**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://127.0.0.1:8000/api/v1/agents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"hi"}'
```

Actual response:

```
{"detail":[{"type":"string_too_short","loc":["body","question"],"msg":"String should have at least 5 characters","input":"hi","ctx":{"min_length":5},"url":"https://errors.pydantic.dev/2.13/v/string_too_short"}]}
HTTP_STATUS:422
```

**b) `question` missing entirely:**

```
curl -s -w "\nHTTP_STATUS:%{http_code}\n" -X POST "http://127.0.0.1:8000/api/v1/agents/ask" \
  -H "Content-Type: application/json" \
  -d '{"channel":"dashboard"}'
```

Actual response:

```
{"detail":[{"type":"missing","loc":["body","question"],"msg":"Field required","input":{"channel":"dashboard"},"url":"https://errors.pydantic.dev/2.13/v/missing"}]}
HTTP_STATUS:422
```

**PASS** — both variants return 422 as expected, no auth/DB dependency, fully verified locally.

(A third variant with an accented Spanish `question` string sent via curl's `-d` on this
Windows/git-bash shell returned `400 {"detail":"There was an error parsing the body"}` — a
local curl/shell UTF-8 encoding artifact unrelated to this change's validation logic, not a
finding worth pursuing; the GET variant in 8.2 sent the same accented text correctly via
URL-encoding and was parsed fine.)

## Summary

| Item | Scenario | Result | Fully local? |
|---|---|---|---|
| 8.1 | Server boot | PASS — boots clean, no crash despite missing Supabase creds | Yes |
| 8.2 | Unauthenticated → Cliente Cero path | Routed correctly to `_resolve_cliente_cero_tenant_id()`; blocked at the Supabase round-trip (500, no live DB) — not a code regression, pre-existing env limitation (see Finding above) | Partially — code path confirmed, final 200 outcome deferred to Stage 11 (11.8) |
| 8.3 | Provisioned client JWT → own `legal_name` | Deferred — no way to mint a real Supabase JWT locally | No — Stage 11 (11.6) |
| 8.4 | Spoofed `company_id` ignored | Deferred — same reason as 8.3 | No — Stage 11 (11.6) |
| 8.5 | Unresolved tenant → `tenant_not_resolved` | Deferred — needs a real JWT for a user with no `user_tenants` row | No — Stage 11 (11.7 covers the sibling unauthenticated-401 case; this specific authenticated-unresolved case has no dedicated Stage 11 item and should be spot-checked manually if a test user without tenant membership exists in production) |
| 8.6 | Deleted route → 404 | PASS | Yes |
| 8.7 | Malformed body → 422 | PASS (both variants) | Yes |

## Server shutdown

Background uvicorn process (PID 15344) stopped cleanly via `taskkill /F /PID 15344` after all
curl commands completed.
