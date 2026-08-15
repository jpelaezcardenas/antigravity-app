# Proposal: Shadow GL Real Data Ingestion (Cliente Cero)

**Change ID:** `shadow-gl-real-data-ingestion`  
**Status:** Proposal  
**Date:** 2026-06-25  
**Owner:** Juan David Peláez Cárdenas  
**Scope:** Phase 5 (post Phase 4 Shadow GL architecture)

## Problem Statement

The Shadow GL infrastructure (Phase 4) is architecturally complete and deployed:
- Tables: `dian_xml_documents`, `erp_journal_entries`, `erp_journal_lines`, `tenants`, `approval_queue`
- Parser & endpoint: UBL 2.1 XML ingestión via `POST /api/v1/shadow-gl/dian-xml/ingest` (verified working 2026-06-25)
- Idempotency: CUFE-based upsert prevents duplicates

**However, all Shadow GL tables are EMPTY.** Contexia (Cliente Cero) operates with real financial data that must flow into the Shadow GL to validate the architecture and prepare for external client onboarding.

## Goal

Enable **daily manual upload of Contexia's real accounting data** (XML DIAN + CSV/Excel Siigo) into the Shadow GL, with validation, error handling, and clean HITL for discrepancies.

By end of this change:
1. Admin can upload XML DIAN invoices daily → land in `dian_xml_documents`
2. Admin can upload Siigo CSV/Excel exports → parse into `erp_journal_entries` + `erp_journal_lines`
3. Both paths validate via Agent Critic (UBL 2.1, CUFE uniqueness, amounts as integer cents, currency checks)
4. Validation errors route to HITL (Approval Queue) with clear remediation instructions
5. SLA: Data from previous business day available before 9am daily
6. Documentation: Admin runbook + API docs for both formats

## Success Criteria

- ✅ Fixture XML DIAN ingested: verified 2026-06-25 (1 row in `dian_xml_documents`)
- ✅ Parser UBL 2.1 + endpoint exist and pass tests
- ✅ Agent Critic (arithmetic, CUFE uniqueness, currency) enforced
- [ ] CSV/Excel Siigo parser + ingestión endpoint built (Phase 5 Task 1)
- [ ] Admin tool (PWA file uploader or CLI) built (Phase 5 Task 2)
- [ ] Error handling + HITL routing tested (Phase 5 Task 3)
- [ ] Stage 11 deployment verified (Phase 5 Task 4)
- [ ] Admin runbook + API docs written (Phase 5 Task 5)

## Out of Scope (Future)

- Live DIAN webhook ingestion (captured in Phase 4 design, deferred to Phase 6)
- Siigo API live sync (deferred pending commercial negotiation + SyncManager)
- Auto-scheduling or cron-based ingestion
- Charting/visualization of Shadow GL data

## Technical Approach

### Format 1: XML DIAN (Already Implemented)

**Parser:** `shadow_gl_service.parse_dian_ubl_xml()`  
**Endpoint:** `POST /api/v1/shadow-gl/dian-xml/ingest`  
**Validation:**
- UBL 2.1 schema compliance (ElementTree parsing)
- Required fields: CUFE, IssueDate, issuer NIT, receiver NIT, total amount
- Currency code extraction (default: COP)
- Amount conversion to integer cents

**Idempotency:** Upsert on (tenant_id, CUFE) — re-upload same document = no duplicate

### Format 2: CSV/Excel Siigo (Phase 5 New)

**Source:** Siigo export of journal entries (required columns: date, account code, debit, credit, description)  
**Parser:** New service method `parse_siigo_csv()` or `parse_siigo_excel()`  
**Destination:** `erp_journal_entries` + `erp_journal_lines`  
**Validation:**
- CSV/Excel format (pandas for parsing)
- Required columns: date, account_code, debit_amount, credit_amount, memo
- Amounts as integer cents (same `_to_minor_units()` logic)
- Double-entry verification: SUM(debit) = SUM(credit) per transaction
- Account codes exist in Contexia's chart of accounts (tenant-specific)

**Idempotency:** Upsert on (tenant_id, external_reference_id, date) to prevent duplicates from repeated uploads

### Admin Tool (Phase 5 New)

Three options (pick one for MVP):

**Option A: PWA File Uploader** (simplest for UI)
- Form: "Upload XML DIAN" + "Upload Siigo CSV/Excel"
- Endpoint: POST `/api/v1/shadow-gl/files/upload` with file + format parameter
- Feedback: live parsing errors, row count, validation summary
- Location: Hermes Workspace or standalone

**Option B: CLI Script** (best for automation)
- Script: `admin_upload_shadow_gl.py` (local, read-only Contexia data)
- Runs: daily by admin, reads XML DIAN export folder + Siigo CSV
- Posts to endpoints via curl or httpx
- Logs: success/error summary to stderr

**Option C: Raw Endpoint** (most minimal)
- Use existing `POST /api/v1/shadow-gl/dian-xml/ingest` for XML
- Document curl/Postman examples for CSV
- Admin uses tools they already have

**Recommendation:** Start with Option C (raw endpoint + docs), then add Option A (PWA) in Phase 6 if UX is bottleneck.

## Dependencies

- Supabase project `kpynymwghfwshvcvevxq` (already configured)
- Backend FastAPI (Railway `production-175a`)
- Existing: `parse_dian_ubl_xml()`, `ingest_dian_xml()`, tests
- Siigo API credentials (for export format reference; not live sync)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Duplicate CUFE/entry uploads | Data quality | Idempotency by CUFE + (tenant, external_ref, date) |
| Malformed CSV or missing columns | Silent errors | Parse validation + clear error messages to HITL |
| Amount precision loss (floats) | Financial accuracy | Enforce integer cents throughout (tested) |
| Admin doesn't know SLA | Delays in closing | Document runbook with daily checklist + alerts |
| Siigo format variations | Parser brittleness | Parameterize column names; start with standard export |

## Timeline

- **Proposal:** 2026-06-25 (this doc)
- **Design:** 2026-06-25 (design.md)
- **Tasks:** 2026-06-25 (tasks.md with Stage 11)
- **Implementation:** 2026-06-26 to 2026-06-30 (5 days, Phase 5)
- **Stage 11 Deploy:** 2026-06-30 → 2026-07-01

## Next Step

→ Review this proposal, confirm scope/approach, then proceed to **design.md**
