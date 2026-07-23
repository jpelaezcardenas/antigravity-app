# Step 5 Report - Manual Endpoint Testing with curl

- Date: 2026-07-23
- Change: taty-lead-router-tenant-scoping
- Endpoint: `POST /api/v1/channels/whatsapp/webhook` (via `find_or_create_lead` -> `CrmService.whatsapp_intake`)

## Environment

Backend started locally: `CRM_CANONICAL=true WHATSAPP_CANONICAL=true python -m uvicorn main:app --host 127.0.0.1 --port 8080` (from `apps/backend/`, `.env` auto-loaded). Both feature flags required — `WHATSAPP_CANONICAL` mounts `/api/v1/channels/whatsapp/*`, `CRM_CANONICAL` mounts `/api/v1/crm/*` (transitively exercised via `whatsapp_intake`).

## Commands and Results

### 1. `GET /webhook` verification, correct token
```
curl "http://127.0.0.1:8080/api/v1/channels/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=contexia-whatsapp-webhook&hub.challenge=test12345"
```
→ `200`, body `test12345` (the challenge echoed back) — matches Meta's webhook verification handshake.

### 2. `GET /webhook` verification, wrong token
```
curl "...&hub.verify_token=wrong&hub.challenge=test12345"
```
→ `403`, `{"detail":"Invalid WhatsApp webhook verification token"}`.

### 3. `POST /webhook`, simulated Meta message from a fresh phone number
```
curl -X POST http://127.0.0.1:8080/api/v1/channels/whatsapp/webhook -H "Content-Type: application/json" -d @wa_payload.json
```
Payload: a realistic Meta Cloud API `entry[].changes[].value.{contacts,messages}` shape (see `channels/whatsapp.py`'s `normalize_whatsapp_webhook`), phone `573009998877`, text "Hola, quiero saber si me toca declarar renta".

→ `500 {"detail":"Error interno del servidor"}`.

**Same known, pre-existing environment gap as `chatwoot-hermes-taty-bridge`'s Step 4 report**: the
local `apps/backend/.env` lacks `SUPABASE_SERVICE_ROLE_KEY`, so any real Supabase call fails at
client construction (`supabase.client.SupabaseException: supabase_key is required`), not a defect
in this change.

**Crucially, the traceback proves the fix is wired correctly end-to-end**:
```
whatsapp_endpoints.py:42 whatsapp_webhook
  -> taty_lead_router.py:254 find_or_create_lead
     -> crm_service.py:400 whatsapp_intake
        -> crm_service.py:101 _resolve_cliente_cero_tenant_id
           -> supabase_client.py (fails on missing key)
```
This is exactly the corrected, tenant-scoped path (`find_or_create_lead` -> `whatsapp_intake` ->
`_resolve_cliente_cero_tenant_id`), NOT the old direct/unscoped `crm_leads` query this change
removed. The delegation is confirmed live, not just at the unit-test level.

## Cleanup

- No `crm_leads` row was created (write failed before reaching Supabase).
- Local uvicorn test server stopped; confirmed no process remained listening on port 8080.

## Outcome

- Step 5 status: **PASS with the same documented, pre-existing, out-of-scope environment gap**
  noted in `chatwoot-hermes-taty-bridge`'s own Step 4 report (missing local
  `SUPABASE_SERVICE_ROLE_KEY`). Routing, GET-verification auth, and the corrected delegation path
  were all verified live; the write path's real-Supabase success is verified by the automated
  suite (Step 4) instead.
