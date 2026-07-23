# Step 7 — Manual Endpoint Testing with curl

**Date:** 2026-07-23
**Environment:** local worktree (`.claude/worktrees/approval-queue-tenant-scoping`), no
`SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY`/`.env` present (confirmed empty in Sections 1-6).
This is the environment's actual state, not a choice — there is no live Supabase connection
available in this session.

## Scope and honest framing

This section proves the **auth and tenant-scope-resolution code paths execute correctly up to
the Supabase DB boundary**. It does **not** and **cannot** prove a genuine DB round-trip
(insert/select/update against `approval_queue`) — that requires live credentials this
environment does not have. Full DB-backed verification against production data is explicitly
deferred to **Stage 11 / task 10.5** (`GET /api/v1/approval-queue` with no token → 401 in prod;
founder Búnker smoke test; provisioned-client tenant isolation; Supabase `tenant_id IS NULL`
count), which is why that section exists as a separate mandatory gate. This is by design per
`tasks.md` Section 10.5, not a gap in this section's execution.

Every command below was actually run against a live local `uvicorn` process (not simulated) and
every response shown is the real, unedited output.

## 7.1 — Start the backend locally

```
cd apps/backend
AUTH_ENFORCED=false python -m uvicorn main:app --port 8000
```

**Result:** starts successfully.

```
[STARTUP] Loading routers...
[STARTUP] Health router loaded
[STARTUP] Metrics router loaded - /api/v1/monitoring/metrics
INFO - Secrets router registered successfully
[STARTUP] Attempting WebSocket router...
[STARTUP] WebSocket router SUCCESS
INFO - WebSocket router registered successfully
INFO - Agent router imported. Routes count: 8
INFO - Agent endpoints router registered successfully. Total API router routes: 61
INFO - Approval queue router registered successfully
INFO:     Started server process [24768]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Confirmed independently that `settings.SUPABASE_URL == ''` and `settings.AUTH_ENFORCED ==
False` at process start (this session, no `.env`, no env vars set) — the constraint stated in
the task prompt. Also confirmed directly (outside the server) what `create_client('', '')`
raises:

```
$ python -c "from supabase import create_client; create_client('', '')"
SupabaseException: supabase_url is required
```

This exact exception is what every downstream test below hits once code reaches a Supabase
call — expected and predicted, not a surprise.

## 7.2 — `GET /api/v1/approval-queue` with no token (staging identity)

```
curl -s -i http://127.0.0.1:8000/api/v1/approval-queue
```

**Response:**
```
HTTP/1.1 500 Internal Server Error
content-type: application/json

{"detail":"Error interno del servidor"}
```

**Server-side traceback (uvicorn stderr):**
```
File ".../presentation/approval_queue_endpoints.py", line 93, in list_drafts
    scope = resolve_request_tenant_scope(user, get_service_supabase())
File ".../core/tenant_context.py", line 58, in resolve_request_tenant_scope
    cliente_cero_id = resolve_cliente_cero_tenant_id(client)
File ".../core/tenant_context.py", line 22, in resolve_cliente_cero_tenant_id
    result = client.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()
File ".../infrastructure/supabase_client.py", line 15, in _ensure_initialized
    self._client = create_client(settings.SUPABASE_URL, key)
File ".../supabase/client.py", line 47, in __init__
    raise SupabaseException("supabase_url is required")
```

**Interpretation:** `AUTH_ENFORCED=false` + no token → `get_current_user` correctly falls
through to `_STAGING_USER` (no exception there, no DB call needed for that step — matches
`core/deps.py`'s documented behavior). The endpoint then calls
`resolve_request_tenant_scope(user, get_service_supabase())`, which — for the staging identity
— must call `resolve_cliente_cero_tenant_id(client)` to look up the real Cliente Cero UUID
(`core/tenant_context.py:65-66`, outcome 3 of its docstring). That is the first real Supabase
call in the request, and it fails immediately at client construction (empty
`SUPABASE_URL`) — proving the routing/auth logic (staging fallback) is reached correctly and
the code stops exactly at the DB boundary, not before or after it.

## 7.3 — `POST /enqueue` with no token (staging)

```
curl -s -i -X POST http://127.0.0.1:8000/api/v1/approval-queue/enqueue \
  -H "Content-Type: application/json" \
  -d '{"draft_id":"test-draft-1","draft_type":"tax_correction","lines":[{"account":"1110","debit":100,"credit":0,"description":"test"}],"memo":"curl test"}'
