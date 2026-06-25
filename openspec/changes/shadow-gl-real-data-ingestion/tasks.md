# Tasks: Shadow GL Real Data Ingestion (Cliente Cero)

**Change ID:** `shadow-gl-real-data-ingestion`  
**Status:** Tasks  
**Date:** 2026-06-25

## Overview

Baby-step implementation of dual ingestion (XML DIAN + CSV Siigo) for Shadow GL. TDD throughout.

---

## Stage 1. Database Schema & Migrations

### 1.1 Create migration: Add external_reference_id to erp_journal_entries

- [ ] File: `apps/backend/migrations/001_shadow_gl_siigo_columns.sql`
- [ ] Task:
  ```sql
  ALTER TABLE erp_journal_entries 
    ADD COLUMN IF NOT EXISTS external_reference_id TEXT,
    ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT NOW(),
    ADD UNIQUE(tenant_id, external_reference_id, transaction_date);
  ```
- [ ] Test: `npm run migrate:test` passes
- [ ] Verify: Column exists in Supabase project kpynymwghfwshvcvevxq

### 1.2 Add constraints to erp_journal_lines

- [ ] File: Same migration (001_...)
- [ ] Task:
  ```sql
  ALTER TABLE erp_journal_lines 
    ADD CONSTRAINT check_amounts_not_negative 
    CHECK (debit_amount >= 0 AND credit_amount >= 0);
  ```
- [ ] Verify: Constraint appears in `information_schema.check_constraints`

---

## Stage 2. CSV Siigo Parser (TDD)

### 2.1 Write failing tests for parse_siigo_csv()

- [ ] File: `apps/backend/tests/test_shadow_gl_siigo_csv.py`
- [ ] Tests (all **failing initially**):
  1. `test_parses_valid_siigo_csv()` — standard export (date, account, debit, credit, memo)
  2. `test_rejects_missing_required_column()` — missing "debit_amount"
  3. `test_converts_amounts_to_minor_units()` — "1234.56" → 123456
  4. `test_detects_imbalanced_entry()` — SUM(debit) ≠ SUM(credit)
  5. `test_handles_empty_csv()` — 0 lines → returns empty list
  6. `test_rejects_invalid_date_format()` — date not ISO 8601

- [ ] Fixture: `apps/backend/tests/fixtures/siigo_journal_export.csv`
  ```csv
  transaction_date,account_code,account_name,debit_amount,credit_amount,memo,external_reference_id
  2026-06-20,1105,Caja,10000.00,,Recibido efectivo,DOC-001-001
  2026-06-20,4105,Ingresos,,,Venta de servicios,DOC-001-001
  2026-06-21,1205,Bancos,50000.00,,Transferencia cliente,TRF-050
  2026-06-21,4105,Ingresos,,,Venta adicional,TRF-050
  ```
- [ ] Run: `pytest test_shadow_gl_siigo_csv.py -v` → 6 failures ✓

### 2.2 Implement parse_siigo_csv() in shadow_gl_service.py

- [ ] File: `apps/backend/services/shadow_gl_service.py`
- [ ] Add imports: `import csv, io, pandas as pd` (or use `csv.DictReader` for simplicity)
- [ ] Implement `parse_siigo_csv(csv_text: str) -> Tuple[List[Dict], Optional[str]]`
  - Parse as DictReader (headers auto-detected)
  - Validate required columns: date, account_code, debit_amount, credit_amount, memo, external_reference_id
  - Convert amounts to integer cents via `_to_minor_units()`
  - Group by external_reference_id (transaction)
  - Check SUM(debit) = SUM(credit) per transaction
  - Return: (list of journal entries + nested lines, error message if imbalanced)
  
- [ ] Run: `pytest test_shadow_gl_siigo_csv.py -v` → 6 passing ✓

### 2.3 Add error class SiigoCsvParseError

- [ ] File: `apps/backend/services/shadow_gl_service.py`
- [ ] Class: `SiigoCsvParseError(ValueError)` (parallel to `DianXmlParseError`)
- [ ] Use in parse_siigo_csv() for validation failures

