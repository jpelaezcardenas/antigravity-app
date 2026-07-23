-- Migration 0035: Rolling reseed of synthetic Shadow GL "yesterday" rows
-- (renumbered from 0033 on 2026-07-23 during merge reconciliation — 0033/0034 were
-- claimed by approval-queue-tenant-scoping and centinela-tenant-scoped-alerts, which
-- landed on main while this change was in progress on an isolated worktree)
-- Date: 2026-07-23
-- The synthetic per-client Shadow GL seed (migration 0028) dated its `SYNTH-*-SALE` and
-- `SYNTH-*-EXPENSE` rows to `CURRENT_DATE - 1` at seed time (2026-07-20) and that date is now
-- static, so `ventas_ayer`/`gastos_ayer` on GET /api/v1/financials go stale (and eventually
-- read $0, since only literal "yesterday" is aggregated) as real days pass.
--
-- Fix (design.md D4, spec `pulso-financials-api` "Synthetic Shadow GL yesterday rows stay
-- fresh via rolling reseed"): (1) a one-shot UPDATE below re-dates the existing rows to
-- yesterday right now, and (2) a daily pg_cron job re-runs the identical UPDATE every day at
-- 05:10 UTC (~00:10 Bogotá) so the rows never go stale again.
--
-- Scope is identical to migration 0028's tagging: `external_reference_id` ending in `-SALE` or
-- `-EXPENSE`, prefixed `SYNTH-`, AND `memo` prefixed `SYNTH:per-tenant-client-access`.
-- `SYNTH-*-OPEN` rows (opening balance) are intentionally excluded — re-dating them would
-- corrupt the cumulative Caja Real balance.
--
-- Idempotent: the one-shot UPDATE is safe to re-run (it always just re-dates matching rows to
-- "yesterday", a no-op if already correct); the cron job registration unschedules any prior job
-- of the same name before scheduling, so re-running this migration never creates duplicates.
-- Requires the `pg_cron` extension, already installed on this project (verified via Supabase
-- MCP `list_extensions`, v1.6.4) — no `create extension` step needed.

-- 1. One-shot re-date: bring the existing synthetic rows current the moment this migration runs.
UPDATE erp_journal_entries
SET entry_date = CURRENT_DATE - INTERVAL '1 day'
WHERE external_reference_id LIKE 'SYNTH-%'
  AND (external_reference_id LIKE '%-SALE' OR external_reference_id LIKE '%-EXPENSE')
  AND memo LIKE 'SYNTH:per-tenant-client-access%';

-- 2. Daily pg_cron job: re-run the identical re-date every day so the rows never go stale again.
--    Idempotent registration — unschedule any existing job of this name first.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'reseed-synth-shadow-gl') THEN
    PERFORM cron.unschedule('reseed-synth-shadow-gl');
  END IF;
END $$;

SELECT cron.schedule(
  'reseed-synth-shadow-gl',
  '10 5 * * *',
  $cron$
  UPDATE erp_journal_entries
  SET entry_date = CURRENT_DATE - INTERVAL '1 day'
  WHERE external_reference_id LIKE 'SYNTH-%'
    AND (external_reference_id LIKE '%-SALE' OR external_reference_id LIKE '%-EXPENSE')
    AND memo LIKE 'SYNTH:per-tenant-client-access%';
  $cron$
);

SELECT '✅ 0035 rolling_reseed_synthetic_shadow_gl complete' AS status;
