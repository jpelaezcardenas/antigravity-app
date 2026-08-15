-- Migration 0041: HubSpot sync-state columns on b2b_clients
-- Date: 2026-08-15
-- Adds nullable tracking columns for the one-way Supabase -> HubSpot Company
-- sync (read-only registry, no pipeline/deal usage). No backfill: null means
-- "never synced". See openspec/changes/hubspot-sync-renta-natural/design.md.

ALTER TABLE b2b_clients
  ADD COLUMN IF NOT EXISTS hubspot_company_id text,
  ADD COLUMN IF NOT EXISTS last_synced_at timestamptz;

COMMENT ON COLUMN b2b_clients.hubspot_company_id IS 'HubSpot Company ID for this B2B client, null until first synced by the Hermes-local poller. Never a Deal.';
COMMENT ON COLUMN b2b_clients.last_synced_at IS 'Timestamp of the last successful HubSpot sync for this client, null if never synced.';

SELECT '✅ 0041 hubspot_sync_b2b_clients complete' AS status;
