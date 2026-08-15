-- Migration 0040: HubSpot sync-state columns on crm_leads
-- Date: 2026-08-15
-- Adds nullable tracking columns for the one-way Supabase -> HubSpot lead sync
-- (Renta Natural funnel, single free-tier pipeline). No backfill: null means
-- "never synced". See openspec/changes/hubspot-sync-renta-natural/design.md.

ALTER TABLE crm_leads
  ADD COLUMN IF NOT EXISTS hubspot_contact_id text,
  ADD COLUMN IF NOT EXISTS hubspot_deal_id text,
  ADD COLUMN IF NOT EXISTS last_synced_at timestamptz;

COMMENT ON COLUMN crm_leads.hubspot_contact_id IS 'HubSpot Contact ID for this lead, null until first synced by the Hermes-local poller.';
COMMENT ON COLUMN crm_leads.hubspot_deal_id IS 'HubSpot Deal ID (single default pipeline) for this lead, null until first synced.';
COMMENT ON COLUMN crm_leads.last_synced_at IS 'Timestamp of the last successful HubSpot sync for this lead, null if never synced.';

SELECT '✅ 0040 hubspot_sync_crm_leads complete' AS status;
