## Why

The B2C "Renta Natural 2026" Kanban funnel (`crm_leads`, Change B, archived) has a `whatsapp_phone`
column and a `NUEVOS` stage designed to receive inbound WhatsApp leads, but no WhatsApp channel
exists to feed it — leads can only be seeded/advanced manually in the Búnker today. Taty
(`taty_service.py`) is a fiscal-advisor agent for already-onboarded tenants; it has no notion of a
pre-signup lead. This change gives Taty a WhatsApp-based sales/onboarding front door: detect a
prospect's interest, persist what's learned about them, and advance them through the existing
funnel — all logic buildable and testable now against simulated inbound messages, since the real
WhatsApp Business number/token is a manual founder step outside this repo's code (an "open
decision to lock later" per the Sell Machine plan).

## What Changes

- New WhatsApp Cloud API channel: `presentation/whatsapp_endpoints.py` (`GET /webhook` hub.challenge
  verification mirroring `meta_endpoints.py` exactly; `POST /webhook` inbound handling) +
  `channels/whatsapp.py` (inbound normalizer + `send_whatsapp_message()` outbound sender mirroring
  `channels/telegram.py`'s pattern).
- **New, separate lead-scoped router** (`services/taty_lead_router.py`) — NOT an extension of
  `taty_intent_router.py`, which is tenant-scoped (existing onboarded tenants asking about their
  own fiscal status) and has no notion of a pre-signup `crm_leads` row. The new router reuses the
  same proven pattern (deterministic keyword classification, escalation-to-approval-queue idiom)
  but operates on lead identity (`whatsapp_phone` → `crm_leads.id`), not `tenant_id`. See design.md
  Decision 1 for why extending the existing router was rejected.
- Sales/lead intents: interest in Renta Natural, pricing/help requests, a payment-confirmation
  intent ("ya pagué") — the last one **stubbed**, since Change C (Wompi) hasn't landed yet (see
  below).
- Persists "User Persona State" (`es_asalariado`, `topes`) into `crm_tax_profiles` as the
  conversation progresses, via the existing `CrmService.update_tax_profile(lead_id, patch)`
  (unmodified, Change B).
- Advances a lead `NUEVOS → PROSPECTOS` on detected sales intent, via the existing
  `CrmService.advance_lead(lead_id, stage)` (unmodified, Change B) — no duplicate transition logic.
- **Explicitly stubbed, not faked**: `generate_wompi_link` / `verify_wompi_transaction` tools raise
  a clear "not yet available" response rather than a fake payment flow — closed for real by Change
  C.
- **BREAKING**: none — this is entirely additive; no existing endpoint, table, or service changes
  behavior.

## Capabilities

### New Capabilities
- `taty-whatsapp-sales-router`: WhatsApp Cloud API channel + lead-scoped sales/onboarding routing
  for Taty, feeding the existing B2C Kanban funnel.

### Modified Capabilities
(none — `crm-b2c-sell-machine-cockpit`'s `advance_lead`/`update_tax_profile` behavior is reused
unmodified; this change is purely a new inbound channel driving those existing, unchanged
functions)

## Impact

- **New tables**: none. Reuses `crm_leads`/`crm_tax_profiles` (Change B) as-is — `whatsapp_phone`
  already serves as the identity/mapping key, confirmed live via Supabase MCP, so no new
  `whatsapp_chat_mappings` table is needed (a deviation from the original plan sketch, justified in
  design.md Decision 2).
- **New config**: `WHATSAPP_CANONICAL` flag (new — this is a new channel surface, not an extension
  of an already-live flag, unlike Change F's reuse of `SELL_MACHINE_CANONICAL`). `WHATSAPP_TOKEN`,
  `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (read via `os.getenv`, matching
  `META_WEBHOOK_VERIFY_TOKEN`'s existing pattern — not added to `config.py`'s pydantic Settings).
- **New endpoints**: `/channels/whatsapp/webhook` (GET+POST), registered in `router.py` behind
  `WHATSAPP_CANONICAL`.
- **No frontend change** — this is an inbound channel, not a Búnker screen. The Búnker's existing
  B2C Kanban tab (Change B) already displays whatever leads land in `crm_leads`, unmodified.
- **Out of scope**: going live with a real WhatsApp Business number/token (manual, outside this
  repo); the real Wompi tools (Change C); anything Hermes/Manus-side.
