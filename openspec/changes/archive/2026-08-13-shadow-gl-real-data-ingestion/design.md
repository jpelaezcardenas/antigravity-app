# Design: Shadow GL Real Data Ingestion (Cliente Cero)

**Change ID:** `shadow-gl-real-data-ingestion`  
**Status:** Design  
**Date:** 2026-06-25

## Architecture Decisions

### Decision 1: Dual Ingestion Pipeline (XML DIAN + CSV Siigo)

**Choice:** Separate parsers + endpoints, but unified validation layer (Agent Critic)

**Rationale:**
- XML DIAN ≠ CSV Siigo structurally (hierarchical vs flat; invoice-level vs line-level detail)
- Both feed same Shadow GL tables but via different routes:
  - XML DIAN → `dian_xml_documents` (fiscal truth, immutable)
  - CSV Siigo → `erp_journal_entries` + `erp_journal_lines` (accounting truth, mutable)
- Separate endpoints allow independent versioning + testing
- Unified validation (Agent Critic) ensures both paths respect arithmetic + currency rules

**Files:**
- `apps/backend/services/shadow_gl_service.py` — add `parse_siigo_csv()`, update Agent Critic
- `apps/backend/presentation/shadow_gl_endpoints.py` — add `POST /api/v1/shadow-gl/siigo-csv/ingest`
- `apps/backend/tests/test_shadow_gl_ingestion.py` — add CSV parsing + persistence tests

### Decision 2: Idempotency Strategy

**XML DIAN:** Upsert on `(tenant_id, cufe)` — CUFE is globally unique in DIAN universe

```sql
INSERT INTO dian_xml_documents (tenant_id, cufe, document_type, ...)
VALUES (...)
ON CONFLICT (tenant_id, cufe) DO UPDATE SET updated_at = NOW();
```

**CSV Siigo:** Upsert on `(tenant_id, external_reference_id, transaction_date)` — reference_id is Siigo's document/voucher ID

```sql
INSERT INTO erp_journal_entries (tenant_id, external_reference_id, transaction_date, ...)
VALUES (...)
ON CONFLICT (tenant_id, external_reference_id, transaction_date) DO UPDATE SET updated_at = NOW();
```

**Why:** Prevents duplicates if admin re-uploads same day's export, but allows legitimate corrections.

### Decision 3: Validation Layer (Agent Critic)

**Parser-level checks (deterministic, no LLM):**
1. XML well-formedness (ElementTree parse succeeds)
2. CSV structure (required columns present, proper types)
3. CUFE or external_reference_id uniqueness within batch (no duplicates in upload)
4. Amount precision: Decimal → integer cents, no floats (prevents rounding errors)
5. Currency code valid ISO 4217 (COP, USD, etc.)
6. Date format valid ISO 8601

**Post-insert checks (SQL constraints + application logic):**
1. `erp_journal_lines.debit_amount + credit_amount > 0` per line
2. `erp_journal_entries.SUM(debit) = SUM(credit)` per transaction (catches data entry errors)
3. Account codes exist in tenant's chart of accounts (foreign key or RLS)
4. No negative amounts (flagged as anomaly, routed to HITL)

**LLM-level check (future, Phase 6):**
- Transaction classification anomalies (e.g., customer payment recorded as expense)
- Threshold-based alerts (unusual transaction volume, large single items)

**For this Phase 5:** Only parser-level + SQL-level checks. All errors route to Approval Queue with clear remediation.

### Decision 4: Admin Tool Strategy (MVP = Minimal)

**Phase 5 MVP:** Raw endpoints + curl/Postman examples (Option C)

**Rationale:**
- Endpoints already exist (XML) or are trivial to build (CSV)
- Admin can test immediately with curl: `curl -X POST -d @invoice.xml https://...`
- No UI complexity, no Hermes integration delays
- Documents API for later PWA/CLI tools (Phase 6)

