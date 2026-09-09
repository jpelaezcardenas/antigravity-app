# Implementer report — whatsapp-b2b-lead-bridge, Group 2 (crm_leads.lead_type column)

**Task:** 2.1 / 2.2 only. No other files touched.

## File created

`apps/backend/migrations/0049_crm_leads_lead_type.sql`

### Numbering rationale

Listed `apps/backend/migrations/` and found the highest existing file was
`0048_uvt_values_and_service_band.sql`. Chose `0049` as the next sequential
number, following the same `00XX_description.sql` naming convention as recent
migrations (`0043_add_plan_tier.sql`, `0047_radar_module_opens.sql`, etc.).

### Content

```sql
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
```

Design choices matching the task spec exactly:
- Column is `text`, nullable — no `NOT NULL`, no `DEFAULT` other than the
  implicit `NULL`.
- `ADD COLUMN IF NOT EXISTS` — idempotent, matches repo style (see 0043, 0047,
  0048).
- No backfill statement of any kind — existing rows are untouched, they simply
  gain a `NULL` value for the new column as a schema-level side effect of
  `ALTER TABLE ADD COLUMN` (unavoidable and expected — not a data write).
- Style (header comment block with migration number/date/rationale, trailing
  `SELECT '✅ ... complete'` status line) follows the most recent migrations in
  the repo (`0043_add_plan_tier.sql` read as reference).

## Confirmation: migration NOT applied

Per task 2.2 and repo-wide policy (every migration requires explicit founder
approval before being run against Supabase — see `ARCHITECTURE.md` Decisión
#23's note on migration `0048` being written and tested at file level but not
applied until approved), **no database command of any kind was executed**
against Supabase in this session. Only a `Write` tool call created the SQL
file on disk; no `psql`, no Supabase CLI, no migration runner was invoked.
The file exists solely as a reviewable artifact awaiting founder sign-off
(tracked as Stage 11 task 11.1 in `tasks.md`, out of scope for this task).

## Scope discipline

Did not touch:
- `apps/backend/services/taty_lead_router.py` (Group 1, already approved /
  Group 3, later task)
- `apps/backend/services/crm_service.py`
- `apps/chatwoot-bridge/main.py`
- `openspec/changes/whatsapp-b2b-lead-bridge/tasks.md` (not edited, per
  instructions)

## Test output

No test run applicable — this task is a pure schema-file creation with no
associated application code change. `apps/backend` test suite untouched by
this change (no import of the new column anywhere yet — that wiring is Group
3, a separate task).
