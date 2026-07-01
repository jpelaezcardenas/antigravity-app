# Phase 6 Stage 10: E2E Testing Scenario

## Prerequisites

- ✅ Hermes Workspace running on localhost:3000
- ✅ Hermes Gateway running on localhost:8642
- ✅ antigravity-app backend running (FastAPI)
- ✅ Supabase available

## Test Case 1: CSV with Imbalance → Approval → Persistence

### Step 1: Create Imbalanced CSV

This CSV has entries that don't balance (total debits ≠ credits):

```csv
Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,100.00,
2026-06-25,TX-001,4100,Sales Revenue,,75.00
2026-06-25,TX-002,1100,Sales Receivable,150.00,
2026-06-25,TX-002,4100,Sales Revenue,,100.00
```

**Expected:** Debits = 250.00, Credits = 175.00 → Imbalance detected

### Step 2: Upload to Backend

```bash
curl -X POST http://localhost:8000/api/v1/shadow-gl/siigo-csv/ingest \
  -H "Content-Type: text/plain" \
  --data-binary @imbalanced.csv
```

**Expected Response (400):**
```json
{
  "detail": "Accounting entries imbalanced: total_debits=25000 total_credits=17500"
}
```

### Step 3: Verify approval_queue Entry

Check Supabase:

```sql
SELECT id, tenant_id, status, payload->>'raw_input' as has_raw_input, created_at
FROM approval_queue
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 1;
```

**Expected:** One row with `status='pending'`, `payload` contains the CSV

### Step 4: Hermes UI Approval

1. Open Hermes Workspace: http://localhost:3000
2. Navigate to Approval Queue
3. Find the pending approval with the imbalanced CSV
4. Review the transaction summary
5. Click **APPROVE**

**Expected:** Hermes sends approval_decision with `status='approved'`, backend receives it

### Step 5: Verify Persistence

Check that entries were persisted:

```sql
SELECT id, external_reference_id, entry_date, status
FROM erp_journal_entries
WHERE external_reference_id IN ('TX-001', 'TX-002')
ORDER BY created_at DESC;
```

**Expected:** 2 rows (one per transaction)

```sql
SELECT entry_id, account_code, debit_cents, credit_cents
FROM erp_journal_lines
WHERE entry_id IN (SELECT id FROM erp_journal_entries WHERE external_reference_id IN ('TX-001', 'TX-002'))
ORDER BY entry_id, line_seq;
```

**Expected:** 4 rows (2 lines per transaction)

---

## Test Case 2: CSV with Rejection

Same as Test Case 1, but:

1. In Hermes UI, click **REJECT** instead of APPROVE
2. Verify approval_queue.status = 'rejected'
3. Verify NO entries persisted to erp_journal_entries
4. Check logs for rejection reason

---

## Files for Testing

### imbalanced.csv

Save this file locally to use in curl command:

```csv
Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,100.00,
2026-06-25,TX-001,4100,Sales Revenue,,75.00
2026-06-25,TX-002,1100,Sales Receivable,150.00,
2026-06-25,TX-002,4100,Sales Revenue,,100.00
```

### balanced.csv (for validation)

```csv
Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-003,1100,Sales Receivable,100.00,
2026-06-25,TX-003,4100,Sales Revenue,,100.00
```

---

## Checklist

- [ ] Hermes services running
- [ ] Backend running and healthy
- [ ] Test imbalanced.csv uploaded → approval_queue created
- [ ] Hermes UI shows pending approval
- [ ] APPROVED → entries persisted to erp_journal_entries
- [ ] REJECTED → no entries persisted, reason logged
- [ ] Full audit trail visible in approval_queue table

---

## Known Issues to Watch

1. **WebSocket timeout**: If Hermes doesn't send decision within 30s, check gateway logs
2. **CSV parsing edge cases**: Ensure date format is exactly `YYYY-MM-DD`
3. **Tenant context**: Verify tenant_id in approval_queue matches backend tenant