**Phase 5 deliverable:**
- `docs/api-shadow-gl-ingestion.md` — curl examples for both formats
- `admin-runbook.md` — daily checklist, troubleshooting, SLA (9am deadline)
- Endpoint responses include row count, validation errors, HITL task ID if created

**Phase 6 (optional):**
- PWA file uploader in Hermes Workspace
- Python CLI script (`scripts/admin_upload_shadow_gl.py`)

### Decision 5: Error Handling + HITL Routing

**Parse Error (invalid XML/CSV):**
```json
{
  "success": false,
  "error": "Malformed XML: unclosed element at line 15",
  "remediation": "Check XML syntax and retry"
}
```
→ Response 400, no HITL task (admin fixes + reupload)

**Validation Error (missing field, invalid amount):**
```json
{
  "success": false,
  "error": "Missing required field: CUFE",
  "remediation": "DIAN invoice must include UUID (CUFE); contact DIAN for corrected document"
}
```
→ Response 400, no HITL task

**Accounting Anomaly (SUM(debit) ≠ SUM(credit)):**
```json
{
  "success": false,
  "error": "Journal entry imbalance detected: debit=105000 COP, credit=100000 COP",
  "remediation": "Create HITL task for manual review"
}
```
→ Response 202 (accepted for review), creates row in `approval_queue`:
```sql
INSERT INTO approval_queue (..., draft_type, status, context)
VALUES (..., 'journal_entry_correction', 'pending_approval', {
  "tenant_id": "...",
  "issue": "entry_imbalance",
  "original_data": {...},
  "suggested_correction": {...}
})
```

**Duplicate CUFE (already ingested):**
```json
{
  "success": true,
  "cufe": "existing-cufe-123",
  "message": "Document already ingested on 2026-06-20; skipping duplicate",
  "action": "none"
}
```
→ Response 200 (idempotent success)

### Decision 6: Tenant Resolution

**Current:** Hardcoded to Cliente Cero (`_resolve_tenant_id()` in shadow_gl_endpoints.py)

**Phase 5:** Keep as-is. All ingestion routes to `tenants.is_cliente_cero = true`.

**Phase 6:** When external clients onboard, add auth middleware to extract `tenant_id` from JWT claims.

## Data Flow Diagrams

### XML DIAN Ingestion

```
Admin: curl -X POST --data @invoice.xml https://api/v1/shadow-gl/dian-xml/ingest
  ↓
Endpoint: shadow_gl_endpoints.ingest_dian_xml_endpoint()
  ├─ Parse XML body
  ├─ Resolve tenant_id (Cliente Cero)
  ├─ Call service: ingest_dian_xml(tenant_id, raw_xml)
  │    ├─ Parser: parse_dian_ubl_xml() — extract fields, validate UBL 2.1
  │    ├─ Agent Critic: amounts → integer cents, CUFE not empty, currency valid
  │    ├─ DB: Upsert into dian_xml_documents on (tenant_id, cufe)
  │    └─ Return: (success, document_row, error)
  └─ Response 200: {"success": true, "cufe": "...", "document_type": "invoice"}
```

### CSV Siigo Ingestion (Phase 5 New)

```
Admin: curl -X POST -F "file=@siigo_export.csv" https://api/v1/shadow-gl/siigo-csv/ingest
  ↓
Endpoint: shadow_gl_endpoints.ingest_siigo_csv_endpoint()
  ├─ Parse CSV file
  ├─ Resolve tenant_id (Cliente Cero)
  ├─ Call service: ingest_siigo_csv(tenant_id, csv_data)
  │    ├─ Parser: parse_siigo_csv() — extract journal entries + lines
  │    ├─ Agent Critic: amounts → integer cents, currency valid, required columns present
  │    ├─ Arithmetic check: SUM(debit) = SUM(credit) per entry
  │    ├─ DB: 
  │    │    ├─ Upsert into erp_journal_entries on (tenant_id, external_reference_id, date)
  │    │    ├─ Upsert into erp_journal_lines on (entry_id, line_seq)
  │    ├─ If arithmetic fails: create approval_queue entry + return 202
  │    └─ Return: (success, row_count, error)
  └─ Response 200 or 202 with summary
```

