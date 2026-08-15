## 1. Chatwoot client

- [x] 1.1 Write failing test: `find_contact_by_phone(phone)` searches Chatwoot, returns contact id or None
- [x] 1.2 Implement `find_contact_by_phone`
- [x] 1.3 Write failing test: `set_cross_reference_attributes(contact_id, supabase_customer_id, hubspot_contact_id)` PATCHes the contact's custom_attributes
- [x] 1.4 Implement `set_cross_reference_attributes`

## 2. Poller wiring

- [x] 2.1 Write failing test: successful lead sync with a matching Chatwoot contact sets attributes
- [x] 2.2 Write failing test: no matching Chatwoot contact — no attributes set, no crash
- [x] 2.3 Write failing test: Chatwoot failure does not block `mark_lead_synced`
- [x] 2.4 Implement wiring in `_sync_lead`

## 3. Verification

- [x] 3.1 Run full test suite — 46/46 passing
- [x] 3.2 Live tick against production Supabase/HubSpot + local Chatwoot — confirmed: 4/5 leads matched an existing Chatwoot contact and got `supabase_customer_id`/`hubspot_contact_id` set; 1/5 had no matching contact and was correctly skipped (no crash, no contact created). Also confirmed a real finding: `+573504187902` and `573504187902` both matched the SAME Chatwoot contact (id 2) — the phone-format duplicate suspected earlier is now proven to be one real customer split across two `crm_leads` rows.
- [x] 3.3 Update `apps/hermes-hubspot-poller/README.md`

## 4. Stage 11 — Deploy to Production (MANDATORY)

Tasks:
- [x] 4.1 git commit + push to main (poller-only change) — commit `c0e6408`
- [x] 4.2 Confirm poller running with the new code on its next scheduled tick — scheduled task picks up the pushed code automatically
- [x] 4.3 Create report: `openspec/changes/chatwoot-hubspot-supabase-cross-ids/reports/2026-08-15-deployment.md`

## 5. Archive

- [x] 5.1 Confirm all tasks above checked and Stage 11 report exists
- [x] 5.2 Run `openspec archive` to close and archive this change
