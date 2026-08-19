## 1. Fixture: Update to Current Spanish Header Format

- [x] 1.1 Rewrite `tests/fixtures/contexia_siigo_journal_2026-06-18-to-2026-06-24.csv` with headers
      `fecha,referencia externa,código de cuenta,descripción,débito,crédito`, dropping
      `account_name`/`currency_code` (not read by `parse_siigo_csv`), preserving the same
      transaction dates/amounts/references so existing balance/grouping properties still hold.
- [x] 1.2 Confirm the file loads and `parse_siigo_csv` doesn't raise on it (quick manual check
      before touching the test assertions).

## 2. `TestParseSiigoCSV`: Rewrite Assertions to Match the Flat-Row Contract

- [x] 2.1 `test_parses_valid_siigo_csv`: asserts flat rows (`fecha`, `referencia_externa`,
      `codigo_cuenta`, `descripcion`, `debito_cents`, `credito_cents` keys), not `lines`.
- [x] 2.2 `test_parses_headers_correctly`: asserts `parsed[0]["referencia_externa"] ==
      "DOC-20260618-001"`, `parsed[0]["fecha"] == "2026-06-18"`, and that `debito_cents`/
      `credito_cents` are ints.
- [x] 2.3 `test_converts_amounts_to_minor_units`: iterates flat rows directly, asserts the first
      `debito_cents > 0` equals `85000000`.
- [x] 2.4 Kept a lightweight parser-level `test_groups_lines_by_transaction` (flat rows sharing a
      `referencia_externa` are the right count) and added a new
      `test_ingest_groups_lines_by_referencia_externa` in `TestIngestSiigoCSVPersistence` that
      asserts `ingest_siigo_csv` creates exactly one `erp_journal_entries` row with 2
      `erp_journal_lines` rows for a shared reference — per the new `shadow-gl-siigo-csv-ingestion`
      spec's grouping requirement. Gated by the class's existing `RUN_SHADOW_GL=1` marker.
- [x] 2.5 `test_detects_balanced_transaction` / `test_detects_all_entries_balanced`: rewritten to
      sum `debito_cents`/`credito_cents` per `referencia_externa` group over the flat row list.
- [x] 2.6 `test_rejects_missing_required_column`: rewritten to drop `descripción,` (a required
      column — `débito`/`crédito` are optional, so dropping those wouldn't trigger the check).
- [x] 2.7 `test_rejects_empty_csv`: updated to the Spanish header-only string.
- [x] 2.8 `test_rejects_invalid_date_format`, `test_rejects_non_numeric_debit`: unchanged
      substitution logic works as-is against the corrected fixture (same date/amount strings
      present).
- [x] 2.9 `test_handles_null_credits_correctly`, `test_preserves_memo_and_account_code`: rewritten
      to read `parsed[0]["debito_cents"]`/`parsed[0]["codigo_cuenta"]`/`parsed[0]["descripcion"]`
      directly.

## 3. `TestIngestSiigoCSVPersistence`: Confirm Still Aligned

- [x] 3.1 `test_ingest_creates_entries_and_lines` needed no change. Found and fixed two real bugs
      while verifying, both part of the original 19 failures:
      (a) `test_ingest_creates_approval_queue_on_imbalance` had its own inline CSV still using old
      English headers — rewritten to the Spanish format;
      (b) `test_ingest_idempotent_on_external_reference_id` asserted
      `summary2["row_count"] == count1` on re-upload, but `ingest_siigo_csv`'s `row_count` counts
      only newly-inserted entries — a true no-op re-upload correctly returns `0`. Fixed the
      assertion to `summary2["row_count"] == 0` (same fix applied in §4 to the integration-test
      twin of this test).

## 4. `test_shadow_gl_integration.py`: Fix the Four Fixture-Dependent Tests

- [x] 4.1 `test_siigo_csv_parses`: asserts `"referencia_externa" in row` (was
      `"external_reference_id"`), matching the flat-row shape.
- [x] 4.2 `test_xml_and_csv_both_valid`: passed unchanged once the fixture loads cleanly.
- [x] 4.3 `test_ingest_xml_and_csv_same_day`: passed unchanged.
      `test_csv_idempotency_no_duplicates`: same `row_count == 0` fix as §3.1(b) — was also
      asserting `row_count == count1` on re-upload.

## 5. Verify

- [x] 5.1 `RUN_SHADOW_GL=1 python -m pytest tests/test_shadow_gl_siigo_csv.py
      tests/test_shadow_gl_integration.py -v` from `apps/backend` → **24 passed** (23 real tests +
      1 new grouping test added in §2.4; the original 19 failures are gone, 0 unexpected skips).
- [x] 5.2 Ran the full `test_shadow_gl_*.py` + `test_phase6_e2e_simulation.py` suite: 72 passed, 2
      skipped, 16 failed, 9 errors — all 16+9 are the pre-existing, unrelated failures in
      `test_shadow_gl_schema.py`, `test_shadow_gl_stage1_migration.py`, and the four files in §5.3
      (broken cwd-relative subprocess paths, missing/renamed migration and test files). None
      reference Siigo CSV parsing or the fixture.
- [x] 5.3 Ran `test_shadow_gl_stage4_uploader.py tests/test_shadow_gl_stage5_error_handling.py
      tests/test_shadow_gl_stage8_e2e.py tests/test_phase6_e2e_simulation.py` in isolation:
      **10 failed, 20 passed, 2 skipped** — byte-for-byte the same counts as the pre-change
      baseline captured before touching any file. Confirmed unaffected.

## 6. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`. This change touches only test files and a test
fixture — no backend/frontend runtime code changes, no migration, nothing for Railway/Vercel to
build differently. Stage 11 here means: land on `main` and confirm CI (or the local suite) is
green, not a Railway/Vercel verification.

- [ ] 6.1 Commit + push to `main` (or via PR per repo convention).
- [ ] 6.2 Re-run §5.1's targeted command against the `main`-merged state to confirm green.
- [ ] 6.3 Create report:
      `openspec/changes/fix-siigo-csv-test-fixture-drift/reports/2026-08-18-deployment.md`
      documenting: no prod deploy needed (test-only change), suite green, out-of-scope items
      confirmed unaffected.
- [ ] 6.4 Archive the change (`openspec-archive-change` skill).