## Database Schema Updates

### New Columns (if not already present)

**erp_journal_entries:**
```sql
ALTER TABLE erp_journal_entries ADD COLUMN IF NOT EXISTS
  external_reference_id TEXT,  -- Siigo voucher/document ID
  source TEXT,  -- "siigo_export" or "manual"
  uploaded_at TIMESTAMP,
  UNIQUE(tenant_id, external_reference_id, transaction_date);
```

**erp_journal_lines:**
```sql
-- Already has debit_amount, credit_amount, currency_code (from Phase 4)
-- Ensure NOT NULL + CHECK constraints:
ALTER TABLE erp_journal_lines ADD CONSTRAINT
  check_amounts_not_negative CHECK (debit_amount >= 0 AND credit_amount >= 0);
```

**approval_queue:**
```sql
-- Already exists from Phase 4; reuse for journal entry corrections
```

## Test Coverage

**Existing tests (passing):**
- `test_shadow_gl_schema.py` — table structure ✓
- `test_shadow_gl_ingestion.py` — XML parsing + persistence ✓

**New tests (Phase 5 TDD):**
- `test_siigo_csv_parsing.py`:
  - Valid CSV → correct fields extracted
  - Missing column → DianXmlParseError (reuse exception class or new SiigoCsvParseError)
  - Duplicate external_reference_id → idempotent
  - Imbalanced entry (debit ≠ credit) → 202 response + HITL task
  - Amount precision: "1234.56" COP → 123456 cents
- `test_shadow_gl_integration.py`:
  - Upload XML + CSV in same day → both land correctly
  - Duplicate CUFE → no second row, 200 response
  - Duplicate external_reference_id → no second row, 200 response

**Manual test (Phase 5):**
- Admin uploads Contexia's real XML DIAN invoices (last 7 days)
- Admin uploads Contexia's real Siigo journal export (last 7 days)
- Verify: row counts match expected, amounts correct, no duplicates on re-upload

## Deployment Considerations

### Railway Environment Variables

No new secrets required. Existing setup:
- `SUPABASE_URL` ✓
- `SUPABASE_ANON_KEY` ✓
- `DATABASE_URL` (if direct Postgres connection needed)

### Vercel (Frontend)

No frontend changes in Phase 5 (raw endpoints only). Phase 6 will add PWA uploader.

### Supabase Migrations

Run in this order:
1. Add `external_reference_id` column to `erp_journal_entries`
2. Add `source` + `uploaded_at` columns to `erp_journal_entries`
3. Add `UNIQUE` constraint on `(tenant_id, external_reference_id, transaction_date)`
4. Add `CHECK` constraints on amounts in `erp_journal_lines`

**Migration files:** `apps/backend/migrations/` (use Supabase CLI format)

## Success Metrics (Stage 11 Validation)

- [ ] `dian_xml_documents` has ≥ 7 rows (1 week of Contexia invoices)
- [ ] `erp_journal_entries` has ≥ 20 rows (1 week of GL entries)
- [ ] `erp_journal_lines` has ≥ 50 rows (detail lines)
- [ ] No duplicates on re-upload (idempotency verified)
- [ ] `approval_queue` has 0-5 entries (minor anomalies, not systematic)
- [ ] API response times: < 500ms for XML upload, < 2s for CSV upload
- [ ] Admin can execute curl commands without debugging

## Open Questions → Design Review

1. **Siigo CSV format** — do we have a sample export? (Required to build parser)
2. **Chart of Accounts** — does `erp_chart_of_accounts` table exist? How to validate codes?
3. **HITL approval workflow** — who reviews `approval_queue` entries? Same Hermes Workspace or separate?
4. **Rollback plan** — if data import is bad, can admin delete batch and re-import? Or manual SQL?

---

## Next Step

→ Confirm design decisions above, then proceed to **tasks.md** with Stage 11 deployment tasks.
