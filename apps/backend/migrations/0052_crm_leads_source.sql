-- Migration 0052: crm_leads.source column
-- Date: 2026-09-09
-- Adds a nullable attribution column recording where a B2C social lead capture
-- originated (see openspec/changes/b2c-social-lead-capture/design.md). Same
-- additive pattern as 0049 (lead_type): NULL default, no backfill — every
-- currently provisioned row keeps its existing (absent) value, and only the
-- new public capture endpoint stamps a value going forward.

ALTER TABLE crm_leads
  ADD COLUMN IF NOT EXISTS source text;

COMMENT ON COLUMN crm_leads.source IS 'Attribution signal for where a lead capture originated (e.g. a social landing page query string), written by the public social-capture endpoint; NULL for leads never captured through that path, including all pre-existing rows.';

SELECT '✅ 0052 crm_leads_source complete' AS status;
