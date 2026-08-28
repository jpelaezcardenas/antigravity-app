## Why

Chatwoot (WhatsApp inbox for Taty) is live, running infrastructure (confirmed: 4 containers up,
`localhost:3020`) — as central to Contexia's lead intake as HubSpot is to its reporting. The
freemium-onboarding master plan's business-routing rules say a natural person who crosses the UVT
threshold with continuous financial operations should become a Campaña 2 (SaaS B2B) lead, not a
Campaña 1 (Renta Natural, B2C) client. But no subdomain of the plan has verified whether a
prospect who first messages Taty on WhatsApp and fits that profile is ever surfaced as a Campaña 2
lead, or whether they silently stay inside the Renta Natural funnel forever. This investigation
answers that before Subdomain 4 (`crm-alta-tiered-provisioning`) assumes the B2B alta funnel's
only inputs are the founder's own book of contacts and the GTM wizard (Subdomain 2's finding).

## What Changes

- No code changes. This produces a findings note answering: does a Campaña-2-eligible prospect who
  messages Taty on WhatsApp get captured/flagged as a B2B lead anywhere today?
- Finding (see `design.md` for full evidence): **no.** Taty's WhatsApp lead-intent classifier
  (`taty_lead_router.py::classify_lead_intent`) has exactly three outcomes — `sales_interest`,
  `payment_confirmation`, `unknown` — all scoped to the Renta Natural tax-filing sale. The one
  signal that touches business-continuity territory, `obligado_declarar`, is a filing-threshold
  check against `UMBRAL_RENTA_COP`, explicitly documented as non-authoritative, and drives no
  branch, flag, or write anywhere. `crm_leads` has no business-type/qualification-tier column, and
  no code path anywhere in `apps/backend/` connects a `crm_leads` row to `tenants`/`b2b_clients`
  creation. The Chatwoot custom-attribute schema (`chatwoot-mcp-and-attributes`, archived
  2026-08-15) *does* define B2B-shaped dropdown values (`tipo_contribuyente: SAS`,
  `servicio_interes: creacion_empresa/CFO`), but the auto-tagging pipeline that would populate them
  automatically was explicitly scoped out as a fast-follow and was never built — those values are
  reachable only by a human agent manually tagging a conversation in the Chatwoot UI. HubSpot sync
  is hardcoded to one free-tier Deal pipeline for every `crm_leads` row, structurally incapable of
  routing a lead elsewhere.

## Capabilities

### New Capabilities
(none — investigation only, no new capability introduced)

### Modified Capabilities
(none — no spec-level behavior is changing; this note informs future design work in Subdomain 4,
which will carry its own capability changes if/when it proceeds)

## Impact

- No affected code, APIs, or systems — read-only investigation.
- Informs `openspec/changes/crm-alta-tiered-provisioning` (Subdomain 4) design work, not yet
  started: the B2B alta funnel's inputs are narrower than assumed — WhatsApp/Chatwoot is not
  (yet) a source of Campaña 2 leads, despite being Contexia's most active conversational channel.
- Files read (no changes): `apps/backend/services/taty_lead_router.py`,
  `apps/backend/services/taty_service.py`, `apps/backend/services/crm_service.py`,
  `apps/backend/migrations/0022_crm_b2c_sell_machine.sql`,
  `apps/backend/migrations/0040_hubspot_sync_crm_leads.sql`, `apps/chatwoot-bridge/main.py`,
  `apps/hermes-hubspot-poller/poller.py`, `apps/hermes-hubspot-poller/config.py`,
  `apps/hermes-hubspot-poller/stage_mapping.py`, `apps/hermes-hubspot-poller/chatwoot_client.py`,
  `openspec/changes/archive/2026-08-15-chatwoot-mcp-and-attributes/design.md`, `ARCHITECTURE.md`.
