## 1. Supabase migration: sync-state columns

- [x] 1.1 Write migration adding `hubspot_contact_id`, `hubspot_deal_id`, `last_synced_at` (nullable) to `crm_leads`
- [x] 1.2 Write migration adding `hubspot_company_id`, `last_synced_at` (nullable) to `b2b_clients`
- [x] 1.3 Apply migrations to Supabase, verify columns exist and are nullable/no-default (safe on existing rows) — applied live to project `kpynymwghfwshvcvevxq`, verified via `information_schema.columns`, no new security advisories introduced

## 2. HubSpot Private App setup (manual, founder)

- [x] 2.1 Create a HubSpot Private App with scopes for Contacts, Deals, Companies (read/write) — "Contexia Hermes Sync", accountId 51867201
- [x] 2.2 Store the Private App Access Token in local Hermes secrets — confirm it is NOT added to any Railway or Vercel env var — `apps/hermes-hubspot-poller/.env` (gitignored, verified via `git status`)
- [x] 2.3 Confirm via `discover_hubspot_schema`/`get_properties` that the token has the expected scopes before writing code against it — confirmed live via real sync run (11 Contacts+Deals, 10 Companies created successfully)

## 3. Hermes poller: lead sync (crm_leads → Contact + Deal)

- [x] 3.1 Scaffold new poller module alongside `apps/hermes-manus-poller/` (same structure/config pattern) — `apps/hermes-hubspot-poller/`
- [x] 3.2 Write failing test: given a `crm_leads` row with no `hubspot_contact_id`, poller creates a Contact + Deal and persists returned IDs
- [x] 3.3 Implement Contact + Deal creation, satisfy the test
- [x] 3.4 Write failing test: given a `crm_leads` row with existing `hubspot_contact_id`/`hubspot_deal_id`, poller upserts instead of duplicating
- [x] 3.5 Implement idempotent upsert path, satisfy the test
- [x] 3.6 Implement stage → `dealstage` mapping per design.md table (corrected to real `crm_leads.stage` values + Wompi override — see design.md Decision #4)
- [x] 3.7 Write test covering stage transition to `closedwon` and to `closedlost`

## 4. Hermes poller: B2B registry sync (b2b_clients → Company)

- [x] 4.1 Write failing test: given a `b2b_clients` row with no `hubspot_company_id`, poller creates a Company and persists the returned ID
- [x] 4.2 Implement Company creation/upsert, satisfy the test
- [x] 4.3 Write test asserting no Deal is ever created from `b2b_clients` sync

## 5. Poller scheduling and resilience

- [x] 5.1 Wire the poller into Hermes's existing scheduling mechanism (same interval pattern as `apps/hermes-manus-poller/`) — `run_poller.ps1` + `register_poller_task.ps1`, 5-min cadence
- [x] 5.2 Add basic error handling/logging so a failed HubSpot API call doesn't crash the poller loop or corrupt `last_synced_at` — fail-soft clients (never raise) + `mark_*_synced` only called after a successful HubSpot upsert
- [x] 5.3 Manual run: confirm a real `crm_leads` test row appears correctly in HubSpot (Contact + Deal in the right stage) — live run 2026-08-15: 11/11 leads synced (201 Created), correct dealstage per mapping, verified idempotent on 2nd tick

## 6. Búnker: read-only sync badge

- [x] 6.1 Add "Sincronizado ✓" badge + HubSpot deep link to lead/client rows where `last_synced_at` is non-null — `HubspotSyncBadge.tsx`, wired into `B2cKanbanTab.tsx` (deal) and `B2bRetainersTab.tsx` (company)
- [x] 6.2 Add neutral "sin sincronizar" state where `last_synced_at` is null — verify no false-positive badge (`HubspotSyncBadge` requires both `hubspotId` AND `lastSyncedAt`)
- [x] 6.3 Confirm no write action/button to HubSpot exists anywhere in this UI surface — badge is an `<a>` deep link only, no onClick/mutation

## 7. Verification

- [x] 7.1 Run full test suite for the new poller module — 21/21 passing after the resync-loop fix (`apps/hermes-hubspot-poller/tests/test_poller.py`); frontend type-checked clean (`tsc --noEmit`), backend files syntax-checked clean
- [x] 7.2 End-to-end manual check: create a test lead in Supabase, confirm it reaches HubSpot within one poll cycle, confirm Búnker badge updates — live: all 11 existing leads + 10 clients synced for real (HubSpot 201s), `last_synced_at`/`hubspot_*_id` persisted via 204s; Búnker badge reads these same columns (visual confirmation in the deployed Búnker still pending — see Stage 11)
- [x] 7.3 Confirm B2B test client syncs to Company only, never appears as a Deal — confirmed live: 10 Companies created, zero Deal calls in the b2b_clients pass

## 8. Documentation

- [x] 8.1 Update `ARCHITECTURE.md` with the new Hermes-local HubSpot poller container (containers table + a "Decisión asentada" entry #20, matching the pattern of decisions #1/#10)
- [x] 8.2 Document the pipeline stage mapping and the free-tier constraints (1 pipeline, 1,000 contacts, 2 users, no workflows) in this change's design.md (Decision #4, corrected) and `apps/hermes-hubspot-poller/README.md`

## 9. Stage 11 — Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL (Búnker badge): https://contexia.online/app/bunker
- Backend: no Railway change required (poller is Hermes-local, not a Railway service)
- Hermes poller: enabled/started as a local process, not part of Vercel/Railway CI

Tasks:
- [ ] 9.1 git commit + push to main (Supabase migration + Búnker frontend change)
- [ ] 9.2 Vercel build complete (green ✅)
- [ ] 9.3 Verify Supabase migration applied in production project
- [ ] 9.4 Confirm Hermes poller running locally and successfully syncing against production Supabase + production HubSpot account
- [ ] 9.5 Production URL: Búnker badge visible and working for a real synced lead
- [ ] 9.6 Create report: `openspec/changes/hubspot-sync-renta-natural/reports/YYYY-MM-DD-deployment.md`

## 10. Archive

- [ ] 10.1 Confirm all tasks above checked and Stage 11 report exists
- [ ] 10.2 Run `openspec-archive-change` to close and archive this change