---

## Stage 3. CSV Siigo Persistence (TDD)

### 3.1 Write failing tests for ingest_siigo_csv()

- [ ] File: `apps/backend/tests/test_shadow_gl_siigo_csv.py` (extend with persistence)
- [ ] Tests (all **failing initially**, gated by `RUN_SHADOW_GL=1`):
  1. `test_ingest_siigo_csv_creates_entries()` — valid CSV → rows in erp_journal_entries + erp_journal_lines
  2. `test_ingest_idempotent_on_external_reference_id()` — re-upload same ref_id → no duplicate
  3. `test_ingest_imbalanced_entry_returns_202()` — SUM(debit) ≠ SUM(credit) → response 202, creates approval_queue task
  4. `test_ingest_invalid_csv_returns_400()` — malformed CSV → error, no DB insert

- [ ] Fixtures: Real vs synthetic test data in CSV format

- [ ] Run: `RUN_SHADOW_GL=1 pytest test_shadow_gl_siigo_csv.py::TestIngestSiigoCSV -v` → 4 failures ✓

### 3.2 Implement ingest_siigo_csv()

- [ ] File: `apps/backend/services/shadow_gl_service.py`
- [ ] Signature: `async def ingest_siigo_csv(tenant_id: str, csv_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]`
- [ ] Logic:
  - Parse CSV via parse_siigo_csv()
  - If parsing fails: return (False, None, error_message)
  - If accounting imbalance detected: create approval_queue entry, return (False, None, "created HITL task")
  - Upsert into erp_journal_entries (on tenant_id, external_reference_id, transaction_date)
  - Upsert into erp_journal_lines for each line
  - Return: (True, summary_dict, None)

- [ ] Summary dict includes: row_count, date_range, total_debit, total_credit

- [ ] Run: `RUN_SHADOW_GL=1 pytest test_shadow_gl_siigo_csv.py::TestIngestSiigoCSV -v` → 4 passing ✓

---

## Stage 4. CSV Siigo Endpoint (TDD)

### 4.1 Write failing test for CSV ingestion endpoint

