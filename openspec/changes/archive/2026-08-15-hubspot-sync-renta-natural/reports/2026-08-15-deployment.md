# Deployment Report — hubspot-sync-renta-natural

**Date:** 2026-08-15
**Commit:** `955a7f5` (pushed `3214cff..955a7f5` to `main`)
**Vercel deployment:** `dpl_5qdpW3yDLKpQdmfy7NesVyVz6v11` — state `READY`, target `production`
**Supabase project:** `kpynymwghfwshvcvevxq`
**HubSpot account:** `51867201` (STANDARD/free tier)

## What shipped

- Migrations `0040`/`0041`: nullable `hubspot_contact_id`/`hubspot_deal_id`/`last_synced_at` on `crm_leads`, `hubspot_company_id`/`last_synced_at` on `b2b_clients`. Applied live to `kpynymwghfwshvcvevxq`, verified via `information_schema.columns` (all nullable, no default).
- `apps/hermes-hubspot-poller/`: Hermes-local sync worker (Python/httpx), scheduled every 5 minutes via Windows Task Scheduler (`ContexiaHermesHubspotPoller`, registered by the founder). Credentials (`HUBSPOT_ACCESS_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`) live only in the local `.env`, gitignored, never in Railway/Vercel.
- `crm_service.py` / `crm_endpoints.py`: extended the existing `list_b2b_clients`/`b2b_payments_grid`/`b2c_pipeline` column selects to project the new sync columns to the frontend.
- `HubspotSyncBadge.tsx` wired into `B2cKanbanTab.tsx` (Deal badge) and `B2bRetainersTab.tsx` (Company badge) — read-only, no write path to HubSpot from the Búnker.
- HubSpot pipeline stages renamed to Spanish via the Pipelines API (`crm.schemas.deals.write` scope on the Private App token) — internal `value`s untouched, only display `label`s changed.

## Live verification

- Full real sync run: 11 leads (Contact+Deal, `201 Created`) + 10 B2B clients (Company, `201 Created`) on first tick.
- Idempotency confirmed: second tick `PATCH`'d the same stored HubSpot ids (`200 OK`), zero duplicates.
- Two real bugs found and fixed during this verification (see design.md Decisions #6/#7):
  1. PostgREST can't compare two columns of the same row in its filter query string — fixed by filtering client-side.
  2. The original "only resync if `updated_at > last_synced_at`" filter self-perpetuated (the sync's own `PATCH` bumps `updated_at` via trigger) — scoped down, then revised again per the founder's explicit requirement that the pipeline reflect live conversation stage: every tick now re-syncs every row (cheap at ~15-record scale).
- 6 seed/smoke-test leads (`SEED-WA-001..004`, "Stage 11 Smoke Test Lead", "Stage 11 Change H Lead") cleaned up from both HubSpot (Contact+Deal, `204` deletes) and Supabase (`crm_leads` rows deleted) — confirmed not recreated by the next tick.
- Test suite: 21/21 passing (`apps/hermes-hubspot-poller/tests/test_poller.py`).

## Known follow-ups (non-blocking)

- Two leads (`+573504187902` / `573504187902`) are likely the same WhatsApp contact recorded twice due to a `+` formatting difference — flagged to the founder, not resolved in this change (needs a decision on merge behavior in `crm_leads`, out of scope here).
- HubSpot free-tier ceiling (1,000 contacts) not actively monitored — flagged in design.md as a future decision, not solved here.
- Custom HubSpot properties and dashboards/reports — explicitly deferred by the founder, not part of this change's scope.
