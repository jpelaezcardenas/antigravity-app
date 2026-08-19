# Deployment report — fix-siigo-csv-test-fixture-drift

**Date:** 2026-08-18

## Nature of this change

Test-only: one fixture CSV, two test files (`tests/test_shadow_gl_siigo_csv.py`,
`tests/test_shadow_gl_integration.py`). No production code, no migration, no API/schema change.
There is nothing for Railway or Vercel to build or serve differently — Stage 11 for this change
is "land on `main`, confirm the suite is green," not a live-URL verification.

## Verification results

- `RUN_SHADOW_GL=1 python -m pytest tests/test_shadow_gl_siigo_csv.py
  tests/test_shadow_gl_integration.py -v` (from `apps/backend`): **24 passed**, 0 failed. The
  originally-reported 19 failures are resolved.
- Full `test_shadow_gl_*.py` + `test_phase6_e2e_simulation.py` sweep: 72 passed, 2 skipped, 16
  failed, 9 errors — all remaining failures/errors are pre-existing and unrelated (confirmed by
  file/assertion content: broken cwd-relative `subprocess` calls in `test_shadow_gl_stage8_e2e.py`,
  a reference to a renamed/deleted `tests/test_shadow_gl_siigo_parser.py`, and DB-schema/migration
  checks in `test_shadow_gl_schema.py`/`test_shadow_gl_stage1_migration.py` unrelated to Siigo CSV
  parsing).
- `test_shadow_gl_stage4_uploader.py`, `test_shadow_gl_stage5_error_handling.py`,
  `test_shadow_gl_stage8_e2e.py`, `test_phase6_e2e_simulation.py` run in isolation: **10 failed, 20
  passed, 2 skipped** — identical to the pre-change baseline captured before any file was touched.
  Confirmed unaffected by this change, as the design predicted.

## Two bugs found and fixed beyond the original 19

While verifying, found `test_ingest_creates_approval_queue_on_imbalance` (inline CSV still using
old English headers) and an idempotency assertion bug in both
`test_ingest_idempotent_on_external_reference_id` and `test_csv_idempotency_no_duplicates`
(asserted `row_count` stays the same on a no-op re-upload, but `ingest_siigo_csv` correctly
reports `0` newly-inserted rows on a true no-op). Both were part of the original 19 failing tests
and are now fixed — see `tasks.md` §3.1 for detail.

## Deploy status

Committed and pushed to `main` on founder confirmation: commit `3d60bb6`
(`dd23c86..3d60bb6`), pushed to `origin/main` at
https://github.com/jpelaezcardenas/antigravity-app.

## Stage 11 checklist

- [x] Suite green locally (see above)
- [x] Committed + pushed to `main` (`3d60bb6`)
- [x] N/A — no Railway/Vercel build to verify (test-only change)
- [x] Archive the change
