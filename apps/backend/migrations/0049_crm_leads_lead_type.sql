-- Migration 0049: crm_leads.lead_type column
-- Date: 2026-09-09
-- Adds a nullable classification column distinguishing B2C Renta Natural leads
-- from B2B business-shaped leads (see openspec/changes/whatsapp-b2b-lead-bridge/
-- design.md). Deliberately NULL-default and no backfill: every currently
-- provisioned row keeps its existing (absent) value, and only a future
-- `business_interest` classification in taty_lead_router.py writes a value.

ALTER TABLE crm_leads
  ADD COLUMN IF NOT EXISTS lead_type text;

COMMENT ON COLUMN crm_leads.lead_type IS 'Lead classification signal (e.g. business_interest) written by taty_lead_router.route_lead_message(); NULL for leads never classified as a business signal, including all pre-existing rows.';

SELECT '✅ 0049 crm_leads_lead_type complete' AS status;
