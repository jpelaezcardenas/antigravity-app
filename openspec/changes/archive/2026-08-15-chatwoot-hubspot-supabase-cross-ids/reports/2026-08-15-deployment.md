# Deployment Report — chatwoot-hubspot-supabase-cross-ids

**Date:** 2026-08-15
**Commit:** `c0e6408`

## What shipped

- New `chatwoot_client.py` in `apps/hermes-hubspot-poller/`: `find_contact_by_phone` (search only, never creates), `set_cross_reference_attributes` (PATCH `custom_attributes`).
- `poller.py::_sync_lead`: after a successful HubSpot sync, best-effort pushes `supabase_customer_id` + `hubspot_contact_id` onto the matching Chatwoot contact.

## Live verification

- 46/46 tests passing.
- Live tick against production Supabase/HubSpot + the local Chatwoot instance (`localhost:3020`, same one `apps/chatwoot-bridge/` uses): 4/5 leads matched an existing Chatwoot contact and got attributes set; 1/5 had no Chatwoot contact and was correctly skipped.
- Real finding surfaced: `+573504187902` and `573504187902` (two separate `crm_leads` rows) both matched Chatwoot contact id 2 — confirms they are the same real customer, split by a phone-format difference. Not resolved in this change; flagged to the founder as a follow-up (merge/dedup decision needed in `crm_leads`).

## Known follow-ups

- The broader founder proposal (Chatwoot custom attributes for `tipo_contribuyente`, `lead_score`, AI-driven qualification, churn tags) is intentionally out of scope here — this change only closes the identity triangle. Those are separate future changes once this link is confirmed useful.
- Lead phone-format duplicate (`+573504187902` / `573504187902`) needs a founder decision on merge behavior.
