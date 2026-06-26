# Phase 9: Metrics Dashboard — Proposal

**Status:** PROPOSED  
**Date:** 2026-06-26  
**Change ID:** metrics-dashboard-phase9

---

## Problem Statement

Phase 7 (Automated Approval Rules) and Phase 8 (CSV Ingestion) are now live in production, but **we have no visibility into their effectiveness**. Key questions unanswered:

- How many entries are auto-approved per rule (recurring, vendor, micro)?
- What's the false positive rate per rule?
- How many CSV batches are ingested daily?
- What's the error rate for uploads?
- Which vendors appear most frequently?
- Approval cycle time improvement vs. before automation?

**Impact:** Operations team is blind to system performance. Cannot tune rules or prioritize improvements. No data-driven decision-making.

---

## Solution Overview

Build a **Metrics Dashboard** (admin view in PWA) that displays:

1. **Auto-Approval Metrics** (Phase 7)
   - Total auto-approved entries (last 7 days)
   - Breakdown by rule (recurring, vendor, micro)
   - Confidence score distribution
   - False positive rate (human reviews of auto-approved entries)

2. **CSV Ingestion Metrics** (Phase 8)
   - Batches uploaded (last 7 days)
   - Success rate (% completed vs. error)
   - Error summary (top error types)
   - Row count distribution

3. **Approval Queue Health**
   - Queue length (pending reviews)
   - Average review time
   - Approval vs. rejection rate

4. **Account-Level Insights**
   - Most frequent vendors (top 10)
   - Most frequent account codes (top 10)
   - Trend: auto-approval rate over time

---

## Success Criteria

- ✅ Dashboard loads in < 2 seconds
- ✅ Metrics update every 5 minutes (refreshable manually)
- ✅ Charts render correctly for empty data (zero entries)
- ✅ RLS enforced: each tenant sees only their metrics
- ✅ All metrics backed by database queries (no hardcoding)
- ✅ Mobile-responsive (PWA)

---

## Scope & Timeline

**Estimated effort:** 5 stages × 1-2 days = 5-7 days  
**Target completion:** 2026-07-03

### Stage Breakdown

| Stage | Task | Days |
|-------|------|------|
| 1 | Design schema: metrics_snapshots table + queries | 1 |
| 2 | Implement backend: GET endpoints for each metric group | 1 |
| 3 | Frontend: Dashboard page layout + chart library | 1 |
| 4 | Frontend: Render charts with real data | 1 |
| 5 | Testing + Production deployment | 1-2 |

---

## Architecture

### Database
**New table:** `metrics_snapshots`
- Snapshot of daily metrics (one row per tenant per day)
- Fields: tenant_id, date, auto_approved_count, csv_batches_count, queue_length, etc.

**Approach:**
- Nightly job computes metrics from approval_queue + ingestion_batches + erp_journal_entries
- Frontend queries snapshots (fast) instead of aggregating live (slow)

### Backend
**New endpoints:**
- `GET /api/v1/metrics/auto-approval/last-7-days` → {daily_counts, by_rule, confidence_distribution}
- `GET /api/v1/metrics/csv-ingestion/last-7-days` → {batches, success_rate, errors}
- `GET /api/v1/metrics/approval-queue/health` → {queue_length, avg_review_time, approval_rate}
- `GET /api/v1/metrics/accounts/vendors/top-10` → {vendor_code, frequency}

### Frontend
**New page:** `/app/dashboard/metrics`
- Layout: 2x2 grid of chart cards
- Charts: Line (trends), Bar (breakdown), Pie (distribution), Table (top-10)
- Chart library: Recharts (lightweight, React-friendly)
- Real-time refresh: 5-minute intervals + manual button

---

## Data Flow

```
[approval_queue] ─┐
[ingestion_batches]├─→ [Nightly Job] ─→ [metrics_snapshots]
[erp_journal_entries]─┘                      ↓
                                    [Dashboard API]
                                      ↓
                                  [Frontend Charts]
```

---

## Dependencies

- ✅ Phase 7 (approval_queue + auto-approval logic)
- ✅ Phase 8 (ingestion_batches + CSV ingestion)
- ⚠️ Nightly job runner (n8n workflow or cron)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Nightly job fails → stale data | Alerting + fallback to live aggregation |
| Large data volumes → slow queries | Indexes on (tenant_id, date), pre-aggregated snapshots |
| RLS bypass → data leak | Test RLS policies on all endpoints |
| Chart library OOM → crash | Pagination for top-10 tables |

---

## Out of Scope (Phase 10+)

- Alerting on thresholds (e.g., "approval queue > 100 pending")
- Custom metric definitions (user-defined KPIs)
- Export to CSV/PDF
- Integration with BI tools (Tableau, Looker)

---

## Next Steps

1. Design: Create `metrics_snapshots` schema + query layer
2. Backend: Implement 4 endpoints
3. Frontend: Build dashboard page with charts
4. Testing: Unit + E2E tests
5. Deploy: Production rollout + verify

**Kickoff:** 2026-06-27

---

## References

- Phase 7: Automated Approval Rules (approval_queue schema)
- Phase 8: Shadow GL Real Data Ingestion (ingestion_batches schema)
- Chart library: https://recharts.org/
