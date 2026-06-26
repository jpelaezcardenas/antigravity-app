# Phase 9: Metrics Dashboard — Proposal

**Status:** PROPOSED (POST-MVP)  
**Date:** 2026-06-26  
**Change ID:** metrics-dashboard-phase9  
**Timeline:** After MVP completion + Client Zero stabilization

---

## Context: This is POST-MVP Work

Phase 9 is **deferred until after MVP launch**. The MVP (Phases 1-8) focuses on Shadow GL core functionality for Cliente Cero (Contexia). Phase 9 adds operational visibility but is not critical for MVP launch.

---

## Problem Statement

When Phase 7 (Automated Approval Rules) and Phase 8 (CSV Ingestion) scale to multiple clients, **we need visibility into system health and per-client metrics**. Key questions:

**For Contexia (Admin):**
- How many entries are auto-approved per rule across all clients?
- What's the false positive rate?
- Which clients are ingesting the most?
- System performance + errors?

**For Clients (Self-Service):**
- How many of MY transactions were auto-approved?
- What's MY approval cycle time improvement?
- Which of MY vendors appear most frequently?
- Are there errors in MY uploads?

- How many entries are auto-approved per rule (recurring, vendor, micro)?
- What's the false positive rate per rule?
- How many CSV batches are ingested daily?
- What's the error rate for uploads?
- Which vendors appear most frequently?
- Approval cycle time improvement vs. before automation?

**Impact:** Operations team is blind to system performance. Cannot tune rules or prioritize improvements. No data-driven decision-making.

---

## Solution Overview: Two Dashboards

### **1. Admin Dashboard** (Contexia internal only)
**Path:** `/admin/dashboard/metrics` (separate admin app)  
**Audience:** Contexia operations team  
**Data:** Cross-tenant system metrics

Displays:
- Total auto-approved entries (all clients)
- Breakdown by rule + client
- System health (errors, queue length)
- Top clients by volume
- Confidence score distribution across all data
- CSV ingestion health (success rates, error types)

### **2. Client Dashboard** (Per-tenant self-service)
**Path:** `/app/dashboard/metrics` (in main PWA)  
**Audience:** Each client's finance team  
**Data:** Tenant-isolated metrics only

Displays:
- YOUR auto-approved entries (last 7 days)
- YOUR approval cycle time improvement
- YOUR CSV upload success rate
- YOUR top 10 vendors
- YOUR pending approvals
- YOUR error history (if any)

---

## Success Criteria

**Both dashboards:**
- ✅ Load in < 2 seconds
- ✅ Metrics update every 5 minutes (+ manual refresh)
- ✅ Charts render correctly for empty data
- ✅ RLS enforced: each tenant sees ONLY their data
- ✅ Mobile-responsive
- ✅ All data from queries (no hardcoding)

**Admin Dashboard additionally:**
- ✅ Accessible by Contexia admins only (firewall/auth gate)
- ✅ Shows ALL tenants + aggregates

**Client Dashboard additionally:**
- ✅ Accessible by each tenant's users (via RLS)
- ✅ Shows only that tenant's data

---

## Scope & Timeline

**Estimated effort:** 6 stages × 1-2 days = 6-8 days  
**Target completion:** 2-3 weeks after MVP launch  
**Prerequisite:** MVP (Phases 1-8) must be stable with 2+ paying clients

### Stage Breakdown

| Stage | Task | Days |
|-------|------|------|
| 1 | Database: metrics_snapshots schema + RLS policies | 1 |
| 2 | Backend: Admin API endpoints (cross-tenant aggregates) | 1 |
| 3 | Backend: Client API endpoints (tenant-isolated queries) | 1 |
| 4 | Frontend: Admin Dashboard (`/admin/dashboard/metrics`) | 1.5 |
| 5 | Frontend: Client Dashboard (`/app/dashboard/metrics`) | 1.5 |
| 6 | Testing + Production deployment | 1-2 |

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
