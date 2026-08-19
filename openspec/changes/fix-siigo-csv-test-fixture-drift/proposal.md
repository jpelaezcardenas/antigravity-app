## Why

`services/shadow_gl_service.py::parse_siigo_csv()` was rewritten to require Spanish CSV headers
(`fecha`, `referencia externa`, `código de cuenta`, `descripción`, `débito`, `crédito`) and to
return a flat list of row dicts, with grouping-by-transaction moved into `ingest_siigo_csv()`.
The test fixture (`tests/fixtures/contexia_siigo_journal_2026-06-18-to-2026-06-24.csv`) and
`TestParseSiigoCSV` in `tests/test_shadow_gl_siigo_csv.py` were never updated to match — they
still use old English headers and assert the old grouped `{"lines": [...]}` shape. This makes
19 tests fail on a clean checkout, unrelated to any real code change
(`RUN_SHADOW_GL=1 python -m pytest tests/test_shadow_gl_siigo_csv.py tests/test_shadow_gl_integration.py -v`
→ 19 failed, 4 passed, confirmed 2026-08-18). The currently-active `shadow-gl-data-integrity-flag`
change already ran into this drift and explicitly deferred it as "tracked separately, out of
scope" — this proposal is that follow-up, and also fills a real gap: no spec today documents the
Siigo CSV ingestion contract at all, so nothing keeps parser/tests/fixture in sync going forward.

## What Changes

- Update `tests/fixtures/contexia_siigo_journal_2026-06-18-to-2026-06-24.csv` to the current
  Spanish header format the parser actually requires.
- Rewrite `TestParseSiigoCSV` in `tests/test_shadow_gl_siigo_csv.py` to assert `parse_siigo_csv`'s
  real flat-row shape (`fecha`/`referencia_externa`/`codigo_cuenta`/`descripcion`/`debito_cents`/`credito_cents`),
  instead of the old grouped `{"lines": [...]}` shape.
- Move the "lines are grouped by transaction" assertion to the `ingest_siigo_csv` level (where
  grouping actually happens today), rather than testing it at the parser level where it no
  longer applies.
- Update `tests/test_shadow_gl_integration.py` (`test_siigo_csv_parses`, `test_xml_and_csv_both_valid`,
  `test_ingest_xml_and_csv_same_day`, `test_csv_idempotency_no_duplicates`) to use the corrected
  fixture/shape.
- No production code changes — `parse_siigo_csv` / `ingest_siigo_csv` behavior is already correct
  and already exercised successfully by the newer `test_ingest_without_flag_defaults_unverified`
  / `test_ingest_with_flag_marks_verified` tests added by `shadow-gl-data-integrity-flag`.

**Out of scope (checked, confirmed unaffected):** `test_shadow_gl_stage4_uploader.py`,
`test_shadow_gl_stage5_error_handling.py`, `test_shadow_gl_stage8_e2e.py`,
`test_phase6_e2e_simulation.py` already define their own inline CSVs with correct Spanish headers
and don't touch the stale fixture. They have 10 pre-existing, unrelated failures (broken
cwd-relative `subprocess` calls, and a reference to a renamed/deleted
`tests/test_shadow_gl_siigo_parser.py`) — a separate defect, not caused by and not fixed here.

## Capabilities

### New Capabilities
- `shadow-gl-siigo-csv-ingestion`: documents the Siigo CSV parsing/ingestion contract (Spanish
  headers, flat-row parser output, grouping-by-`referencia_externa` at the ingest layer) so the
  fixture and tests have a spec to stay in sync against going forward.

### Modified Capabilities
(none — no existing spec covers Shadow GL ingestion; `shadow-gl-data-integrity-flag`'s proposal
notes this same gap)

## Impact

- **Tests only**: `apps/backend/tests/fixtures/contexia_siigo_journal_2026-06-18-to-2026-06-24.csv`,
  `apps/backend/tests/test_shadow_gl_siigo_csv.py`, `apps/backend/tests/test_shadow_gl_integration.py`.
- **No production code, no migration, no deploy** — Stage 11 is N/A beyond committing to `main`
  and confirming the suite is green in CI/local; there is nothing to observe in Railway/Vercel.
- **Docs**: new `openspec/specs/shadow-gl-siigo-csv-ingestion/spec.md`.
