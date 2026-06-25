# Admin Runbook: Shadow GL Real Data Ingestion (Cliente Cero)

**Audience:** Contexia admin + operations  
**Purpose:** Daily upload of Contexia's accounting data (XML DIAN + CSV Siigo)  
**SLA:** Data from previous business day available before 9am  
**Updated:** 2026-06-25

---

## Quick Start

### What to Upload Daily

1. **XML DIAN Invoices** — From DIAN portal exports (UBL 2.1 format)
2. **Siigo Journal Export** — CSV from Siigo accounting software

### Upload Methods

#### Option A: curl (Simple, Recommended for Manual)

**Upload XML:**
```bash
curl -X POST \
  -H "Content-Type: application/xml" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/dian-xml/ingest \
  --data @factura_20260625.xml
```

**Upload CSV:**
```bash
curl -X POST \
  -H "Content-Type: text/csv" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/shadow-gl/siigo-csv/ingest \
  --data @siigo_journal_20260625.csv
```

#### Option B: Script (For Automation)

Create `upload_daily.sh`:
```bash
#!/bin/bash
set -e

BACKEND_URL="https://antigravity-app-production-175a.up.railway.app"
DIAN_FOLDER="/home/admin/exports/dian"
SIIGO_FOLDER="/home/admin/exports/siigo"

# Upload XML files from DIAN
for xml in "$DIAN_FOLDER"/*.xml; do
  echo "Uploading $xml..."
  curl -X POST -H "Content-Type: application/xml" \
    "$BACKEND_URL/api/v1/shadow-gl/dian-xml/ingest" \
    --data @"$xml"
done

# Upload CSV from Siigo
if [ -f "$SIIGO_FOLDER/journal.csv" ]; then
  echo "Uploading Siigo journal..."
  curl -X POST -H "Content-Type: text/csv" \
    "$BACKEND_URL/api/v1/shadow-gl/siigo-csv/ingest" \
    --data @"$SIIGO_FOLDER/journal.csv"
fi

echo "All uploads completed."
```

---

## Daily Checklist

- [ ] **7:00am** — Retrieve DIAN XML exports from DIAN portal
- [ ] **7:30am** — Export Siigo journal to CSV (Reports → Journal → Download)
- [ ] **8:00am** — Upload XML via curl or script
- [ ] **8:15am** — Upload CSV via curl or script
- [ ] **8:30am** — Verify responses (see below)
- [ ] **9:00am** — SLA deadline (data must be available)

---

## Expected Responses

### Success Response (XML)

```json
{
  "success": true,
  "cufe": "xyz123-abc456-def789",
  "document_type": "invoice",
  "error": ""
}
```

### Success Response (CSV)

```json
{
  "success": true,
  "row_count": 15,
  "date_range": "2026-06-24..2026-06-25",
  "error": ""
}
```

### Error Response

```json
{
  "error": "Malformed XML: unclosed element at line 15"
}
```

---

## Troubleshooting

### "Request body must contain XML/CSV"
**Cause:** Empty file uploaded  
**Fix:** Verify file is not empty and retry

### "Missing required field(s): CUFE"
**Cause:** XML is incomplete (missing CUFE field)  
**Fix:** Contact DIAN for corrected invoice

### "Entry ... imbalanced (debit=X, credit=Y)"
**Cause:** CSV has unmatched debit/credit amounts  
**Fix:** Verify the CSV in Siigo, fix the discrepancy, re-export

### Endpoint Not Responding
**Cause:** Backend down or network issue  
**Fix:** Check Railway dashboard or verify internet connection

---

## Data Flow

```
DIAN Portal
    ↓ (Download XML)
    ↓
Admin Workstation
    ↓ (curl upload)
    ↓
POST /api/v1/shadow-gl/dian-xml/ingest
    ↓
Supabase: dian_xml_documents table
    ↓
Shadow GL ready for reconciliation
```

```
Siigo Accounting
    ↓ (Export CSV)
    ↓
Admin Workstation
    ↓ (curl upload)
    ↓
POST /api/v1/shadow-gl/siigo-csv/ingest
    ↓
Supabase: erp_journal_entries + erp_journal_lines
    ↓
Shadow GL ready for analysis
```

---

## Rollback (If Needed)

### Delete Recent Imports (Last 24 Hours)

If bad data was uploaded and needs to be removed:

```bash
# Contact admin with access to Supabase
# SQL to delete entries uploaded in last 24 hours:

DELETE FROM erp_journal_lines 
WHERE entry_id IN (
  SELECT id FROM erp_journal_entries 
  WHERE uploaded_at > NOW() - INTERVAL '1 day'
);

DELETE FROM erp_journal_entries 
WHERE uploaded_at > NOW() - INTERVAL '1 day';

DELETE FROM dian_xml_documents 
WHERE created_at > NOW() - INTERVAL '1 day';
```

---

## SLA Monitoring

Admin should verify:
- ✅ Data appears in tables before 9:00am
- ✅ Row counts match uploaded items (idempotency check)
- ✅ No duplicate entries on re-upload
- ✅ Error messages are clear if upload fails

---

## Support

**Questions?** Contact: operations@contexia.co (pending formal setup)  
**Monitoring:** Check Railway logs at https://railway.app/[project]/logs
