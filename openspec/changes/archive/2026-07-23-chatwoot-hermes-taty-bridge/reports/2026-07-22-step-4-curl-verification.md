# Step 4 Report - Manual Endpoint Testing with curl

- Date: 2026-07-22
- Change: chatwoot-hermes-taty-bridge
- Endpoint: `POST /api/v1/crm/leads/whatsapp-intake`

## Environment

Backend started locally: `CRM_CANONICAL=true python -m uvicorn main:app --host 127.0.0.1 --port 8080`
(from `apps/backend/`, `.env` auto-loaded per `config.py`'s `SettingsConfigDict(env_file=".env")`).

`CRM_CANONICAL` defaults to `False` (feature-flag gated router, per `presentation/router.py`) —
had to be set explicitly to mount `/api/v1/crm/*` at all for manual testing.

## Commands and Results

### 1. Malformed body (missing `whatsapp_phone`) — validation
```
curl -X POST http://127.0.0.1:8080/api/v1/crm/leads/whatsapp-intake -H "Content-Type: application/json" -d '{}'
```
→ `422`, `{"detail":[{"type":"missing","loc":["body","whatsapp_phone"],...}]}` — Pydantic
request-model validation correctly enforced.

### 2. Route sanity check (typo'd path)
```
curl -X POST http://127.0.0.1:8080/api/v1/crm/leads/whatsapp-intak
```
→ `404` — confirms the real route is exactly `whatsapp-intake`, no accidental alias.

### 3. Unauthenticated call, `AUTH_ENFORCED=true` (server restarted with this flag)
```
curl -X POST http://127.0.0.1:8080/api/v1/crm/leads/whatsapp-intake -H "Content-Type: application/json" -d '{"whatsapp_phone": "+573001112233"}'
```
→ `401`, `{"detail":"Invalid or missing authentication token"}` — matches
`specs/crm-b2c-sell-machine/spec.md` scenario "Call requires tenant-scoped authentication".

### 4. Invalid/garbage bearer token, `AUTH_ENFORCED=true`
```
curl -X POST ... -H "Authorization: Bearer not-a-real-token" -d '{"whatsapp_phone": "+573001112233"}'
```
→ `401` — same rejection, confirms the router-level `Depends(get_current_user)` gate runs
before the handler in both the missing- and invalid-token cases.

### 5. Successful create/lookup path — BLOCKED, documented as a known environment gap (not a
   regression from this change)

```
curl -X POST http://127.0.0.1:8080/api/v1/crm/leads/whatsapp-intake -H "Content-Type: application/json" -d '{"whatsapp_phone": "+573001112233"}'
```
→ `500 {"detail":"Error interno del servidor"}`.

Traceback shows the request reaches exactly the expected code path
(`crm_endpoints.py:whatsapp_intake` → `crm_service.py:395 whatsapp_intake` →
`_resolve_cliente_cero_tenant_id` → `client.table("tenants")`) and fails only at Supabase client
construction: `supabase.client.SupabaseException: supabase_key is required`. The local `apps/backend/.env`
has `SUPABASE_KEY=` (empty) and no `SUPABASE_SERVICE_ROLE_KEY` entry at all — a pre-existing local
dev-environment gap, not something introduced by this change.

**Confirmed pre-existing, not a regression**: the already-shipped, already-in-production
`GET /api/v1/crm/b2c/pipeline` endpoint was hit with the same running server/`.env` and returned
`200 {"source":"demo_fallback",...}` — that endpoint has an explicit demo-data fallback for
Supabase-unreachable (a *read*-endpoint UX decision, per its own spec scenario). `whatsapp_intake`
is a *write* (find-or-create); per the spec for this change there is no fallback-on-Supabase-down
requirement, and failing loudly (500) rather than silently faking a lead creation is the correct
behavior for a write path — same as every other CRM write endpoint (`create_b2b_client`,
`advance_lead`, etc.), none of which have a demo fallback either.

**Why not obtained and retried**: `SUPABASE_SERVICE_ROLE_KEY` is a production credential. Bitwarden
CLI was checked and found unauthenticated (`bw status` → `unauthenticated`) earlier this session,
and logging into it is outside what this agent can/should do. Per repo policy (no hardcoded
secrets, fail closed), this was not worked around by inventing or hardcoding a key.

**What this does NOT block**: the automated test suite (Step 3, `pytest`, mocked Supabase client)
already covers the full create/lookup/tenant-scoping behavior end-to-end at the logic level, and
was independently re-run and verified in this session (26 passed, 4 pre-existing skips). The gap
here is purely "exercise it against the real live Supabase project from a local curl session",
which requires a credential this agent does not have safe access to.

## Cleanup

- No `crm_leads` rows were created (every write attempt failed before reaching Supabase).
- No database state to restore.
- Local uvicorn test server stopped; verified via `Get-NetTCPConnection -LocalPort 8080` that no
  process remained listening on port 8080 afterward.

## Outcome

- Step 4 status: **PASS with a documented, pre-existing, out-of-scope gap** (missing local
  `SUPABASE_SERVICE_ROLE_KEY`, affects manual testing of the write path only — routing, validation,
  and auth-gating were all verified live; logic-level create/lookup/tenant-scoping is verified by
  the automated suite in Step 3).
- Blocking issues: none for this change. Follow-up: whoever has the real `SUPABASE_SERVICE_ROLE_KEY`
  should add it to `apps/backend/.env` locally (not committed) to unblock future live manual
  testing of CRM write endpoints in general — this is a local dev setup gap, not a code task.
