## Why

Renta Natural (B2C, 2026 campaign) is a mass conversion funnel — quiz → lead → payment — with no visual pipeline or commercial reporting today; leads live only as rows in `crm_leads`. HubSpot's free tier gives exactly one deal pipeline, verified live against the account (accountId 51867201, STANDARD/free): one pipeline is enough to model the Renta Natural funnel end-to-end, but not enough to also model B2B retainer relationships as deals. B2B retainers don't need a sales-stage pipeline anyway — they're contract + recurring billing, already served by `b2b_clients`/`b2b_payments`. This change gives Renta Natural leads a kanban view and reporting layer without touching how B2B operates.

## What Changes

- One-way sync **Supabase → HubSpot** (Supabase stays authoritative; no writes flow back).
- `crm_leads` → HubSpot Contacts + Deals, using the account's single default pipeline (`pipeline: default`, "Sales Pipeline"), with its 7 stock stages remapped to the real Renta Natural funnel: Quiz Completado → Lead Calificado → Contactado → Pago Iniciado → Cliente Pagado → Perdido.
- `b2b_clients` → HubSpot Companies only, as a read-only registry (no Deals, no pipeline usage) — B2B retainers are explicitly out of this pipeline.
- New sync worker triggered by **Hermes polling**, mirroring the existing `apps/hermes-manus-poller/` pattern — HubSpot Private App Access Token lives local with Hermes, never in Railway env vars.
- Búnker gets a read-only **"Sincronizado ✓"** badge + deep link to the HubSpot record on synced leads/clients. No write actions from the Búnker to HubSpot.

## Capabilities

### New Capabilities
- `hubspot-lead-sync`: one-way sync of `crm_leads` to HubSpot Contacts + Deals in the single Renta Natural pipeline, driven by Hermes polling with local-only credentials.
- `hubspot-company-registry`: one-way sync of `b2b_clients` to HubSpot Companies as a read-only reporting registry (no deal/pipeline involvement).

### Modified Capabilities
(none — no existing spec's requirements change; this only adds new outbound sync behavior)

## Impact

- New Hermes-side worker (local/WSL, alongside `apps/hermes-manus-poller/`) holding the HubSpot Private App Access Token — never touches Railway.
- New Supabase columns/table to track sync state (e.g. `hubspot_contact_id`, `hubspot_deal_id`, `hubspot_company_id`, `last_synced_at`) on `crm_leads` and `b2b_clients`, or a dedicated `hubspot_sync_log`.
- Búnker frontend: new read-only badge + link component on lead/client rows; no new write endpoints.
- No backend (Railway) API changes required — sync runs entirely from Hermes against HubSpot's API and Supabase directly.
- External dependency: HubSpot free-tier account (1 pipeline, 1,000 contacts, 2 users, no workflows) — growth beyond those caps requires a paid-tier decision, out of scope here.
