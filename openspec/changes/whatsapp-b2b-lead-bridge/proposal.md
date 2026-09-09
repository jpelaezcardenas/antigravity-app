## Why

WhatsApp is Contexia's most active live channel (Taty, Chatwoot inbox `1`), but a prospect who
messages Taty and would qualify for the B2B SaaS plan (Campaña 2 — a persona jurídica, or a
natural person crossing UVT with continuous financial operations) is invisible to the system as a
B2B lead today. Confirmed by investigation
(`openspec/changes/archive/2026-08-28-chatwoot-b2b-lead-capture-investigation/reports/2026-08-28-findings.md`):
Taty's WhatsApp classifier only recognizes `sales_interest`/`payment_confirmation`/`unknown`, all
scoped to selling Renta Natural (Campaña 1); `crm_leads` has no B2B signal column and nothing ever
promotes a row to `tenants`/`b2b_clients`; and Chatwoot's own `tipo_contribuyente`/
`servicio_interes` attributes exist but are only ever filled by a human reading the conversation.
The founder is prioritizing this over finishing `real-data-ingestion-mvp` because every day without
it is a live B2B lead lost during peak Renta Natural season, when WhatsApp volume is highest.

## What Changes

- `TatyAgentService`'s WhatsApp intent classification gains a `business_interest` signal
  (alongside the existing `sales_interest`/`payment_confirmation`/`unknown`), detecting language
  consistent with Campaña 2 (persona jurídica, "empresa", "SAS", "contabilidad del negocio",
  continuous-operations natural person) without changing existing Campaña 1 classification
  behavior.
- When `business_interest` is detected, the backend writes/updates the Chatwoot conversation's
  existing `tipo_contribuyente`/`servicio_interes` custom attributes automatically (closing the
  "fast-follow never built" gap), instead of only a human agent filling them.
- The same detection creates or updates the corresponding `crm_leads` row with an explicit B2B
  qualification signal, so it becomes visible for a Contexia operator to act on (manual alta via
  the existing `crm-alta-tiered-provisioning` flow) — this change does NOT auto-provision a tenant;
  it makes the lead visible, provisioning stays a human decision.
- No changes to the Campaña 1 (Renta Natural) reply content, pricing, or the existing
  `hubspot-sync-renta-natural` poller's Deal-stage mapping — B2B leads surfaced by this change
  follow the existing rule that B2B never syncs to HubSpot Deals, only Companies once provisioned.

## Capabilities

### New Capabilities
- `whatsapp-b2b-lead-signal`: detecting and persisting a B2B-lead signal from a WhatsApp/Taty
  conversation into `crm_leads` and the conversation's Chatwoot attributes.

### Modified Capabilities
- `taty-whatsapp-sales-router`: the intent classifier gains the `business_interest` category
  alongside its existing three; routing/reply behavior for the existing categories is unchanged.

## Impact

- Backend: `apps/backend/services/taty_lead_router.py` (or wherever the WhatsApp intent classifier
  lives — confirm exact file during design), `TatyAgentService`, `crm_leads` write path.
- Chatwoot: automated write to existing custom attributes `tipo_contribuyente`/`servicio_interes`
  on inbox `1` conversations (no new attribute schema).
- Does not touch `tenants`/`b2b_clients` provisioning — reuses `crm-alta-tiered-provisioning`
  (already archived, human-triggered) for the actual alta.
- Does not touch `hermes-hubspot-poller`'s Deal/Company sync rules (Decisión #20).
