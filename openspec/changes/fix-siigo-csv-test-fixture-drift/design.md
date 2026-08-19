## Context

`parse_siigo_csv()` (`apps/backend/services/shadow_gl_service.py:127`) was rewritten at some
point to require Spanish Siigo export headers and to return a flat list of row dicts (one per
CSV line). Grouping rows into transactions by `referencia_externa` now happens inside
`ingest_siigo_csv()` (same file, line ~445), not in the parser. The test fixture and
`TestParseSiigoCSV` were never updated to match, so 19 tests fail today on a clean checkout —
confirmed by running `RUN_SHADOW_GL=1 python -m pytest tests/test_shadow_gl_siigo_csv.py
tests/test_shadow_gl_integration.py -v` (19 failed, 4 passed). This is pure test/fixture drift:
the parser and ingest functions are correct and already proven by the newer
`test_ingest_without_flag_defaults_unverified` / `test_ingest_with_flag_marks_verified` tests
(added by `shadow-gl-data-integrity-flag`), which already use inline CSVs with the current
Spanish headers.

## Goals / Non-Goals

**Goals:**
- Make the fixture CSV and `TestParseSiigoCSV` assertions match `parse_siigo_csv`'s actual,
  current contract (Spanish headers in, flat rows out).
- Preserve test coverage for "lines are grouped by transaction" and "batch is balanced" by moving
  those assertions to where that behavior now actually lives (`ingest_siigo_csv`'s internal
  grouping, and `parse_siigo_csv`'s own batch-balance check which already exists at
  `shadow_gl_service.py:215-221`).
- Fix `test_shadow_gl_integration.py`'s four tests that consume the same stale fixture.
- Document the ingestion contract as a spec, since none exists today for Shadow GL CSV ingestion.

**Non-Goals:**
- No change to `parse_siigo_csv` / `ingest_siigo_csv` production behavior — both are correct.
- No changes to `test_shadow_gl_stage4_uploader.py`, `test_shadow_gl_stage5_error_handling.py`,
  `test_shadow_gl_stage8_e2e.py`, `test_phase6_e2e_simulation.py` — verified they already use
  inline Spanish-header CSVs and don't reference the stale fixture. Their 10 pre-existing failures
  (broken cwd-relative `subprocess` calls invoking `apps/backend/tests/...` paths, and a reference
  to `tests/test_shadow_gl_siigo_parser.py` which doesn't exist / was renamed at some point) are a
  distinct, unrelated defect — out of scope here, left for a separate change.
- No new production capability — `shadow-gl-siigo-csv-ingestion` spec documents existing,
  already-shipped behavior for the first time; it does not change it.

## Decisions

**Decision: rewrite `TestParseSiigoCSV` to assert the flat-row shape, and move the
grouping/balance assertions down to `ingest_siigo_csv`, rather than trying to make the parser
group again.**

Two options were on the table (per the task's framing):
- (a) Update the fixture + rewrite `TestParseSiigoCSV` assertions to match `parse_siigo_csv`'s
  actual flat-row return shape.
- (b) Treat `ingest_siigo_csv`'s internal grouping-by-`referencia_externa` as the thing that
  should be tested for "grouped by transaction," since grouping moved there.

Chose **both, split by layer**: (a) for what's genuinely a parser-level concern (header mapping,
date validation, minor-units conversion, per-row shape, missing-column/negative-amount rejection,
overall batch balance — all of which `parse_siigo_csv` still does directly), and (b) for the one
assertion (`test_groups_lines_by_transaction`) that tested behavior the parser no longer performs.
Testing grouping against the parser would mean asserting behavior that doesn't exist there
anymore; testing it only at `ingest_siigo_csv` (which requires `RUN_SHADOW_GL=1` + Supabase) would
leave the parser-level suite silently weaker. Splitting keeps each test asserting behavior that
actually lives at that layer.

**Decision: keep the same fixture file (update in place), not add a second one.**

The fixture's transaction data (dates, memos, account codes) doesn't need to change — only its
header row and monetary values need to align with the parser's Spanish-header expectations. A
second fixture would just be more drift risk. Alternatives considered: generating the fixture
CSV inline in the test file (rejected — fixture-as-file matches the pattern the other 4 stage
test files use for their own inline CSVs, and this file is also referenced by
`test_shadow_gl_integration.py`, so a shared file avoids duplicating the same data twice).

**Decision: add `shadow-gl-siigo-csv-ingestion` as a new capability spec, not fold into
`shadow-gl-data-integrity`.**

`shadow-gl-data-integrity`'s spec is scoped narrowly to the `is_verified_real` flag (see
`openspec/changes/shadow-gl-data-integrity-flag/specs/shadow-gl-data-integrity/spec.md`) — mixing
in the CSV parsing/grouping contract would conflate two different concerns under one capability
name. A dedicated spec also gives future sessions a single place to check before touching the
parser or its tests again.

## Risks / Trade-offs

[Risk: fixing the fixture without re-verifying the actual parser behavior against real Siigo
export data] → Mitigation: the corrected fixture's header row and cell values are derived
directly from `parse_siigo_csv`'s own required-column set and `_to_minor_units` logic (already
verified against the two new inline-CSV tests added by `shadow-gl-data-integrity-flag`), not
guessed; amounts are re-verified by running the updated `test_converts_amounts_to_minor_units`
assertion against the corrected fixture before considering the task done.

[Risk: `test_shadow_gl_integration.py`'s DB-backed tests could still fail for reasons unrelated to
the fixture (e.g. `RUN_SHADOW_GL=1` DB state, network)] → Mitigation: task list requires running
the full targeted suite with `RUN_SHADOW_GL=1` and confirming the specific 19 previously-failing
tests now pass, not just that new code doesn't raise.