- [ ] File: `apps/backend/tests/test_shadow_gl_endpoints.py` (create if doesn't exist)
- [ ] Test: `test_ingest_siigo_csv_endpoint()` — POST /api/v1/shadow-gl/siigo-csv/ingest with CSV body
  - Expect 200 response: `{"success": true, "row_count": 4, "date_range": "2026-06-20..2026-06-21"}`
  - Expect 202 response (imbalanced): `{"success": false, "error": "...", "hitl_task_id": "..."}`

- [ ] Run: `pytest test_shadow_gl_endpoints.py::test_ingest_siigo_csv_endpoint -v` → 1 failure ✓

### 4.2 Implement siigo_csv_ingest_endpoint() in shadow_gl_endpoints.py

- [ ] File: `apps/backend/presentation/shadow_gl_endpoints.py`
- [ ] Endpoint: `@router.post("/siigo-csv/ingest", response_model=SiigoCSVIngestResponse)`
- [ ] Logic:
  - Read request body (CSV text)
  - Resolve tenant_id (Cliente Cero)
  - Call ingest_siigo_csv(tenant_id, csv_text)
  - Return 200 or 202 based on success flag
  
- [ ] Response model: `SiigoCSVIngestResponse(success: bool, row_count: int, error: str, hitl_task_id: str)`

- [ ] Run: `pytest test_shadow_gl_endpoints.py::test_ingest_siigo_csv_endpoint -v` → 1 passing ✓

---

## Stage 5. Integration Tests (XML + CSV)

### 5.1 Write integration test

- [ ] File: `apps/backend/tests/test_shadow_gl_integration.py` (create if new)
- [ ] Test: `test_ingest_xml_and_csv_same_day()`
  - Upload XML DIAN invoice (date: 2026-06-22)
  - Upload Siigo CSV with entries (dates: 2026-06-22, 2026-06-23)
  - Verify: dian_xml_documents has 1 row, erp_journal_entries has N rows, erp_journal_lines has M rows
  - Verify: Re-uploading same CSV creates no duplicates (idempotency)

- [ ] Run: `RUN_SHADOW_GL=1 pytest test_shadow_gl_integration.py -v` → 1 passing ✓

---

## Stage 6. Documentation

### 6.1 Admin Runbook

- [ ] File: `docs/admin-runbook-shadow-gl.md`
- [ ] Content:
  - Daily checklist (before 9am deadline)
  - How to export XML DIAN from DIAN portal
  - How to export Siigo journal (steps: Reports → Journal → Download CSV)
  - Upload commands (curl examples):
    ```bash
    # XML DIAN
    curl -X POST -H "Content-Type: application/xml" \
      https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/dian-xml/ingest \
      --data @invoice_20260625.xml

    # CSV Siigo
    curl -X POST -H "Content-Type: text/csv" \
      https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
      --data @siigo_journal_20260625.csv
    ```
  - Troubleshooting: common errors + fixes
  - Rollback: how to delete bad batch from DB (SQL provided, requires admin access)

### 6.2 API Documentation

- [ ] File: `docs/api-shadow-gl-ingestion.md`
- [ ] Content:
  - Endpoint 1: POST /api/v1/shadow-gl/dian-xml/ingest
    - Request: raw XML body
    - Response: 200 `{"success": true, "cufe": "...", "document_type": "..."}`
    - Response: 400 `{"error": "..."}`
  - Endpoint 2: POST /api/v1/shadow-gl/siigo-csv/ingest
    - Request: CSV body (format: date, account_code, debit, credit, memo, ref_id)
    - Response: 200 `{"success": true, "row_count": N, "date_range": "..."}`
    - Response: 202 `{"success": false, "error": "imbalance", "hitl_task_id": "..."}`
  - Error codes + remediation
  - Idempotency guarantees

### 6.3 Update README.md

- [ ] Add section: "Shadow GL Data Ingestion (Cliente Cero)"
  - Link to admin runbook
  - Link to API docs
  - Current status: "Phase 5 in progress, 2026-06-25"

---

## Stage 7. Manual Testing (Cliente Cero Real Data)

### 7.1 Prepare Contexia real data exports

- [ ] Get real XML DIAN invoices from Contexia (last 7 days)
- [ ] Get real Siigo journal export (last 7 days) in CSV format
- [ ] Save to `openspec/changes/shadow-gl-real-data-ingestion/fixtures/`

### 7.2 Test XML DIAN upload

- [ ] Command: `curl -X POST --data @contexia_invoice_20260618.xml https://...`
- [ ] Verify: 200 response, CUFE appears in dian_xml_documents
- [ ] Verify: Re-upload same file → idempotent (200 response, no duplicate)
- [ ] Verify: dian_xml_documents row count increases

### 7.3 Test CSV Siigo upload

- [ ] Command: `curl -X POST --data @contexia_siigo_20260620.csv https://...`
- [ ] Verify: 200 response, row_count in response matches CSV lines
- [ ] Verify: erp_journal_entries + erp_journal_lines populated
- [ ] Verify: Re-upload same file → idempotent (200 response, no duplicate)
- [ ] Verify: Amounts are correct (in centavos, no rounding errors)

### 7.4 Test error scenarios

- [ ] Malformed XML → 400 response
- [ ] Missing CSV column → 400 response
- [ ] Imbalanced Siigo entry (SUM(debit) ≠ SUM(credit)) → 202 response + HITL task created
- [ ] Verify HITL task is visible in approval_queue

---

## Stage 8. Code Quality & Tests

### 8.1 Type checking

- [ ] Run: `mypy apps/backend/services/shadow_gl_service.py --strict`
- [ ] Fix any type errors
- [ ] Run: `mypy apps/backend/presentation/shadow_gl_endpoints.py --strict`

### 8.2 Linting

- [ ] Run: `ruff check apps/backend/services/ apps/backend/presentation/`
- [ ] Fix any style violations (naming, imports, line length)

### 8.3 Test coverage

- [ ] Run: `pytest apps/backend/tests/test_shadow_gl*.py -v --cov=apps/backend/services --cov=apps/backend/presentation`
- [ ] Target: ≥ 85% coverage for shadow_gl_service.py and shadow_gl_endpoints.py

### 8.4 All tests pass

- [ ] Run: `pytest` (full suite)
- [ ] Expect: 0 failures, 0 skipped (or skipped tests require RUN_SHADOW_GL=1)

---

## Stage 9. Code Review & Readiness

### 9.1 Commit changes (before deployment)

- [ ] Staged: All .py files, .md files, migration files, tests
- [ ] Commit message:
  ```
  feat: Shadow GL real data ingestion (XML DIAN + CSV Siigo)

  - Add parse_siigo_csv() parser + ingest_siigo_csv() persistence
  - Implement POST /api/v1/shadow-gl/siigo-csv/ingest endpoint
  - Add migrations for external_reference_id + source + uploaded_at columns
  - Add comprehensive tests (TDD, unit + integration + E2E)
  - Add admin runbook + API documentation
  - Idempotency: CUFE-based for XML, (tenant, ref_id, date) for CSV
  - HITL: imbalanced entries routed to approval_queue for manual review

  Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
  ```

### 9.2 Push to main

- [ ] Command: `git push origin main`
- [ ] Verify: GitHub shows commit on main branch

---

## Stage 10. Deployment Verification (Railway + Vercel)

### 10.1 Railway backend deployment

- [ ] Check: Railway build for `production-175a` completes (green ✅)
- [ ] Check: `docker ps` shows container is running (if local WSL)
- [ ] Check: `curl https://antigravity-app-production-175a.up.railway.app/api/v1/health`
  - Expect 200 response: `{"status": "healthy"}`
- [ ] Check: No error logs in Railway dashboard

### 10.2 Verify endpoints are live

- [ ] Test XML endpoint:
  ```bash
  curl -X POST -H "Content-Type: application/xml" \
    https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/dian-xml/ingest \
    --data @test_fixture.xml
  ```
  - Expect 200: `{"success": true, ...}`

- [ ] Test CSV endpoint:
  ```bash
  curl -X POST -H "Content-Type: text/csv" \
    https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
    --data @test_fixture.csv
  ```
  - Expect 200 or 202: `{"success": ..., ...}`

### 10.3 Verify migrations applied

- [ ] Check Supabase project `kpynymwghfwshvcvevxq`:
  - `erp_journal_entries` has new columns: external_reference_id, source, uploaded_at
  - UNIQUE constraint on (tenant_id, external_reference_id, transaction_date) exists
  - `erp_journal_lines` has CHECK constraint on amounts

### 10.4 Smoke test with real data

- [ ] Upload Contexia's real XML DIAN invoice
- [ ] Verify: Row appears in dian_xml_documents
- [ ] Upload Contexia's real Siigo CSV export
- [ ] Verify: Rows appear in erp_journal_entries + erp_journal_lines
- [ ] Verify: No duplicates on re-upload

---

## Stage 11. Deploy Report & Archive

### 11.1 Create deployment report

- [ ] File: `openspec/changes/shadow-gl-real-data-ingestion/reports/2026-06-30-deployment.md`
- [ ] Content:
  ```markdown
  # Deployment Report: shadow-gl-real-data-ingestion
  
  **Date:** 2026-06-30  
  **Status:** ✅ SUCCESS
  
  ## Commits
  - SHA: [commit hash from main]
  - Message: "feat: Shadow GL real data ingestion (XML DIAN + CSV Siigo)"
  
  ## Build Status
  - Vercel: ✅ Green (no frontend changes)
  - Railway: ✅ Green, container healthy
  
  ## Endpoint Verification
  - POST /api/v1/shadow-gl/dian-xml/ingest: ✅ 200 OK
  - POST /api/v1/shadow-gl/siigo-csv/ingest: ✅ 200/202 OK
  - GET /api/v1/health: ✅ 200 healthy
  
  ## Database Verification
  - Migrations applied: ✅
  - dian_xml_documents: 1 row (fixture)
  - erp_journal_entries: N rows (real Siigo data)
  - erp_journal_lines: M rows (detail)
  - No duplicates on re-upload: ✅
  
  ## Smoke Tests
  - Real XML DIAN invoice uploaded: ✅
  - Real Siigo CSV export uploaded: ✅
  - Idempotency verified: ✅
  - HITL error handling tested: ✅ (imbalanced entry → approval_queue task)
  
  ## Documentation
  - Admin runbook: docs/admin-runbook-shadow-gl.md ✅
  - API docs: docs/api-shadow-gl-ingestion.md ✅
  - README updated: ✅
  
  ## Rollback Plan
  If issues arise:
  1. Delete rows: `DELETE FROM erp_journal_entries WHERE uploaded_at > '2026-06-30'`
  2. Revert commit: `git revert [SHA]`
  3. Push: `git push origin main`
  4. Railway auto-redeploys
  
  ## Next Phase
  - Phase 6: Live DIAN webhook ingestion (design in progress)
  - Phase 6: SyncManager API integration for Siigo (commercial negotiation pending)
  - Phase 6: PWA file uploader UI in Hermes Workspace
  ```

### 11.2 Archive the change

- [ ] Move to `openspec/changes/archive/shadow-gl-real-data-ingestion/`
- [ ] Command: `mv openspec/changes/shadow-gl-real-data-ingestion openspec/changes/archive/`

### 11.3 Update memory/status

- [ ] Update MEMORY.md (auto-tracked by Claude Code)
- [ ] Mark as: "Phase 5 - shadow-gl-real-data-ingestion COMPLETED (2026-06-30)"

---

## Acceptance Criteria (All Must Pass)

- [ ] All tests pass (pytest with RUN_SHADOW_GL=1)
- [ ] Type checking: mypy --strict, 0 errors
- [ ] Code coverage: ≥ 85% for shadow_gl_*
- [ ] dian_xml_documents: ≥ 1 real row (fixture verified)
- [ ] erp_journal_entries + lines: ≥ 20 rows (real Siigo data)
- [ ] No duplicates on re-upload (idempotency verified)
- [ ] HITL error handling: imbalanced entry → approval_queue task
- [ ] Admin can execute curl commands from runbook without debugging
- [ ] Endpoints respond in < 500ms (XML), < 2s (CSV)
- [ ] Deployment report written + archived
- [ ] README + docs updated

---

## Timeline

- **Stage 1–3:** 2026-06-25 (database + parsers, TDD)
- **Stage 4–5:** 2026-06-26 (endpoints + integration, TDD)
- **Stage 6:** 2026-06-27 (documentation)
- **Stage 7:** 2026-06-28 (manual E2E testing with real data)
- **Stage 8–9:** 2026-06-29 (code quality + review + commit)
- **Stage 10–11:** 2026-06-30 (deployment + report + archive)

---

## Blockers & Questions (Resolve Before Proceeding)

1. **Siigo CSV format** — Do we have a real sample export from Contexia's Siigo? Or should I generate a synthetic one?
2. **Chart of Accounts** — Does a `erp_chart_of_accounts` table exist to validate account codes?
3. **Rollback authority** — Can admin delete rows, or does only backend service have DB write access?
4. **Approval Queue workflow** — Who reviews HITL tasks? Hermes Workspace Approval Queue or separate Centinela workflow?

---

## Execution Plan (Next Action)

1. ✅ Proposal + design approved (this doc)
2. ⏭️ **Clarify blockers above with Juan David**
3. ⏭️ **Start Stage 1: Database schema + migrations (TDD)**
4. → Proceed through Stages 2–11 sequentially
5. → Complete Stage 11 deploy + report before considering "done"
