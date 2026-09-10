# Task 1.1 / 1.2 — crm_leads.source migration

**Change:** b2c-social-lead-capture
**Task:** 1.1 Create migration `00XX_crm_leads_source.sql`; 1.2 Do not apply yet.

## What was done

- Checked `apps/backend/migrations/` for the next available number: highest existing was
  `0051_crm_leads_cadence.sql`, so this migration is `0052`.
- Created `apps/backend/migrations/0052_crm_leads_source.sql`:
  - `ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS source text;` — nullable, no default,
    no backfill of existing rows.
  - `COMMENT ON COLUMN` documenting intent (mirrors style of `0049_crm_leads_lead_type.sql`,
    the `whatsapp-b2b-lead-bridge` reference migration named in the task).
  - Trailing `SELECT '✅ 0052 crm_leads_source complete' AS status;` sentinel, same pattern as
    other migrations in this directory.
- **Not applied to Supabase** — per task 1.2, migrations require explicit founder confirmation.
- Marked `[x]` for tasks 1.1 and 1.2 in
  `openspec/changes/b2c-social-lead-capture/tasks.md`.

## Files touched

- `apps/backend/migrations/0052_crm_leads_source.sql` (new)
- `openspec/changes/b2c-social-lead-capture/tasks.md` (checkboxes 1.1, 1.2)

## Verification

No test suite applies to a raw SQL migration file that isn't applied yet. Verified by reading
the file back and confirming the numbering doesn't collide with any existing migration
(`ls apps/backend/migrations` sorted, highest was `0051`).

## Scope note

Did not touch any other task (2.x–6.x, Stage 11) or any other file. Awaiting reviewer before
marking this task `done` in any tracker.
