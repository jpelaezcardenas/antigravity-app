## Why

`hubspot-sync-renta-natural` (archived 2026-08-15) syncs leads and B2B clients into HubSpot as bare records — Contacts and Deals with no conversation history, no deal value, and no follow-up reminders. The founder wants to actually work the pipeline inside HubSpot (see conversation history, see how much money is in the funnel, get reminded to follow up), not just see names on a board. All three gaps are closeable with data the sync already has access to (`crm_leads.last_message`, `crm_wompi_transactions.amount_cents`, `crm_leads.stage`).

## What Changes

- Log Taty's latest WhatsApp message as a HubSpot **Note** (engagement) on the synced Contact whenever `crm_leads.last_message` changes — gives visible conversation history in HubSpot without duplicating Chatwoot/Taty's own history.
- Set the HubSpot Deal's **`amount`** property from the lead's latest `crm_wompi_transactions.amount_cents` (COP, converted from minor units) when a transaction exists.
- Create a HubSpot **Task** on the Deal when a lead reaches `POR_APROBAR` (needs human payment approval) — a visible reminder in HubSpot's own task list, not just the Búnker's "Aprobar Pago" button.

## Capabilities

### New Capabilities
- `hubspot-activity-logging`: syncs each lead's latest WhatsApp message as a HubSpot Note on its Contact.
- `hubspot-deal-value-and-tasks`: sets Deal `amount` from the latest payment transaction, and creates a follow-up Task when a lead needs approval.

### Modified Capabilities
(none — additive only, no existing requirement changes)

## Impact

- `apps/hermes-hubspot-poller/hubspot_client.py`: new functions to create Engagement Notes and Tasks (HubSpot Engagements API, `/crm/v3/objects/notes`, `/crm/v3/objects/tasks`, with associations to the Contact/Deal).
- `apps/hermes-hubspot-poller/poller.py`: `_sync_lead` extended to call these after the existing Contact/Deal upsert.
- No new Supabase columns needed — reuses `crm_leads.last_message`, `crm_wompi_transactions.amount_cents`, `crm_leads.stage` as already read.
- No Búnker/frontend change — this is HubSpot-side enrichment only.
