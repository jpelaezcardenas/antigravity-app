# Step 6 Report - Unit Tests and Database Verification

- Date: 2026-08-18
- Change: shadow-gl-data-integrity-flag
- Agent: Claude Sonnet 5

## Commands Executed

- `RUN_SHADOW_GL=1 python -m pytest tests/test_shadow_gl_ingestion.py::TestIngestDianXmlPersistence::test_ingest_without_flag_defaults_unverified tests/test_shadow_gl_ingestion.py::TestIngestDianXmlPersistence::test_ingest_with_flag_marks_verified tests/test_shadow_gl_siigo_csv.py::TestIngestSiigoCSVPersistence::test_ingest_without_flag_defaults_unverified tests/test_shadow_gl_siigo_csv.py::TestIngestSiigoCSVPersistence::test_ingest_with_flag_marks_verified -v` (targeted new tests)
- `RUN_SHADOW_GL=1 python -m pytest tests/test_shadow_gl_ingestion.py tests/test_shadow_gl_siigo_csv.py tests/test_shadow_gl_integration.py -v` (broader regression pass)

## Unit Test Results

- Targeted new tests (the 4 tests added for this change): **4 passed, 0 failed**.
- Broader pass: **13 passed, 19 failed** — all 19 failures confirmed **pre-existing and unrelated**
  to this change (reproduced identically before any code in this change was written): the Siigo CSV
  parser (`parse_siigo_csv`) was rewritten at some point to require Spanish column headers
  (`fecha`, `referencia externa`, `código de cuenta`, `descripción`), but the shared test fixture
  file and several test assertions still use the old English headers/shape. Flagged as a separate
  follow-up task (`task_718da7b8`, not this change's scope) rather than fixed here — fixing it
  would mean rewriting the parser's test contract, well beyond an additive data-integrity flag.
- Runtime: ~16s for the broader pass.
- No flaky behavior observed — failures are deterministic (same error every run).

## Database State Verification

### Pre-test baseline (before this change's migration)
- `erp_journal_entries`: 73 rows
- `erp_journal_lines`: 136 rows
- `dian_xml_documents`: 4 rows
- `approval_queue`: 20 rows

### Post-migration, pre-regression-suite
- `erp_journal_entries`: 73 rows, all `is_verified_real=false` (backfilled correctly)
- `dian_xml_documents`: 4 rows, all `is_verified_real=false` (backfilled correctly)

### Post broader regression suite (`test_shadow_gl_integration.py` included)
- `erp_journal_entries`: **29 rows** (all `source='manual'`, the load-bearing per-tenant SYNTH demo
  seed — migration 0028/0035 — confirmed unaffected)
- `erp_journal_lines`: 58 rows
- `dian_xml_documents`: **0 rows**
- `approval_queue`: 27 rows

### Incident and disclosure

Running `test_shadow_gl_integration.py`'s `TestShadowGLIntegrationWithDB` class (part of the
"broader regression suite" pass above) triggered a **pre-existing** autouse cleanup fixture bug:
it unconditionally deleted every `erp_journal_entries`/`erp_journal_lines`/`dian_xml_documents` row
for the Cliente Cero tenant after each test — including rows the test didn't create — and pytest
runs `yield`-based teardown even when the test body itself fails (both tests in that class failed
for the unrelated pre-existing CSV-header reason above). Net effect: 44 `erp_journal_entries` rows
and 3 `dian_xml_documents` rows — all previously-documented synthetic/fixture data, none of it
load-bearing for any real client or dashboard — were deleted.

Founder was informed immediately (mid-task) with full detail and explicitly chose to accept the
loss rather than attempt a partial restore (a metadata-only restore of the 44 entries without their
corresponding `erp_journal_lines` — never snapshotted — would have left dangling journal entries
with no debit/credit detail, which is worse than absent).

**Fixed as part of this change** (both in `test_shadow_gl_siigo_csv.py::TestIngestSiigoCSVPersistence`
and `test_shadow_gl_integration.py::TestShadowGLIntegrationWithDB`): cleanup fixtures now snapshot
row ids *before* the test runs and delete only ids that are new *after* — they can no longer delete
data they didn't create, regardless of test outcome.

**State restored:** No — see above, the founder chose not to restore (synthetic data, no product
dependency, restore would have been incomplete/misleading). Documented in
`docs/supabase-mcp-admin.md` §3.

**Load-bearing data confirmed intact throughout:** the 29 `SYNTH-*-SALE`/`SYNTH-*-EXPENSE` rows
(migration 0028, kept fresh by the `reseed-synth-shadow-gl` pg_cron job) that the live per-tenant
`GET /api/v1/financials` endpoint depends on for the ~10 real B2B clients were never touched at any
point — verified by direct `source` breakdown query before and after.

## Outcome

- Step 6 status: **PASS** (for this change's own tests and code — 4/4 new tests green, no
  regression introduced by this change's code)
- Blocking issues: none for this change. Separate, disclosed issues: (1) 19 pre-existing test
  failures from stale CSV fixture format (`task_718da7b8`, out of scope); (2) an incident where a
  different pre-existing test bug deleted 47 rows of already-documented synthetic data during
  verification — disclosed to the founder in-session, accepted, and the root-cause fixture bug is
  now fixed in both affected classes so it cannot recur.
