# Phase 7: Automated Approval Rules — Design Document

**Status:** Design  
**Architecture Decision:** In-process rule engine (heuristic-based)

---

## 1. Data Model

### approval_queue Extension

```sql
ALTER TABLE approval_queue ADD COLUMN (
  auto_approved boolean DEFAULT false,
  rule_applied varchar(100),
  confidence_score numeric(3, 2),
  rule_data jsonb
);
```

**Examples:**

```json
{
  "auto_approved": true,
  "rule_applied": "RECURRING_TRANSACTION",
  "confidence_score": 0.95,
  "rule_data": {
    "matched_entries": [
      "entry-id-1",
      "entry-id-2",
      "entry-id-3"
    ],
    "variance": 0.0,
    "last_occurrence": "2026-06-25T10:00:00Z"
  }
}
```

### approval_rules Table (Admin Configuration)

```sql
CREATE TABLE approval_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid REFERENCES tenants(id),
  rule_name varchar(100) NOT NULL,
  rule_type varchar(50) NOT NULL, -- "RECURRING", "VENDOR", "MICRO"
  enabled boolean DEFAULT true,
  min_confidence_score numeric(3, 2) DEFAULT 0.85,
  rule_config jsonb, -- Rule-specific config
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now(),
  created_by uuid REFERENCES auth.users(id)
);
```

---

## 2. Rule Engine

### Interface

```python
async def evaluate_auto_approval_rules(
    tenant_id: str,
    entry: JournalEntry,
    history: List[JournalEntry]
) -> ApprovalDecision:
    """
    Evaluate entry against heuristic rules.
    
    Returns:
        ApprovalDecision(
            approved: bool,
            rule_id: str,
            rule_name: str,
            confidence: float,
            reason: str
        )
    """
```

### Rules

#### Rule 1: Recurring Transaction

**Logic:**
```
1. Query last 3 entries for same (tenant_id, account_code)
2. Compare current entry amount/date pattern
3. If all 3 match within variance threshold:
   - confidence = 0.95
   - approve = true
```

**Code:**
```python
async def _check_recurring_rule(
    tenant_id: str,
    entry: JournalEntry,
    history: List[JournalEntry]
) -> Optional[ApprovalDecision]:
    """
    Detect recurring transactions (same amount, vendor, account).
    """
    if len(history) < 3:
        return None  # Not enough history
    
    last_3 = history[-3:]
    
    # Check if all 3 have same amount
    amounts = [e.amount_cents for e in last_3]
    if amounts[0] == amounts[1] == amounts[2]:
        variance = 0.0
    else:
        variance = (max(amounts) - min(amounts)) / amounts[0]
    
    # Check if current entry matches pattern
    if abs(entry.amount_cents - amounts[0]) / amounts[0] < 0.02:  # 2% tolerance
        return ApprovalDecision(
            approved=True,
            rule_id="RECURRING_TRANSACTION",
            rule_name="Recurring Transaction Match",
            confidence=0.95,
            reason=f"Matched last 3 entries (variance={variance:.2%})"
        )
    
    return None
```

#### Rule 2: Known Vendor

**Logic:**
```
1. Query vendor_whitelist for entry.vendor_code
2. Check if amount ±10% of average_amount
3. If match:
   - confidence = 0.90
   - approve = true
```

**Data:**
```sql
CREATE TABLE vendor_whitelist (
  id uuid PRIMARY KEY,
  tenant_id uuid,
  vendor_code varchar(100),
  vendor_name varchar(255),
  avg_amount_cents bigint,
  tolerance_percent numeric(3, 2) DEFAULT 0.10,
  enabled boolean DEFAULT true,
  created_at timestamp,
  updated_at timestamp
);
```

#### Rule 3: Micro Transaction

**Logic:**
```
1. If amount < 10 COP (1000000 cents)
2. AND vendor_code matches any vendor
3. Then:
   - confidence = 0.85
   - approve = true
```

---

## 3. Workflow

### Happy Path: Auto-Approval

```
POST /api/v1/shadow-gl/siigo-csv/ingest
    ↓
Parse CSV
    ↓
For each entry:
    ├─ Balanced? YES → persist to erp_journal_entries
    │
    └─ Balanced? NO
       ├─ _evaluate_auto_approval_rules()
       │   ├─ Check RECURRING_TRANSACTION
       │   ├─ Check KNOWN_VENDOR
       │   ├─ Check MICRO_TRANSACTION
       │   └─ Return: (approved, confidence, reason)
       │
       ├─ If approved ≥ min_confidence:
       │   ├─ Persist to erp_journal_entries
       │   ├─ Update approval_queue:
       │   │  - auto_approved = true
       │   │  - rule_applied = "RECURRING_TRANSACTION"
       │   │  - confidence_score = 0.95
       │   │
       │   └─ Return 200 OK
       │
       └─ Else:
          ├─ Create approval_queue (status='pending')
          ├─ Send to Hermes
          └─ Return 202 Accepted
```

### Fallback: Manual Review

