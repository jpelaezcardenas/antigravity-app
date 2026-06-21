# T5: Centinela Rules Engine E2E Tests

**Objective:** Validate all 10 Centinela fiscal rules against realistic Colombian tax scenarios.

**Endpoint:** POST /api/v1/centinela/evaluate

**Status:** Ready for testing (routing fixed 2026-05-24)

---

## Test Cases

### Rule 1: UVT Excedido (R001) — WARNING
**Trigger:** Annual revenue exceeds 160 UVT limit for Régimen Simple
```json
{
  "company_id": "test-r001",
  "financial_data": {
    "regimen": "Régimen Simple",
    "annual_revenue": 10000000
  },
  "save_alerts": false
}
```
**Expected:** severity="warning", rule_id="R001", evidence shows excess amount

---

### Rule 2: Retención No Pagada (R002) — CRITICAL
**Trigger:** Retention obligations not met
```json
{
  "company_id": "test-r002",
  "financial_data": {
    "regimen": "Régimen Común",
    "annual_revenue": 50000000,
    "retention_due": 5000000,
    "retention_paid": 0
  },
  "save_alerts": false
}
```
**Expected:** severity="critical", rule_id="R002"

---

### Rule 3: Facturación Irregular (R003) — WARNING
**Trigger:** Invoice patterns show irregularities
```json
{
  "company_id": "test-r003",
  "financial_data": {
    "regimen": "Régimen Común",
    "total_invoices_issued": 100,
    "invoices_cancelled": 45,
    "cancellation_rate": 0.45
  },
  "save_alerts": false
}
```
**Expected:** severity="warning", rule_id="R003"

---

### Rule 4: Cambio de Régimen No Reportado (R004) — CRITICAL
**Trigger:** Regime change detected without DIAN declaration
```json
{
  "company_id": "test-r004",
  "financial_data": {
    "regimen": "Régimen Común",
    "previous_regimen": "Régimen Simple",
    "regime_change_date": "2026-03-01",
    "dian_notification_date": null
  },
  "save_alerts": false
}
```
**Expected:** severity="critical", rule_id="R004"

---

### Rule 5: Provisiones Insuficientes (R005) — WARNING
**Trigger:** Provisions don't match obligations
```json
{
  "company_id": "test-r005",
  "financial_data": {
    "regimen": "Régimen Común",
    "annual_revenue": 100000000,
    "provisions_amount": 5000000,
    "minimum_required": 15000000
  },
  "save_alerts": false
}
```
**Expected:** severity="warning", rule_id="R005"

---

### Rule 6: Margen Bruta Sospechoso (R006) — WARNING
**Trigger:** Gross margin outside normal range
```json
{
  "company_id": "test-r006",
  "financial_data": {
    "regimen": "Régimen Común",
    "sales": 100000000,
    "cost_of_sales": 95000000,
    "gross_margin": 0.05
  },
  "save_alerts": false
}
```
**Expected:** severity="warning", rule_id="R006"

---

### Rule 7: Operación Relacionada No Reportada (R007) — CRITICAL
**Trigger:** Related party transaction not disclosed
```json
{
  "company_id": "test-r007",
  "financial_data": {
    "regimen": "Régimen Común",
    "related_party_transactions": [
      {"counterparty": "Empresa Hermana S.A.S", "amount": 50000000}
    ],
    "disclosed_related_parties": []
  },
  "save_alerts": false
}
```
**Expected:** severity="critical", rule_id="R007"

---

### Rule 8: Activo Sobrevaluado (R008) — WARNING
**Trigger:** Asset value exceeds reasonable threshold
```json
{
  "company_id": "test-r008",
  "financial_data": {
    "regimen": "Régimen Común",
    "total_assets": 500000000,
    "goodwill": 300000000,
    "goodwill_ratio": 0.60
  },
  "save_alerts": false
}
```
**Expected:** severity="warning", rule_id="R008"

---

### Rule 9: Deuda DIAN (R009) — CRITICAL
**Trigger:** Outstanding tax debt with DIAN
```json
{
  "company_id": "test-r009",
  "financial_data": {
    "regimen": "Régimen Común",
    "dian_debt": 10000000,
    "dian_debt_status": "active"
  },
  "save_alerts": false
}
```
**Expected:** severity="critical", rule_id="R009"

---

### Rule 10: Inconsistencia Contable (R010) — CRITICAL
**Trigger:** Accounting mismatch (e.g., VAT)
```json
{
  "company_id": "test-r010",
  "financial_data": {
    "regimen": "Régimen Común",
    "vat_collected": 19000000,
    "vat_paid": 20000000,
    "sales_reported": 100000000,
    "invoices_total": 98000000
  },
  "save_alerts": false
}
```
**Expected:** severity="critical", rule_id="R010"

---

## Batch Test: Multiple Rules Triggered

Test scenario where company triggers multiple rules to verify risk_level calculation:
```json
{
  "company_id": "test-multi",
  "financial_data": {
    "regimen": "Régimen Común",
    "annual_revenue": 100000000,
    "retention_due": 10000000,
    "retention_paid": 0,
    "related_party_transactions": [{"counterparty": "Related Co", "amount": 30000000}],
    "disclosed_related_parties": [],
    "dian_debt": 5000000,
    "dian_debt_status": "active"
  },
  "save_alerts": false
}
```
**Expected:**
- alert_count >= 3
- critical_count >= 2 (R002, R004, R007, R009)
- risk_level = "critical" (2+ critical alerts)

---

## Success Criteria

| Test | Status | Evidence |
|------|--------|----------|
| All 10 rules trigger on matching data | ? | Response contains rule_id R001-R010 |
| Severity levels correct | ? | critical vs warning match specification |
| Risk level calculation | ? | critical_count >= 2 → risk_level="critical" |
| Evidence field populated | ? | evidence shows data that triggered rule |
| save_alerts=true → IDs returned | ? | saved_alert_ids array non-empty |
| save_alerts=false → IDs empty | ? | saved_alert_ids array empty |
| Response time < 5s | ? | latency acceptable for real-time use |

---

## Test Execution

```bash
# Run against staging
STAGING_URL="https://antigravity-app-production-175a.up.railway.app"

# Test each rule
for rule in R001 R002 R003 R004 R005 R006 R007 R008 R009 R010; do
  echo "Testing $rule..."
  curl -X POST "$STAGING_URL/api/v1/centinela/evaluate" \
    -H "Content-Type: application/json" \
    -d "{...rule payload...}" | jq '.alerts[] | select(.rule_id == "'$rule'")'
done
```

---

## Notes
- All tests use save_alerts=false to avoid polluting Supabase during E2E
- For integration tests, set save_alerts=true and verify Supabase alerts table
- Response times should be < 2 seconds per evaluation (currently <1s local)
- Implement batch testing (10+ companies) to verify database performance
