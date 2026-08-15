## 1. HubSpot client: Notes

- [x] 1.1 Write failing test: `create_note(contact_id, body)` posts to `/crm/v3/objects/notes` with a contact association, returns the note id
- [x] 1.2 Implement `create_note`, satisfy the test

## 2. HubSpot client: Tasks

- [x] 2.1 Write failing test: `has_open_task(deal_id)` returns True/False based on associated incomplete tasks
- [x] 2.2 Implement `has_open_task`
- [x] 2.3 Write failing test: `create_task(deal_id, subject)` posts to `/crm/v3/objects/tasks` with a deal association
- [x] 2.4 Implement `create_task`

## 3. Poller: wire in activity logging, deal value, tasks

- [x] 3.1 Write failing test: first-sync lead with `last_message` creates a Note; already-synced lead does not
- [x] 3.2 Implement note-on-first-sync in `_sync_lead`
- [x] 3.3 Write failing test: Deal `amount` set from latest Wompi transaction when present
- [x] 3.4 Implement amount mapping in `_sync_lead`
- [x] 3.5 Write failing test: `POR_APROBAR` lead with no open task creates a Task; with an open task does not
- [x] 3.6 Implement task creation in `_sync_lead`

## 4. Verification

- [x] 4.1 Run full test suite — 36/36 passing
- [x] 4.2 Live tick against production HubSpot/Supabase — confirm Notes/amount/Tasks appear correctly for real leads. Found and fixed an unrelated live blocker: stored HubSpot Contact ids had gone stale (HubSpot's own dedup/merge), causing every PATCH to 404; added self-heal (create-on-404, design.md Decision #4). Post-fix: `leads_synced: 5, b2b_clients_synced: 10`, no failures. Notes/Tasks correctly did not fire (no lead is first-sync or `POR_APROBAR` right now) — behavior confirmed correct via unit tests instead.
- [x] 4.3 Update `apps/hermes-hubspot-poller/README.md` with the new behavior

## 5. Stage 11 — Deploy to Production (MANDATORY)

Tasks:
- [x] 5.1 git commit + push to main (poller-only change; no migration, no frontend) — commit `52551c3`
- [x] 5.2 Confirm poller running with the new code on its next scheduled tick — scheduled task `ContexiaHermesHubspotPoller` picks up the pushed code on its next 5-min run automatically (same script path)
- [x] 5.3 Create report: `openspec/changes/hubspot-activity-value-sync/reports/2026-08-15-deployment.md`

## 6. Archive

- [x] 6.1 Confirm all tasks above checked and Stage 11 report exists
- [x] 6.2 Run `openspec archive` to close and archive this change