```
If auto_approval fails (confidence < threshold):
    ├─ Create approval_queue
    ├─ Set status = 'pending'
    ├─ Send approval_request to Hermes
    └─ (Continue as Phase 6 flow)
```

---

## 4. Configuration

### approval_rules Presets

```json
{
  "RECURRING_TRANSACTION": {
    "enabled": true,
    "min_confidence": 0.95,
    "min_history": 3,
    "variance_tolerance": 0.02
  },
  "KNOWN_VENDOR": {
    "enabled": true,
    "min_confidence": 0.90,
    "amount_tolerance": 0.10
  },
  "MICRO_TRANSACTION": {
    "enabled": true,
    "min_confidence": 0.85,
    "threshold_cents": 1000000
  }
}
```

### Per-Tenant Customization

Admin can adjust thresholds:
```sql
UPDATE approval_rules
SET min_confidence_score = 0.92
WHERE tenant_id = 'abc-def' AND rule_name = 'RECURRING_TRANSACTION';
```

---

## 5. Monitoring

### Metrics to Track

1. **Auto-Approval Rate**
   ```
   metric: auto_approval_rate
   value: (auto_approved_count / total_entries) * 100
   labels: {tenant_id, rule_id}
   ```

2. **Rule Effectiveness**
   ```
   metric: rule_confidence_distribution
   value: histogram of confidence scores
   labels: {rule_id, tenant_id}
   ```

3. **False Positive Rate** (requires user feedback)
   ```
   metric: auto_approval_reverted
   value: count of auto-approved entries user later rejected
   labels: {rule_id, tenant_id}
   ```

### Dashboard Queries

```sql
-- Auto-approval rate by rule
SELECT 
  rule_applied,
  COUNT(*) as count,
  AVG(confidence_score) as avg_confidence,
  (COUNT(*) FILTER (WHERE auto_approved) / COUNT(*)) * 100 as approval_rate
FROM approval_queue
WHERE auto_approved = true
GROUP BY rule_applied
ORDER BY count DESC;

-- Confidence score distribution
SELECT 
  rule_applied,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY confidence_score) as p50,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY confidence_score) as p95
FROM approval_queue
WHERE auto_approved = true
GROUP BY rule_applied;
```

---

## 6. Security & Audit

### Audit Trail

```sql
INSERT INTO audit_log (
  tenant_id,
  action,
  entity_type,
  entity_id,
  old_value,
  new_value,
  reason
) VALUES (
  'tenant-123',
  'auto_approve',
  'journal_entry',
  'entry-456',
  NULL,
  '{...entry data...}',
  'Rule: RECURRING_TRANSACTION, confidence: 0.95'
);
```

### RLS Policy

```sql
-- Only tenant admins can view approval_rules
CREATE POLICY approval_rules_view_policy ON approval_rules
  FOR SELECT USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles 
      WHERE tenant_id = approval_rules.tenant_id 
      AND role_name = 'admin'
    )
  );
```

---

## 7. API Changes

### Response Format

**Before (Phase 6):**
```json
{
  "success": true,
  "row_count": 2,
  "date_range": "2026-06-25"
}
```

**After (Phase 7):**
```json
{
  "success": true,
  "row_count": 2,
  "date_range": "2026-06-25",
  "auto_approved_count": 1,
  "pending_review_count": 1,
  "summary": {
    "entries": [
      {
        "reference": "TX-001",
        "status": "auto_approved",
        "rule": "RECURRING_TRANSACTION",
        "confidence": 0.95
      },
      {
        "reference": "TX-002",
        "status": "pending_review",
        "queue_id": "queue-123"
      }
    ]
  }
}
```

---

## 8. Testing Strategy

### Unit Tests

1. `test_recurring_rule_matches` ✅
2. `test_recurring_rule_insufficient_history` ✅
3. `test_vendor_rule_matches` ✅
4. `test_micro_rule_matches` ✅
5. `test_confidence_threshold_rejected` ✅

### Integration Tests

1. `test_csv_with_recurring_entry_auto_approves` ✅
2. `test_csv_with_mixed_entries_partial_approval` ✅
3. `test_fallback_to_manual_review_if_no_rule_match` ✅

### E2E Tests

1. Upload CSV with recurring entry → auto-approve (no Hermes) ✅
2. Query erp_journal_entries → entry exists (verify persistence) ✅
3. Query approval_queue → rule_applied + confidence populated ✅

---

## 9. Rollback Plan

If auto-approval causes issues:

1. **Disable rule via admin UI** (future)
   ```sql
   UPDATE approval_rules SET enabled = false WHERE rule_name = 'RECURRING_TRANSACTION';
   ```

2. **Lower confidence threshold** (if false positives)
   ```sql
   UPDATE approval_rules SET min_confidence_score = 0.99 WHERE rule_name = 'RECURRING_TRANSACTION';
   ```

3. **Full rollback** (revert commits)
   ```bash
   git revert <phase-7-commits>
   git push
   ```

All auto-approved entries remain audited in approval_queue.

---

## 10. Next Steps

➡️ **Proceed to Implementation** (tasks.md)

