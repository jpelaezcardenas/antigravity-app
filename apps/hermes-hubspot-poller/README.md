# hermes-hubspot-poller

One-way sync worker: Supabase (`crm_leads`, `b2b_clients`) -> HubSpot (Contacts + Deals,
Companies). Runs **local to Hermes only** — never on Railway/Vercel — so the HubSpot Private
App Access Token and the Supabase service-role key never leave this machine.

Every tick also:
- Logs a HubSpot **Note** on a lead's Contact with `crm_leads.last_message`, once, the first
  time that lead is synced.
- Sets the Deal's **`amount`** from the lead's latest `crm_wompi_transactions.amount_cents`.
- Creates a follow-up **Task** on the Deal when the lead reaches `POR_APROBAR`, skipping it if
  an incomplete Task is already attached.
- Self-heals a stale stored HubSpot id (e.g. after HubSpot's own contact dedup/merge) by
  creating a fresh object instead of failing the sync.
- Pushes `supabase_customer_id`/`hubspot_contact_id` as custom attributes onto the matching
  Chatwoot contact (found by phone, same local Chatwoot instance `apps/chatwoot-bridge/` uses)
  — closes the identity triangle between Supabase, HubSpot, and Chatwoot. Best-effort: a
  Chatwoot blip never blocks the HubSpot sync itself.

See `openspec/changes/archive/2026-08-15-hubspot-sync-renta-natural/` (base sync),
`openspec/changes/hubspot-activity-value-sync/` (notes/value/tasks), and
`openspec/changes/chatwoot-hubspot-supabase-cross-ids/` (Chatwoot identity linking) for the
full design.

## Setup

```bash
cd apps/hermes-hubspot-poller
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# fill in HUBSPOT_ACCESS_TOKEN and SUPABASE_SERVICE_ROLE_KEY in .env
```

## Run

```bash
python main.py            # one tick
python main.py --dry-run  # log only, touches nothing
```

## Test

```bash
pytest tests/ -v
```

## Scheduling

Same pattern as `apps/hermes-manus-poller/` — register as a local scheduled task (see that
app's `register_poller_task.ps1` / `run_poller.ps1` for the template) so it ticks on an
interval without a daemon process.

## What this does NOT do

- No writes flow HubSpot -> Supabase (one-way only).
- `b2b_clients` never becomes a HubSpot Deal — Companies only.
- No credentials are ever written to a Railway or Vercel environment variable.
