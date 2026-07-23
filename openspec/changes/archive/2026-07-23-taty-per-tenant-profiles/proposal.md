# Taty Per-Tenant Profile Resolution

## Why
Taty (agente conversacional #5) resolves client profiles from a hardcoded `AGENT_PROFILES` dict in
`apps/backend/services/taty_service.py` with only 3 demo keys (`ctx-001`, `ferez-001`,
`martinez-001`). Any of the 10 real B2B clients provisioned by `per-tenant-client-access`
(each with their own `client_tenant_id`) gets a hard `"Cliente no configurado"` error — Taty
cannot serve a single real paying client today. Separately, `POST/GET /api/v1/agents/ask` has
**zero authentication** and takes a client-supplied, unverified `company_id` — any caller can
read any of the 3 hardcoded profiles and burn LLM spend with no accountability.

## What Changes
- **Dynamic profile resolution:** `taty_service.py` derives a profile from `tenants`
  (`legal_name`, `nit`, `company_id`) plus an in-code default template (tone, enabled sources,
  escalation keywords). No new table, no per-client seeding step — any tenant resolves
  automatically.
- **Authenticated, tenant-scoped endpoints:** `/api/v1/agents/ask` (POST + GET) adopts the
  canonical tenant-resolution pattern already used by `GET /api/v1/financials`
  (`Depends(get_current_user)` → own tenant, or Cliente Cero for the staging identity only, or a
  clear in-band error for an authenticated-but-unresolved caller — never Cliente Cero by
  accident). The request body's `company_id` becomes optional, deprecated, and ignored for
  resolution (closes the spoofing hole).
- **`ask()` signature**: `company_id` renamed to `tenant_id` across the service and all 3
  in-repo callers (dashboard endpoint, deprecated wrapper, Telegram webhook).
- **Retirements:** delete the deprecated `POST /api/v1/agents/taty/ask` route (zero consumers,
  duplicate of `/agents/ask`); delete `services/taty_intent_router.py` and its test — it is dead
  code (only its own test imports `route_message`), and reviving it as the canonical entry point
  would silently change the response contract and pull approval-queue writes into a read-only
  Q&A path. A future change may reintroduce tenant-scoped intent routing deliberately.
- **Compliance:** the prompt template no longer asserts a tax regime ("Régimen Común") for a
  client we don't actually know — the régimen clause is omitted when unset, per
  `.antigravity/GROUND_TRUTH.md` (Taty never presents unverified regulatory determinations).

## Impact
- **Specs:** NEW `taty-fiscal-assistant` capability.
- **Code:** `apps/backend/services/taty_service.py`, `presentation/taty_endpoints.py`,
  `presentation/telegram_endpoints.py`, `presentation/agents_endpoints.py`; deletes
  `services/taty_intent_router.py` + `tests/test_taty_intent_router.py`.
- **Data:** no migrations. Reads only from the existing `tenants` table.
- **Non-goals:** WhatsApp Taty (`taty_lead_router`, lead-scoped by design — untouched); Chatwoot
  bridge (active sibling change, different session — untouched); per-tenant custom
  tone/escalation overrides (the single `_get_tenant_profile()` seam supports adding this later
  without touching callers); reviving `taty_intent_router` as a live conversational-command path.