```

**Response:**
```
HTTP/1.1 500 Internal Server Error
{"detail":"Error interno del servidor"}
```

**Interpretation:** identical breaking point — `resolve_request_tenant_scope` is called before
`ApprovalQueueService.enqueue_draft` is ever reached (`presentation/approval_queue_endpoints.py`
lines 137-154), so this proves the endpoint resolves scope *before* attempting the write, exactly
as designed (no silent Cliente Cero fallback happens; the 403-vs-500 distinction depends on
scope being resolvable at all, which requires DB access here). **No row was created** (the
Supabase client never initialized) — no cleanup needed, "restore state" step is a no-op in this
environment.

## 7.4 — Tenant-scoped path: locally-signed JWT

No real Supabase Auth session is available locally, so per the task's documented fallback, a
local backend-issued JWT was constructed with `core.security.create_access_token` (this backend's
own HS256 signer used by `core/deps.py::verify_token`), restarting the server with an explicit
`JWT_SECRET` so a same-process token could be minted and verified:

```
JWT_SECRET=local-test-secret-for-curl-testing-only-32chars uvicorn main:app --port 8000
```

```python
from core.security import create_access_token
token = create_access_token({
    "sub": "aaaaaaaa-1111-4111-8111-111111111111",
    "email": "test-client@example.com",
    "workspace_id": "75c97251-8caa-41c6-8a7a-01eb8eb2acb1",
})
```

```
curl -s -i http://127.0.0.1:8000/api/v1/approval-queue -H "Authorization: Bearer $TOKEN"
```

**Response:**
```
HTTP/1.1 500 Internal Server Error
{"detail":"Error interno del servidor"}
```

**Server log (identity-resolver, before the 500):**
```
identity-resolver - ERROR - User resolution by email failed for test-client@example.com: supabase_url is required
identity-resolver - ERROR - Tenant resolution by company_id failed for contexia-org-1: supabase_url is required
```

**Interpretation — this proves more of the pipeline than 7.2/7.3:**
1. `verify_token(token)` (local HS256, `core/security.py`) succeeds — no network call, proves
   the JWT itself is valid and parsed.
2. `identity_resolver.resolve(sub, email, workspace_id)` is invoked (`core/deps.py:130`) and
   **does not crash the request** — `IdentityResolver.resolve_user_uuid` /
   `resolve_tenant_uuid` each wrap their Supabase calls in `try/except Exception` and fail
   closed (return `None`, log the error) per `core/identity_resolver.py:80-82,111-117`. This is
   visible directly in the log lines above.
3. `get_current_user` therefore returns successfully with `resolved_tenant_id=None` (never
   raises) — a materially different code path from 7.2/7.3's staging identity.
4. The endpoint's own `resolve_request_tenant_scope(user, get_service_supabase())` call is what
   ultimately raises — `resolve_cliente_cero_tenant_id` (`core/tenant_context.py:22`) has **no**
   try/except, so this is the first unguarded Supabase call in the authenticated-caller path,
   and it is exactly the DB boundary the task description predicted.

**Chain confirmed to break at:** `core.tenant_context.resolve_cliente_cero_tenant_id` (an
un-guarded `client.table("tenants")...execute()` call), reached only *after* JWT verification
and identity resolution both ran for real. This is the deepest point reachable in this scoping
logic without live Supabase credentials.

## 7.5 — `POST /approve` / `POST /reject` happy path + cross-tenant

```
curl -s -i -X POST http://127.0.0.1:8000/api/v1/approval-queue/approve \
  -H "Content-Type: application/json" \
  -d '{"decision_id":"00000000-0000-0000-0000-000000000001","reason":"curl test approve","approved_by":"tester@contexia.online"}'
```
```
HTTP/1.1 500 Internal Server Error
{"detail":"Error interno del servidor"}
```

```
curl -s -i -X POST http://127.0.0.1:8000/api/v1/approval-queue/reject \
  -H "Content-Type: application/json" \
  -d '{"decision_id":"00000000-0000-0000-0000-000000000001","reason":"curl test reject","rejected_by":"tester@contexia.online"}'
