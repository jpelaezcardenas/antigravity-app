# OpenSpec Change: Phase 7 — Automated Approval Rules

**Status:** Proposal  
**Phase:** 7  
**Depends On:** Phase 6 (HITL Workflows) ✅  
**Timeline:** 5-7 days  

---

## Problem Statement

**Current State (Phase 6):**
- All imbalanced accounting entries require human approval
- Every error → Hermes review queue
- Manual approval bottleneck (no auto-approval even for low-risk entries)

**User Pain Point:**
Accountants waste time reviewing obviously-correct entries (e.g., recurring transactions, known vendors, micro-transactions).

**Business Impact:**
- ❌ Slow approval cycle (hours/days)
- ❌ Inconsistent decision-making
- ❌ Hermes queue accumulates
- ❌ No audit trail for auto-approved decisions

---

## Solution Overview

**Automated Approval Rules (ML + Heuristics)**

```
Imbalanced entry detected
    ↓
[Rule Engine] — Apply heuristic rules
    ├─ If: Recurring transaction + balance matches history
    │  └─ Action: AUTO-APPROVE (confidence ≥ 95%)
    │
    ├─ If: Known vendor + amount within tolerance
    │  └─ Action: AUTO-APPROVE (confidence ≥ 90%)
    │
    ├─ If: Micro-transaction (< 10 COP) + vendor matches
    │  └─ Action: AUTO-APPROVE (confidence ≥ 85%)
    │
    └─ Else
       └─ Route to Hermes (human review)
    ↓
Persist or Queue
    ↓
Audit trail: {rule_id, confidence_score, reason}
```

---

## Key Features

### 1. Rule Engine (Heuristic-based)

**Rules to implement:**

| Rule | Condition | Confidence | Action |
|------|-----------|------------|--------|
| **Recurring** | Exact match to last 3 transactions | ≥95% | AUTO-APPROVE |
| **Known Vendor** | Vendor in whitelist + amount ±10% | ≥90% | AUTO-APPROVE |
| **Micro** | Amount < 10 COP + vendor match | ≥85% | AUTO-APPROVE |
| **Balance Mismatch** | Difference > 50% | <70% | HUMAN_REVIEW |

### 2. Audit Trail

```sql
approval_queue.auto_approved = true
approval_queue.rule_applied = "RECURRING_TRANSACTION"
approval_queue.confidence_score = 0.95
approval_queue.reason = "Matched last 3 recurring transactions"
```

### 3. Admin Dashboard (Future)

- View auto-approval metrics
- Adjust rule thresholds
- Audit decisions
- Override auto-approvals

---

## Acceptance Criteria

- ✅ Heuristic rules engine implemented
- ✅ Recurring transaction detection
- ✅ Known vendor whitelist + matching
- ✅ Confidence scoring (0-100%)
- ✅ Auto-approval logic (approve → persist, skip Hermes)
- ✅ Audit trail with rule_id + confidence
- ✅ Fallback to human review if confidence < threshold
- ✅ E2E test: recurring entry auto-approves without Hermes
- ✅ Monitoring: track auto-approval rate + success

---

## Architecture Decision

### Option A: In-Process Rule Engine (RECOMMENDED)

```
Backend receives imbalanced entry
    ↓
_evaluate_auto_approval_rules(entry) → bool
    │
    ├─ Check recurring: query last 3 entries
    ├─ Check vendor: query vendor_whitelist
    ├─ Check amount: compare against thresholds
    └─ Return: (approved, rule_id, confidence)
    ↓
If approved: persist directly to erp_journal_entries
If not: create approval_queue for human review
    ↓
Audit log: {entry_id, rule_id, confidence, timestamp}
```

**Pros:** No network calls, deterministic, auditable  
**Cons:** Rule logic couples to backend

### Option B: External ML Service

```
Backend → ML Service (OpenRouter/Claude API)
    ↓
"Should this entry auto-approve? [history, entry]"
    ↓
Model response: {approved: bool, confidence: float, reason: str}
```

**Pros:** Flexible, ML-driven, easy to update  
**Cons:** Latency, cost, external dependency

**Decision:** **Option A** (faster, deterministic, cost-effective)

---

## Phase Breakdown

| Stage | Task | Duration |
|-------|------|----------|
| **1** | Rule engine design + heuristics | 1 day |
| **2** | Implement recurring detection | 1 day |
| **3** | Implement vendor whitelist + matching | 1 day |
| **4** | Confidence scoring + thresholds | 1 day |
| **5** | Integration with approval_queue | 1 day |
| **6** | Unit + E2E tests | 1 day |
| **7** | Manual testing + tuning | 1 day |
| **8** | Deployment + monitoring | 0.5 day |
| **9** | Metrics dashboard (optional) | 1 day |

**Total:** ~7 days

---

## Success Metrics

**By End of Phase 7:**

- Auto-approval rate: 40-60% (target)
- Human review time: -50% (Phase 6 baseline)
- False positives: <2% (confidence threshold tuning)
- Audit completeness: 100% (all decisions logged)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Rule too permissive (auto-approve bad entry) | High | Low confidence threshold (≥85%) + audit trail |
| Rule too strict (no auto-approval) | Medium | Start with high thresholds, lower over time |
| Vendor whitelist maintenance | Medium | Admin UI to manage (Phase 8) |
| History data incomplete | Low | Fallback to manual review if no history |

---

## Stakeholder Impact

**For Accountants:**
- Faster approval cycles (auto for routine entries)
- Manual review only for unusual transactions
- Full audit trail (why was it auto-approved?)

**For System:**
- Reduced Hermes queue pressure
- Deterministic decision-making
- Measurable performance improvement

---

## References

- **Phase 6:** HITL Workflows (approval_queue schema)
- **Depends On:** approval_queue table (Phase 6 ✅)
- **Data:** erp_journal_entries, vendor history

---

## Next Step

➡️ **Proceed to Design Phase** (design.md)

