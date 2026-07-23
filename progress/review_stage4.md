# Review — task stage4 (pwa-tenant-aware-screens)

**Verdict:** APPROVED

## Scope reviewed

`apps/backend/migrations/0033_rolling_reseed_synthetic_shadow_gl.sql` (commit `fa61548`,
tasks.md 4.2/4.3), against `openspec/changes/pwa-tenant-aware-screens/design.md` §D4, the
`pulso-financials-api` spec's "Synthetic Shadow GL yesterday rows stay fresh via rolling
reseed" requirement, and migrations 0028/0030 as the tagging-convention source of truth.

## Point-by-point

1. **WHERE clause identity (one-shot vs cron).** Lines 27–29 and lines 46–48 of the migration
   are byte-for-byte identical (`external_reference_id LIKE 'SYNTH-%' AND (... LIKE '%-SALE' OR
   ... LIKE '%-EXPENSE') AND memo LIKE 'SYNTH:per-tenant-client-access%'`). No drift.

2. **`-OPEN` exclusion is structural.** `LIKE '%-SALE'` and `LIKE '%-EXPENSE'` are anchored to
   the literal string end; a value ending in `-OPEN` cannot satisfy either pattern under any
   string content. Matches 0028's suffix convention (`-OPEN`/`-SALE`/`-EXPENSE`) exactly — 0028
   lines 61, 73, 86, 119, 129 confirm those are the only three suffixes ever written.

3. **Cron registration idempotency.** Lines 33–38: `DO $$ IF EXISTS (... cron.job WHERE jobname
   = 'reseed-synth-shadow-gl') THEN cron.unschedule(...) END IF $$`, followed unconditionally by
   `cron.schedule(...)`. Re-running the file: existing job (if any) is unscheduled first, then a
   fresh job is scheduled — no duplicate `cron.job` row, no error on either first or Nth apply.

4. **Cron time arithmetic.** `10 5 * * *` = 05:10 UTC daily. Bogotá is UTC-5 with no DST →
   05:10 − 5:00 = 00:10 Bogotá. Matches the migration's own comment and design.md's intent.

5. **Dry-run row-count arithmetic — cross-checked against 0028/0030 SQL, not just the
   implementer's prose.** 0028's client loop seeds SALE only `IF venta_ayer_cents > 0` and
   EXPENSE only `IF gasto_ayer_cents > 0`; all 10 VALUES rows (including Nia Cano) have both
   > 0, so the loop alone produces 10×2 = 20 SALE+EXPENSE rows. CÓDIGO 520 is seeded separately
   (0028 lines 97–136) with only an EXPENSE row (no SALE branch present at all) → +1 = 21 total
   SALE+EXPENSE rows pre-0030. 0030 deletes *all* `erp_journal_entries`/`lines` for Nia Cano's
   tenant (line 24–25, unscoped by suffix) — that's 3 rows (OPEN+SALE+EXPENSE), of which 2
   (SALE+EXPENSE) are in migration 0033's scope. 21 − 2 = 19. Matches the implementer's dry-run
   count (9 SALE + 10 EXPENSE = 19) exactly. The implementer's report (impl_stage4.md lines
   58–63) reaches the same number but via a messier, self-correcting narrative
   ("10*2 - 2 - 1 = 17... actually count check:... = 19") — the final number is right and my
   independent derivation from 0028/0030's actual SQL confirms it; the report's arithmetic
   trail is sloppy but not misleading since it flags its own correction inline. Not a blocker.

6. **Read-only dry-run credential check.** `apps/backend/.env` `SUPABASE_KEY` and
   `js/supabase-client.js`'s `SUPABASE_ANON_KEY` are byte-identical (both start
   `eyJhbGciOiJIUzI1NiIsInR5cCI...`, role claim `"anon"` per the JWT payload segment). `git log
   --follow -- js/supabase-client.js` shows it's a tracked, pre-existing file (last touched by
   an unrelated commit `6825d3f`), not something the implementer newly created to smuggle a
   credential in. A PostgREST `GET` against `erp_journal_entries` with an anon key, gated by
   RLS, is genuinely read-only — there is no PostgREST write without a POST/PATCH/DELETE verb,
   none of which appear in the report or diff. No write endpoint was called.

7. **Nothing applied to production.** `git show --stat fa61548` touches exactly one file (the
   migration). `git status` shows only untracked `progress/*.md` files, no staged/modified
   tracked files. `tasks.md` 13.2 ("Apply migration `0033_*.sql` ... via Supabase MCP
   `apply_migration`") is still unchecked `[ ]`, consistent with the implementer's claim that
   application is deferred to Stage 13/deploy. I have no Supabase MCP tool in this session
   either, so I can't independently query `cron.job`/`erp_journal_entries` state to double-
   confirm nothing was applied — this rests on the artifact trail being internally consistent,
   which it is (single-file commit, no deploy-stage tasks checked, explicit "Not run" disclosure
   in the report).

8. **SQL style consistency.** Header comment block (migration number, date, one-line
   description, followed by a "why" paragraph) matches 0028/0030/0031. Trailing `SELECT '✅
   00XX_name complete' AS status;` sentinel matches all three neighbors exactly. No neighboring
   migration wraps in explicit `BEGIN/COMMIT` either (Supabase migration runner handles
   transaction boundaries), so 0033's omission is consistent, not a deviation.

## Minor non-blocking note

- The implementer flagged their own tooling deviation (PostgREST read instead of the Supabase
  MCP `execute_sql` tool specified in the task) transparently, with a stated reason (tool not
  exposed in their session) and confirmed the substitution didn't touch production or introduce
  a new secret. Accepted — the verification goal was met and the deviation is fully disclosed,
  not hidden.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md, scoped to this task)

- Docs-sync: N/A for this task — no container/dependency change requiring an `ARCHITECTURE.md`
  update; design.md D4 already documents this exact behavior and the migration matches it
  verbatim.
- No stubs/mocks fabricated: confirmed — real SQL against the real seeded rows.
- Type-checking / build gates: N/A (SQL migration, not app code).
- Not archived/deployed prematurely: confirmed — Stage 13 (apply + deploy) remains unchecked.

## Required changes

None. Task 4.2/4.3 is complete and correct as implemented. Reviewer defers to the implementer's
own note that tasks.md checkboxes for 4.2/4.3 should be marked `[x]` by the leader/reviewer per
protocol — recommend doing so now that this review passes.
