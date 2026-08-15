# Deployment Report — hubspot-activity-value-sync

**Date:** 2026-08-15
**Commit:** `52551c3`

## What shipped

- `hubspot_client.py`: `create_note`, `has_open_task`, `create_task`, and a self-heal for stale HubSpot ids (PATCH 404 → create fresh object instead of failing).
- `poller.py::_sync_lead`: logs a Note on first sync (if `last_message` present), sets Deal `amount` from the latest Wompi transaction, creates a follow-up Task on `POR_APROBAR` (gated on no open task already existing).

## Live verification

- 36/36 tests passing.
- Live tick: found and fixed the stale-id bug (HubSpot's own contact dedup/merge had retired previously-synced ids) — after the fix, `leads_synced: 5, b2b_clients_synced: 10`, zero failures.
- Notes/Tasks did not fire in this run (no lead was first-sync or in `POR_APROBAR` at the time) — correct per the gating logic, confirmed via unit tests instead of a live trigger.

## Known follow-ups

- Note-on-first-sync-only (not live-updating) — documented limitation, fast-follow is a `last_logged_message` tracking column if the founder wants a live conversation feed in HubSpot.
