## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [ ] 0.1 Create feature branch `feature/shadow-gl-data-integrity-flag` from `main`
- [ ] 0.2 Verify branch creation and current branch status

## 1. Migration (TDD: verify before/after on the live DB via Supabase MCP)

- [ ] 1.1 Confirm next migration number by listing `apps/backend/migrations/` directly (do not
      trust memory — a numbering collision already happened once, see
      `docs/supabase-mcp-admin.md` §6)
- [ ] 1.2 Write `apps/backend/migrations/00NN_shadow_gl_is_verified_real.sql`:
      `ALTER TABLE erp_journal_entries ADD COLUMN is_verified_real BOOLEAN NOT NULL DEFAULT false;`
      `ALTER TABLE dian_xml_documents ADD COLUMN is_verified_real BOOLEAN NOT NULL DEFAULT false;`
- [ ] 1.3 Apply the migration against `kpynymwghfwshvcvevxq` via Supabase MCP
- [ ] 1.4 Verify: `SELECT is_verified_real, COUNT(*) FROM erp_journal_entries GROUP BY 1;` returns
      all 73 existing rows as `false`; same check on `dian_xml_documents` (4 rows, `false`)

## 2. Backend: Service Layer Tests First (TDD)

- [ ] 2.1 Add failing tests in `apps/backend/tests/test_shadow_gl_siigo_csv.py` and the DIAN XML
      test file: `ingest_siigo_csv(..., is_verified_real=True)` persists `is_verified_real=true`;
      omitting the arg persists `false`
- [ ] 2.2 Add failing test: `ingest_dian_xml(..., is_verified_real=True)` persists
      `is_verified_real=true`; omitting the arg persists `false`
- [ ] 2.3 Run the new tests, confirm they fail (red) before implementation

## 3. Backend: Service Layer Implementation

- [ ] 3.1 `ingest_siigo_csv(tenant_id, csv_text, is_verified_real: bool = False)` — include the
      flag in `entry_data` before insert
- [ ] 3.2 `ingest_dian_xml(tenant_id, raw_xml, is_verified_real: bool = False)` — include the flag
      in the inserted `row` dict
- [ ] 3.3 Run tests from §2, confirm they pass (green)

## 4. Backend: Endpoint Layer

- [ ] 4.1 `POST /dian-xml/ingest`: read `is_verified_real` query param (default `false`), pass
      through to `ingest_dian_xml`
- [ ] 4.2 `POST /siigo-csv/ingest`: same, passed through to `ingest_siigo_csv`
- [ ] 4.3 `POST /siigo-csv/upload`: same query param, passed through to `ingest_siigo_csv`
- [ ] 4.4 `_persist_approved_entry` stays unchanged (uses the `False` default per design.md
      Non-Goals) — add a one-line comment noting this is deliberate, not an oversight

## 5. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [ ] 5.1 Run the full `test_shadow_gl_*.py` suite, confirm no regressions in existing
      XML/CSV parsing or idempotency tests

## 6. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 6.1 Capture pre-test DB baseline: row counts + `is_verified_real` distribution on both
      tables
- [ ] 6.2 Run targeted tests for `shadow_gl_service.py` and `shadow_gl_endpoints.py`
- [ ] 6.3 Run the broader backend test suite
- [ ] 6.4 Verify post-test DB state matches baseline (tests should not leave stray rows against
      the live project; use local/test DB config if the suite hits a live connection)
- [ ] 6.5 Create report
      `openspec/changes/shadow-gl-data-integrity-flag/reports/2026-08-18-step-6-unit-test-and-db-verification.md`
- [ ] 6.6 Mark this step complete only after tests pass and the report exists

## 7. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 7.1 Ensure the backend is reachable (production Railway URL — no local server for this repo)
- [ ] 7.2 `curl` a synthetic DIAN XML fixture to `/dian-xml/ingest` with no flag → verify inserted
      row has `is_verified_real=false` via Supabase MCP, then delete the test row
- [ ] 7.3 `curl` the same fixture with `?is_verified_real=true` (different CUFE) → verify
      `is_verified_real=true`, then delete the test row
- [ ] 7.4 `curl` a synthetic Siigo CSV fixture to `/siigo-csv/ingest` with no flag → verify
      `false`, then delete the test rows (entries + lines)
- [ ] 7.5 `curl` the same fixture with `?is_verified_real=true` (different reference id) → verify
      `true`, then delete the test rows
- [ ] 7.6 Document all curl commands, responses, and cleanup in the same report as §6.5
- [ ] 7.7 Verify DB state matches the §6.1 baseline after cleanup

## 8. Documentation

- [ ] 8.1 Update `docs/admin-runbook-shadow-gl.md` curl examples to show `?is_verified_real=true`
      for genuine Siigo/DIAN uploads
- [ ] 8.2 Update `docs/api-shadow-gl-ingestion.md` to document the new query param on all three
      endpoints
- [ ] 8.3 Update `docs/supabase-mcp-admin.md` §3 to reflect the flag is live (not just proposed)

## 9. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app
- No frontend impact — Vercel build unaffected

- [ ] 9.1 Merge feature branch, commit + push to main
- [ ] 9.2 Railway deploy active — verify `/api/v1/health` returns 200 after deploy
- [ ] 9.3 Re-run one curl check from §7 against the live post-deploy backend, confirm the flag
      still works end to end, clean up the test row
- [ ] 9.4 Create deployment report:
      `openspec/changes/shadow-gl-data-integrity-flag/reports/2026-08-18-deployment.md`
- [ ] 9.5 Archive the change (`openspec-archive-change` skill)
