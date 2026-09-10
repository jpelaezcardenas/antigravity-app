-- Migration 0051: crm_leads follow-up cadence columns
-- Date: 2026-09-09
-- Part of taty-voice-outbound-calls, capability taty-followup-cadence (text-only, no telephony,
-- ships and deploys independently of the voice pieces of that change).
--
-- NOT APPLIED to the live database as part of this session. Applying migrations requires
-- explicit founder approval (CLAUDE.md / ARCHITECTURE.md Decision #23 precedent). Written and
-- unit-tested at the file level only; the endpoint/poller degrade in a controlled way
-- (send-touch returns sent=False, reason="cadence_columns_missing"-shaped Supabase error surfaces
-- as a 500 from the underlying client) until this is applied.
--
-- last_inbound_at: an explicit column rather than reusing crm_leads.updated_at, because
-- updated_at is bumped by ANY write to the row (advance_lead, update_tax_profile, lead_type
-- stamping, etc. — see update_crm_b2b_updated_at() trigger), not only by a genuine inbound
-- WhatsApp message. Reasoning about that trigger's side effects to treat updated_at as an inbound
-- signal would be fragile; a column that only route_lead_message ever sets is not.
--
-- cadence_day: NULL means "no automated touch sent yet". Set to 1/2/4/7/14 as each scripted
-- touch is sent (services/taty_lead_router.py / presentation/cadence_endpoints.py), and reset
-- back to NULL the instant the lead sends any inbound message (route_lead_message), per
-- spec.md's "a lead who responds exits the automated cadence" requirement.
--
-- cadence_completed_at: set once the day-14 touch is sent. A day 14 lead that never becomes NULL
-- again (i.e. never replies) must never receive a further automated touch — this column, plus
-- there being no schedule entry past day 14, is the belt-and-suspenders guard for that.

ALTER TABLE crm_leads
  ADD COLUMN IF NOT EXISTS last_inbound_at timestamptz,
  ADD COLUMN IF NOT EXISTS cadence_day integer,
  ADD COLUMN IF NOT EXISTS cadence_completed_at timestamptz;

COMMENT ON COLUMN crm_leads.last_inbound_at IS 'Timestamp of the lead''s most recent genuine inbound WhatsApp message, set only by services.taty_lead_router.route_lead_message — never by any other crm_leads write. Anchor for the taty-followup-cadence threshold check.';
COMMENT ON COLUMN crm_leads.cadence_day IS 'The last automated follow-up day (1/2/4/7/14) sent to this lead by taty-followup-cadence, or NULL if none has been sent yet or the lead has replied since (which resets this to NULL). NOT a general-purpose lead status field.';
COMMENT ON COLUMN crm_leads.cadence_completed_at IS 'Set once the day-14 scripted touch is sent, so no schedule gap can ever cause a further automated touch to this lead.';

SELECT '✅ 0051 crm_leads_cadence complete' AS status;
