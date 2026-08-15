## Why

Contexia now runs three systems that each hold a partial view of the same lead: Chatwoot (WhatsApp conversation), Supabase `crm_leads` (operational source of truth), and HubSpot (commercial pipeline, `hubspot-sync-renta-natural`). None of them can look up the others' record for a given lead — an agent looking at a WhatsApp conversation in Chatwoot has no link to that lead's HubSpot Deal, and vice versa. This is step 1 of the founder-approved hybrid architecture (Chatwoot = operational front, HubSpot = commercial CRM, Supabase = source of truth): close the identity triangle before building anything else on top of it (custom attributes, AI qualification, churn tags).

## What Changes

- After `hermes-hubspot-poller` syncs a `crm_leads` row to HubSpot, it also pushes two cross-reference custom attributes onto the matching Chatwoot contact (found by phone number, same Chatwoot instance the WhatsApp bridge already uses):
  - `supabase_customer_id`: the `crm_leads.id` (UUID) — links back to the operational source of truth.
  - `hubspot_contact_id`: the synced HubSpot Contact id — links to the commercial pipeline.
- No new Supabase columns, no new HubSpot fields — this only writes into Chatwoot, which already supports arbitrary custom contact attributes.

## Capabilities

### New Capabilities
- `chatwoot-cross-reference-ids`: pushes `supabase_customer_id` and `hubspot_contact_id` onto a lead's Chatwoot contact after each successful HubSpot sync.

### Modified Capabilities
(none)

## Impact

- `apps/hermes-hubspot-poller/`: new minimal Chatwoot client (find contact by phone, set custom attributes — same Chatwoot REST endpoints `apps/chatwoot-bridge/chatwoot_client.py` already uses), wired into `_sync_lead` after a successful Contact/Deal upsert.
- New local-only env vars (`CHATWOOT_URL`, `CHATWOOT_API_TOKEN`, `CHATWOOT_ACCOUNT_ID`) in `apps/hermes-hubspot-poller/.env` — same Chatwoot instance and token the existing bridge already uses, never Railway/Vercel.
- No change to `apps/chatwoot-bridge/` itself — this is additive, read-adjacent to the same Chatwoot instance.
