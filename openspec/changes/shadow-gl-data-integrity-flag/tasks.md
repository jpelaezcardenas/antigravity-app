## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/shadow-gl-data-integrity-flag` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Migration (TDD: verify before/after on the live DB via Supabase MCP)

- [x] 1.1 Confirm next migration number by listing `apps/backend/migrations/` directly (do not
      trust memory — a numbering collision already happened once, see
      `docs/supabase-mcp-admin.md` §6) — confirmed 0042 (last was 0041)
- [x] 1.2 Write `apps/backend/migrations/0042_shadow_gl_is_verified_real.sql`:
      `ALTER TABLE erp_journal_entries ADD COLUMN is_verified_real BOOLEAN NOT NULL DEFAULT false;`
      `ALTER TABLE dian_xml_documents ADD COLUMN is_verified_real BOOLEAN NOT NULL DEFAULT false;`
- [x] 1.3 Apply the migration against `kpynymwghfwshvcvevxq` via Supabase MCP
- [x] 1.4 Verify: all 73 existing `erp_journal_entries` rows and 4 `dian_xml_documents` rows
      backfilled `false`

## 2. Backend: Service Layer Tests First (TDD)

- [x] 2.1 Added failing tests for `ingest_siigo_csv(..., is_verified_real=True)` /
      omitted-arg-defaults-false in `test_shadow_gl_siigo_csv.py`
- [x] 2.2 Added failing tests for `ingest_dian_xml(..., is_verified_real=True)` /
      omitted-arg-defaults-false in `test_shadow_gl_ingestion.py`
- [x] 2.3 Ran the new tests, confirmed TypeError (red) before implementation

## 3. Backend: Service Layer Implementation

- [x] 3.1 `ingest_siigo_csv(tenant_id, csv_text, is_verified_real: bool = False)` — flag included
      in `entry_data` before insert
- [x] 3.2 `ingest_dian_xml(tenant_id, raw_xml, is_verified_real: bool = False)` — flag included in
      the inserted `row` dict
- [x] 3.3 Ran tests from §2, confirmed green (4/4 passed)

## 4. Backend: Endpoint Layer

- [x] 4.1 `POST /dian-xml/ingest`: reads `is_verified_real` query param (default `false`)
- [x] 4.2 `POST /siigo-csv/ingest`: same
- [x] 4.3 `POST /siigo-csv/upload`: same
- [x] 4.4 `_persist_approved_entry` left unchanged (uses `False` default) — comment added noting
      this is deliberate, per design.md Non-Goals

## 5. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 5.1 Ran the full `test_shadow_gl_*.py` suite. Found 19 pre-existing failures, all confirmed
      independent of this change (stale English-header CSV fixture vs. the now-Spanish-header
      parser — same failures reproduce with none of this change's code present). Flagged as a
      separate follow-up (`task_718da7b8`), not fixed here — out of scope for an additive flag.
      This change's own 4 new tests: 0 regressions, all green.

## 6. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [x] 6.1 Captured pre-test DB baseline (73/136/4/20 rows across the four tables)
- [x] 6.2 Ran targeted tests for `shadow_gl_service.py`/`shadow_gl_endpoints.py` (4/4 passed)
- [x] 6.3 Ran the broader `test_shadow_gl_*.py` suite (13 passed, 19 pre-existing failures — see §5)
- [x] 6.4 Verified post-test DB state — **found and disclosed an incident**: a pre-existing,
      unrelated cleanup-fixture bug (not this change's code) deleted 44 `erp_journal_entries` +
      3 `dian_xml_documents` rows of already-documented synthetic/test data during the broader
      suite run. Load-bearing per-tenant SYNTH demo data (29 rows) confirmed unaffected. Founder
      informed immediately, chose to accept the loss over an incomplete partial restore. Root-cause
      fixture bug fixed in both affected test classes so it cannot recur. Full account in
      `docs/supabase-mcp-admin.md` §3 and the report below.
- [x] 6.5 Created report
      `openspec/changes/shadow-gl-data-integrity-flag/reports/2026-08-18-step-6-unit-test-and-db-verification.md`
- [x] 6.6 Step marked complete — tests pass (for this change's scope), report exists, incident
      disclosed

## 7. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [x] 7.1 Backend reachable at production Railway URL (no local server for this repo) — merged
      with Stage 11 verification below since there is no separate staging environment
- [x] 7.2 curl DIAN XML to `/dian-xml/ingest` with no flag → verified `is_verified_real=false` via
      Supabase MCP, deleted test row (cufe `curl-test-flag-verification-2026-08-18`)
- [x] 7.3 curl DIAN XML with `?is_verified_real=true` (different CUFE, suffix `-B`) → verified
      `true`, deleted test row
- [x] 7.4 curl Siigo CSV to `/siigo-csv/ingest` with no flag → verified `false`
      (`external_reference_id=CURL-TEST-001`), deleted test entry + lines
- [x] 7.5 curl Siigo CSV with `?is_verified_real=true` (`CURL-TEST-002`) → verified `true`, deleted
      test entry + lines
- [x] 7.6 All 4 curl commands, responses, and cleanup documented in this task list and the Stage 11
      deployment report
- [x] 7.7 Verified DB state matches the post-incident baseline (29/58/0) after cleanup — confirmed
      clean, no test residue

## 8. Documentation

- [x] 8.1 Updated `docs/admin-runbook-shadow-gl.md` curl examples to show `?is_verified_real=true`
- [x] 8.2 Updated `docs/api-shadow-gl-ingestion.md` to document the new query param + changelog
      entry (v1.1)
- [x] 8.3 Updated `docs/supabase-mcp-admin.md` §3 to reflect the flag is live in production, plus
      full incident disclosure

## 9. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app
- No frontend impact — Vercel build unaffected

- [x] 9.1 Merged feature branch (fast-forward, no conflicts), committed (`f984460`) + pushed to
      main. Staged only this change's files — left unrelated uncommitted work from another
      session untouched on the working tree.
- [x] 9.2 Railway deploy active — confirmed `/api/v1/health` returns 200
      (`{"status":"healthy",...}`) after deploy `da585a77` (SUCCESS)
- [x] 9.3 Re-ran curl checks (§7) against the live post-deploy backend, confirmed the flag works
      end to end in production, cleaned up all test rows
- [x] 9.4 Created deployment report:
      `openspec/changes/shadow-gl-data-integrity-flag/reports/2026-08-18-deployment.md`
- [x] 9.5 Archive the change (`openspec-archive-change` skill)
