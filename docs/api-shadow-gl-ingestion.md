# Shadow GL Ingestion API Documentation

**Base URL:** `https://antigravity-app-production-175a.up.railway.app`  
**Version:** 1.0 (Phase 5 — Cliente Cero MVP)  
**Last Updated:** 2026-06-25

---

## Endpoints

### 1. Ingest DIAN UBL 2.1 XML Invoice

#### Request

```http
POST /api/v1/shadow-gl/dian-xml/ingest
Content-Type: application/xml

<?xml version="1.0"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  ...
</Invoice>
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| body | XML | Yes | Raw DIAN UBL 2.1 XML document (invoice, credit note, or debit note) |

#### Response: 200 OK

```json
{
  "success": true,
  "cufe": "xyz123abc456def789",
  "document_type": "invoice",
  "error": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Always `true` on 200 response |
| cufe | string | CUFE identifier (globally unique per DIAN) |
| document_type | string | One of: `invoice`, `credit_note`, `debit_note` |
| error | string | Empty on success |

#### Response: 400 Bad Request

```json
{
  "error": "Malformed XML: unclosed element at line 15"
}
```

#### Idempotency

- **Key:** `(tenant_id, cufe)`
- **Behavior:** Re-uploading the same CUFE returns 200 with existing data
- **Example:** Upload invoice ABC123 twice → second upload returns same CUFE, no duplicate row

#### Example: curl

```bash
curl -X POST \
  -H "Content-Type: application/xml" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/dian-xml/ingest \
  --data @invoice_20260625.xml
```

#### Valid CUFE Extraction

The endpoint extracts:
- `cbc:UUID` (CUFE — globally unique)
- `cbc:IssueDate` (ISO 8601)
- Supplier NIT (issuer)
- Customer NIT (receiver)
- Total payable amount
- Tax amount
- Withholding amount
- Currency code (default: COP)

---

### 2. Ingest Siigo CSV Journal Export

#### Request

```http
POST /api/v1/shadow-gl/siigo-csv/ingest
Content-Type: text/csv

transaction_date,account_code,account_name,debit_amount,credit_amount,memo,external_reference_id,currency_code
2026-06-25,1105,Caja General,850000.00,,Payment received,DOC-001,COP
2026-06-25,4105,Revenue,,850000.00,Service income,DOC-001,COP
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| body | CSV | Yes | Siigo journal export (comma-separated, with headers) |

#### CSV Format Requirements

```
Column Name              | Type    | Required | Notes
------------------------|---------|----------|-------------------------------------------
transaction_date        | string  | Yes      | ISO 8601 format (YYYY-MM-DD)
account_code            | string  | Yes      | GL account number (e.g., "1105", "4105")
account_name            | string  | Optional | Description (informational only)
debit_amount            | numeric | Yes*     | Decimal (e.g., "850000.00"); empty if 0
credit_amount           | numeric | Yes*     | Decimal (e.g., "850000.00"); empty if 0
memo                    | string  | Yes      | Transaction description
external_reference_id   | string  | Yes      | Siigo voucher/document ID (e.g., "DOC-001")
currency_code           | string  | Optional | ISO 4217 (default: "COP"); supports USD, EUR, etc.

* At least one must be non-empty (debit XOR credit per line)
```

#### Response: 200 OK

```json
{
  "success": true,
  "row_count": 15,
  "date_range": "2026-06-24..2026-06-25",
  "error": ""
}
```

| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Always `true` on 200 response |
| row_count | integer | Number of journal entries created |
| date_range | string | Date span of imported transactions (e.g., "2026-06-24..2026-06-25") |
| error | string | Empty on success |

#### Response: 400 Bad Request

```json
{
  "error": "Entry DOC-001: imbalanced (debit=850000, credit=750000)"
}
```

Common error messages:
- `"Missing required column(s): debit_amount, credit_amount"`
- `"Row 3: Invalid date format '25/06/2026'; expected ISO 8601 (YYYY-MM-DD)"`
- `"Row 5: Invalid monetary amount: 'not-a-number'"`
- `"Entry DOC-001: imbalanced (debit=X, credit=Y)"` — SUM(debit) ≠ SUM(credit)

#### Idempotency

- **Key:** `(tenant_id, external_reference_id, transaction_date)`
- **Behavior:** Re-uploading the same batch returns 200 with same row count
- **Example:** Upload CSV with DOC-001 on 2026-06-25 twice → second upload returns same row_count, no duplicates

#### Example: curl

```bash
curl -X POST \
  -H "Content-Type: text/csv" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
  --data @siigo_journal_20260625.csv
```

#### Validation Rules

1. **CSV Structure:** Required headers must exist; order doesn't matter
2. **Date Format:** Must be valid ISO 8601 (YYYY-MM-DD)
3. **Amounts:** Converted to integer cents (100 COP = 10000 minor units)
4. **Double-Entry:** Per transaction (external_reference_id), SUM(debit) MUST equal SUM(credit)
5. **Debit/Credit:** Both cannot be empty; at least one must be non-zero

---

## Data Storage

### DIAN XML Documents
**Table:** `dian_xml_documents`

```sql
SELECT id, cufe, document_type, issuer_nit, receiver_nit, 
       total_amount_minor, tax_amount_minor, currency_code, 
       created_at, raw_xml
FROM dian_xml_documents
WHERE tenant_id = '<cliente_cero_id>'
ORDER BY created_at DESC;
```

### Siigo Journal Entries
**Table:** `erp_journal_entries`

```sql
SELECT id, external_reference_id, entry_date, memo, 
       source, uploaded_at
FROM erp_journal_entries
WHERE tenant_id = '<cliente_cero_id>'
ORDER BY entry_date DESC;
```

**Table:** `erp_journal_lines`

```sql
SELECT id, entry_id, account_code, debit_minor, credit_minor, 
       currency_code, memo, created_at
FROM erp_journal_lines
WHERE tenant_id = '<cliente_cero_id>'
ORDER BY created_at DESC;
```

---

## Error Handling

### Parsing Errors (400)
- Malformed XML (missing namespace, unclosed tags)
- Missing CSV headers
- Invalid date formats
- Non-numeric amounts

### Validation Errors (400)
- Required fields missing
- Accounting imbalance (debit ≠ credit)
- Negative amounts
- Invalid account codes (future: when chart of accounts is available)

### Server Errors (500)
- Database connection failures
- Unexpected exceptions

---

## Rate Limits

- No rate limiting implemented (Phase 5)
- Recommended: Max 1 upload per 10 seconds per tenant

---

## Authentication

- **Current:** None (Cliente Cero only, internal network)
- **Phase 6:** JWT-based multi-tenant routing
- **Future:** API key per tenant for external integrations

---

## Examples

### Example 1: Upload XML DIAN Invoice

```bash
#!/bin/bash
curl -s -X POST \
  -H "Content-Type: application/xml" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/dian-xml/ingest \
  --data @factura_20260625.xml | jq .
```

Output:
```json
{
  "success": true,
  "cufe": "abc123def456",
  "document_type": "invoice",
  "error": ""
}
```

### Example 2: Upload Siigo CSV Export

```bash
#!/bin/bash
curl -s -X POST \
  -H "Content-Type: text/csv" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
  --data @siigo_2026-06-25.csv | jq .
```

Output:
```json
{
  "success": true,
  "row_count": 12,
  "date_range": "2026-06-25..2026-06-25",
  "error": ""
}
```

### Example 3: Handle Error (Malformed CSV)

```bash
#!/bin/bash
response=$(curl -s -X POST \
  -H "Content-Type: text/csv" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
  --data @bad_export.csv)

if echo "$response" | jq -e '.error' > /dev/null; then
  echo "Upload failed: $(echo "$response" | jq -r '.error')"
  exit 1
fi

echo "Upload succeeded: $(echo "$response" | jq -r '.row_count') rows"
```

---

## Monitoring

### Health Check

```bash
curl -s https://antigravity-app-production-175a.up.railway.app/api/v1/health | jq .
```

Expected response:
```json
{
  "status": "healthy"
}
```

### Logs

Railway dashboard: https://railway.app/[project]/logs

Filter by:
- `shadow_gl` (keyword)
- `dian-xml/ingest` or `siigo-csv/ingest` (endpoint)
- Timerange (last 24 hours, etc.)

---

## Support & Escalation

| Issue | Contact | Resolution |
|-------|---------|-----------|
| "Endpoint not responding" | Ops | Check Railway status + logs |
| "Validation error" | Admin/Accounting | Review CSV/XML format |
| "Duplicate detection not working" | Engineering | Check UNIQUE constraint in DB |
| "Data not visible 9am" | Admin/Ops | Verify uploads completed + no errors |

---

## Changelog

### v1.0 (2026-06-25)
- Initial release (Phase 5)
- DIAN XML ingestion (UBL 2.1)
- Siigo CSV ingestion (double-entry)
- Idempotency via CUFE and external_reference_id
- Cliente Cero only (multi-tenant wiring Phase 6)
