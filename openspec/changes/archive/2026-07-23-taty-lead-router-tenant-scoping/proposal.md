## Why

There are now two independent "find-or-create a `crm_leads` row by WhatsApp phone" implementations on the same table. `CrmService.whatsapp_intake` (added for `chatwoot-hermes-taty-bridge`) looks up by `tenant_id` + `whatsapp_phone`, matching `crm_leads`' `UNIQUE (tenant_id, whatsapp_phone)` constraint. The older `taty_lead_router.find_or_create_lead` (shipped in `taty-whatsapp-sales-router`) looks up by `whatsapp_phone` alone — safe only by accident, because today there is exactly one tenant (Cliente Cero). This repo is actively building multi-tenant support elsewhere (`per-tenant-client-access`), so this latent cross-tenant lookup risk needs closing now, not after a second tenant exists and a phone number collides.

## What Changes

- `taty_lead_router.find_or_create_lead` becomes a thin wrapper around `CrmService.whatsapp_intake`, instead of running its own duplicate, phone-only Supabase query and its own duplicate Cliente Cero tenant-resolution query.
- `CrmService.whatsapp_intake` gains an optional `full_name` parameter (set only on creation) so `find_or_create_lead`'s existing `full_name` capability (used by `whatsapp_endpoints.py` from the inbound message's `actor_name`) is preserved, not silently dropped.
- `find_or_create_lead`'s existing `-> str` (lead_id) return signature is preserved exactly — no caller (`whatsapp_endpoints.py`, tests) needs to change how it calls this function.
- No **BREAKING** change to any public contract; this is an internal de-duplication + tenant-scoping fix.

## Capabilities

### New Capabilities
(none — this modifies existing capabilities only)

### Modified Capabilities
- `taty-whatsapp-sales-router`: the lead find-or-create requirement is tightened to require tenant-scoped lookup and to delegate to `CrmService.whatsapp_intake` rather than duplicating the query.

Note: `whatsapp_intake` also gains an optional `full_name` parameter as part of this change, but that is an implementation detail of `crm-b2c-sell-machine` (an additive input with no observable requirement/behavior change to that capability's existing spec) — not listed as a modified capability per its own scope.

## Impact

- Modified: `apps/backend/services/taty_lead_router.py` (`find_or_create_lead`), `apps/backend/services/crm_service.py` (`whatsapp_intake` signature), `apps/backend/tests/test_taty_lead_router.py` (mocks currently assert on the old direct-Supabase-query shape; must be updated to assert delegation to `CrmService.whatsapp_intake` instead), `apps/backend/tests/test_crm_whatsapp_intake.py` (extend for the new optional `full_name` param).
- No API surface change — `POST /api/v1/channels/whatsapp/webhook` (feature-flag gated, `WHATSAPP_CANONICAL`) and `POST /api/v1/crm/leads/whatsapp-intake` both keep their existing external contracts.
- Migration note: `whatsapp_intake`'s phone normalization (`_normalize_whatsapp_phone` — strips non-digits, keeps a leading `+`) differs from `find_or_create_lead`'s previous literal/unnormalized match. Any pre-existing `crm_leads` row created via the old unnormalized path with a phone format that normalizes differently could, in theory, fail to match on the next inbound message and create a duplicate row. Given this is a single-tenant, pre-production deployment (`WHATSAPP_CANONICAL` defaults `False` — this channel has never received real traffic), there is no production data to migrate; flagged in `design.md` as a risk for completeness, not a blocking migration step.
