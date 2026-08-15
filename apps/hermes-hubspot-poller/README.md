# hermes-hubspot-poller

One-way sync worker: Supabase (`crm_leads`, `b2b_clients`) -> HubSpot (Contacts + Deals,
Companies). Runs **local to Hermes only** — never on Railway/Vercel — so the HubSpot Private
App Access Token and the Supabase service-role key never leave this machine.

See `openspec/changes/hubspot-sync-renta-natural/` for the full proposal/design/specs.

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