```
```
HTTP/1.1 500 Internal Server Error
{"detail":"Error interno del servidor"}
```

**Interpretation:** both routes call `resolve_request_tenant_scope(user, get_service_supabase())`
before touching `ApprovalQueueService.approve_draft`/`reject_draft` at all
(`presentation/approval_queue_endpoints.py` lines 189/228), so they break at the same DB boundary
as 7.2-7.4, before ever reaching the tenant-filtered `.eq("tenant_id", ...)` select/update logic
added in Section 2 (`services/approval_queue_service.py`). That happy-path/cross-tenant behavior
(scoped select+update, "not found" on cross-tenant) is exercised for real by the mocked-client
unit tests in `test_approval_queue_service_scoping.py` (Section 2) and the endpoint-level tests
in `test_approval_queue_endpoint_tenant_scoping.py` (Section 4, `test_approve_passes_caller_tenant_scope`,
`test_admin_approve_passes_unrestricted_scope`, and the reject symmetry tests) — both green
(Sections 2 and 4 report 100% pass). curl cannot add anything beyond what those tests already
proved without a live DB; documenting that explicitly rather than re-asserting it.

## 7.6 — Error cases

### `AUTH_ENFORCED=true`, no token — restart required (env read once at import)

```
AUTH_ENFORCED=true JWT_SECRET=local-test-secret-for-curl-testing-only-32chars \
  uvicorn main:app --port 8000
```

All four routes, no `Authorization` header:

| Route | Status | Body |
|---|---|---|
| `GET /api/v1/approval-queue` | **401** | `{"detail":"Invalid or missing authentication token"}` |
| `POST /api/v1/approval-queue/enqueue` | **401** | same |
| `POST /api/v1/approval-queue/approve` | **401** | same |
| `POST /api/v1/approval-queue/reject` | **401** | same |
| `GET /api/v1/approval-queue` with `Authorization: Bearer not-a-real-jwt` | **401** | same |

All five also carried `www-authenticate: Bearer`.

**Interpretation:** this is the one sub-task in Section 7 that is **fully DB-independent and
fully proven end-to-end** — `get_current_user`'s `AUTH_ENFORCED` gate (`core/deps.py:138-143`)
raises `401` before any endpoint code, before `resolve_request_tenant_scope`, before any
Supabase call whatsoever. No Supabase client is ever constructed for these five requests
(confirmed: no traceback in the server log for any of them, only the four 401 lines). This is a
genuine, complete verification, not a truncated one — reproduces the exact behavior tasks.md
asks for and is the same check task 10.5 re-runs against production
(`GET /api/v1/approval-queue` with no token → 401 confirms `AUTH_ENFORCED=true` live).

### Malformed `decision_id`

Not independently reachable in this environment: `ApprovalQueueService.approve_draft`/
`reject_draft` (where a malformed UUID would surface as a Postgres/Supabase error, unchanged by
this OpenSpec change) is never reached — every attempt breaks earlier, at
`resolve_request_tenant_scope`'s Supabase call (see 7.5). The relevant "existing error handling
unchanged" claim from the task is verified by inspection instead: `approval_queue_service.py`'s
`approve_draft`/`reject_draft` bodies were touched only to add `tenant_id` filtering
(`.eq("tenant_id", ...)`, Section 2 design) — the surrounding try/except and error-message
construction for a bad `decision_id` was not modified by this change (confirmed via `git diff`
against the pre-change version in Section 2's commit `d75e90f`, which shows only the
tenant-filter additions, no change to the existing error path).

## Summary of what curl was able to prove vs. what remains for Stage 11

| Layer | Proven locally by curl (7.1-7.6)? |
|---|---|
| Server starts, all routers (incl. approval-queue) register | Yes (7.1) |
| `AUTH_ENFORCED=false` staging-identity fallback is reached | Yes (7.2, 7.3) |
| `AUTH_ENFORCED=true` → 401 with no valid token, zero DB calls | Yes, fully (7.6) |
| Local JWT verification (`verify_token`) succeeds independent of DB | Yes (7.4) |
| `identity_resolver` fails closed (catches, doesn't crash) on DB error | Yes (7.4, server log) |
| Endpoints call `resolve_request_tenant_scope` before any write/read | Yes, for all 4 routes (7.2-7.5) |
| Real DB round-trip: row insert, tenant-scoped select/update, cross-tenant "not found" | **No** — requires live Supabase credentials. Proven by mocked unit tests (Sections 2, 4) instead; genuine end-to-end DB proof deferred to Stage 11 / task 10.5 |

## Cleanup

- Both uvicorn processes started for this section (`AUTH_ENFORCED=false` and
  `AUTH_ENFORCED=true` variants) were killed after testing (`taskkill /F` on their PIDs).
- No rows were created in any datastore (every write attempt failed before reaching Supabase) —
  no state to restore.
- Verified the server is down after cleanup: a curl to `127.0.0.1:8000` after `taskkill` returns
  no HTTP response (connection refused), confirming no orphaned process was left listening.
