# Phase 9: Metrics Dashboard — Design

**Status:** DESIGNED (POST-MVP)  
**Date:** 2026-06-26  
**Change ID:** metrics-dashboard-phase9  
**Architecture:** Two dashboards (Admin + Client)

---

## Data Model

### metrics_snapshots Table (PostgreSQL)

```sql
CREATE TABLE metrics_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  snapshot_date date NOT NULL,
  
  -- Auto-Approval Metrics
  auto_approved_count int DEFAULT 0,
  auto_approved_recurring int DEFAULT 0,
  auto_approved_vendor int DEFAULT 0,
  auto_approved_micro int DEFAULT 0,
  
  -- CSV Ingestion Metrics
  csv_batches_uploaded int DEFAULT 0,
  csv_batches_completed int DEFAULT 0,
  csv_batches_error int DEFAULT 0,
  csv_rows_total int DEFAULT 0,
  
  -- Approval Queue Health
  queue_pending_count int DEFAULT 0,
  queue_approved_count int DEFAULT 0,
  queue_rejected_count int DEFAULT 0,
  avg_review_time_minutes int,
  
  -- Computed at snapshot time
  created_at timestamp DEFAULT now(),
  
  UNIQUE(tenant_id, snapshot_date),
  CHECK(snapshot_date <= CURRENT_DATE)
);

CREATE INDEX idx_metrics_tenant_date 
  ON metrics_snapshots(tenant_id, snapshot_date DESC);
```

### RLS Policies

```sql
ALTER TABLE metrics_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY metrics_snapshots_tenant_isolation ON metrics_snapshots
  FOR ALL
  USING (tenant_id = auth.uid()::uuid)  -- TODO: adjust for multi-tenant
  WITH CHECK (tenant_id = auth.uid()::uuid);
```

---

## Backend API Design

### Endpoint: GET /api/v1/metrics/auto-approval/last-7-days

**Response:**
```json
{
  "period": "2026-06-19..2026-06-26",
  "total_auto_approved": 342,
  "by_rule": {
    "recurring_transaction": {
      "count": 200,
      "confidence": 0.95,
      "false_positive_rate": 0.02
    },
    "known_vendor": {
      "count": 120,
      "confidence": 0.90,
      "false_positive_rate": 0.05
    },
    "micro_transaction": {
      "count": 22,
      "confidence": 0.85,
      "false_positive_rate": 0.10
    }
  },
  "daily_trend": [
    { "date": "2026-06-19", "count": 40 },
    { "date": "2026-06-20", "count": 52 },
    ...
  ],
  "confidence_distribution": {
    "0.85": 22,
    "0.90": 120,
    "0.95": 200
  }
}
```

### Endpoint: GET /api/v1/metrics/csv-ingestion/last-7-days

**Response:**
```json
{
  "period": "2026-06-19..2026-06-26",
  "batches_uploaded": 18,
  "batches_completed": 17,
  "batches_error": 1,
  "success_rate": 0.944,
  "total_rows": 1247,
  "daily_trend": [
    { "date": "2026-06-19", "uploaded": 2, "completed": 2, "rows": 145 },
    { "date": "2026-06-20", "uploaded": 3, "completed": 3, "rows": 289 },
    ...
  ],
  "error_summary": {
    "imbalanced_transaction": 1
  }
}
```

### Endpoint: GET /api/v1/metrics/approval-queue/health

**Response:**
```json
{
  "queue_pending": 8,
  "queue_approved_7d": 342,
  "queue_rejected_7d": 12,
  "approval_rate": 0.966,
  "avg_review_time_minutes": 45,
  "queue_age_minutes": {
    "0-30": 5,
    "30-60": 2,
    "60+": 1
  }
}
```

### Endpoint: GET /api/v1/metrics/accounts/vendors/top-10

**Response:**
```json
{
  "period": "2026-06-19..2026-06-26",
  "vendors": [
    { "code": "VENDOR-001", "name": "Acme Corp", "frequency": 45 },
    { "code": "VENDOR-002", "name": "Global Inc", "frequency": 38 },
    ...
  ]
}
```

---

## Frontend Design

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│  Metrics Dashboard                      [Refresh]        │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────┐  ┌─────────────────────┐       │
│  │ Auto-Approval Rate  │  │ CSV Success Rate    │       │
│  │ 342 entries         │  │ 17/18 batches       │       │
│  │ (Recurring: 200)    │  │ 1247 rows           │       │
│  └─────────────────────┘  └─────────────────────┘       │
│                                                           │
│  ┌─────────────────────┐  ┌─────────────────────┐       │
│  │ Queue Health        │  │ Approval Trend      │       │
│  │ 8 pending           │  │ [Line chart: 7 days]│       │
│  │ Avg: 45 min review  │  │                     │       │
│  └─────────────────────┘  └─────────────────────┘       │
│                                                           │
│  ┌────────────────────────────────────────────────┐     │
│  │ Top 10 Vendors                                 │     │
│  │ Acme Corp (45) | Global Inc (38) | ...         │     │
│  └────────────────────────────────────────────────┘     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Chart Components (Recharts)

| Card | Chart Type | Data |
|------|-----------|------|
| Auto-Approval Rate | Pie + Stats | by_rule breakdown |
| CSV Success Rate | Bar + Stats | batches completed/error |
| Queue Health | Gauge + Stats | pending count, avg time |
| Approval Trend | Line | daily_trend (7 days) |
| Top 10 Vendors | Bar | vendor frequency |

### Mobile Responsiveness
- Desktop: 2x2 grid
- Tablet: 2-column stack
- Mobile: 1-column stack (vertical scroll)

---

## Query Layer

### Compute Auto-Approval Metrics (for snapshot)

```sql
SELECT
  tenant_id,
  CURRENT_DATE as snapshot_date,
  COUNT(*) FILTER (WHERE auto_approved = true) as auto_approved_count,
  COUNT(*) FILTER (WHERE rule_applied = 'RECURRING_TRANSACTION') as auto_approved_recurring,
  COUNT(*) FILTER (WHERE rule_applied = 'KNOWN_VENDOR') as auto_approved_vendor,
  COUNT(*) FILTER (WHERE rule_applied = 'MICRO_TRANSACTION') as auto_approved_micro
FROM approval_queue
WHERE entry_date >= CURRENT_DATE - 7
GROUP BY tenant_id;
```

### Compute CSV Metrics (for snapshot)

```sql
SELECT
  tenant_id,
  CURRENT_DATE as snapshot_date,
  COUNT(*) as csv_batches_uploaded,
  COUNT(*) FILTER (WHERE status = 'completed') as csv_batches_completed,
  COUNT(*) FILTER (WHERE status = 'error') as csv_batches_error,
  COALESCE(SUM(row_count), 0) as csv_rows_total
FROM ingestion_batches
WHERE uploaded_at >= CURRENT_DATE - 7
GROUP BY tenant_id;
```

---

## Implementation Strategy

### Stage 1: Database Schema
- [ ] Create metrics_snapshots table
- [ ] Add RLS policies
- [ ] Create indexes
- [ ] Implement nightly computation job (n8n)

### Stage 2: Backend API
- [ ] GET /metrics/auto-approval/last-7-days
- [ ] GET /metrics/csv-ingestion/last-7-days
- [ ] GET /metrics/approval-queue/health
- [ ] GET /metrics/accounts/vendors/top-10
- [ ] Response models (Pydantic)
- [ ] Error handling

### Stage 3: Frontend Layout
- [ ] New page: `/app/dashboard/metrics`
- [ ] Card components (4x reusable cards)
- [ ] Responsive grid
- [ ] Loading states

### Stage 4: Chart Rendering
- [ ] Recharts integration
- [ ] LineChart (trend)
- [ ] BarChart (by_rule)
- [ ] PieChart (distribution)
- [ ] Table (top-10)
- [ ] Stats display (numbers)

### Stage 5: Testing & Deploy
- [ ] Unit tests (backend queries)
- [ ] Component tests (frontend charts)
- [ ] E2E tests (full flow)
- [ ] Production deployment
- [ ] Monitoring

---

## Testing Strategy

### Backend Tests
- Query accuracy (test fixtures with known data)
- RLS enforcement (tenant isolation)
- Edge cases (zero data, large datasets)
- Response structure validation

### Frontend Tests
- Chart rendering (data → DOM)
- Responsive layout (mobile/tablet/desktop)
- Loading & error states
- Pagination (top-10 table)

### E2E Tests
- Load dashboard → see metrics
- Refresh button triggers reload
- Mobile navigation works
- Data updates reflect in charts

---

## Performance Considerations

| Concern | Solution |
|---------|----------|
| Large snapshots table | Partition by (tenant_id, year) |
| Slow queries | Pre-aggregate in snapshots, not compute on-demand |
| Chart library bundle size | Use Recharts (minimal, tree-shakeable) |
| Real-time metrics | Accept 5-minute refresh + manual button |

---

## Rollout Plan

1. Deploy metrics_snapshots schema to Supabase
2. Enable nightly job (n8n) to populate snapshots
3. Deploy backend API endpoints
4. Deploy frontend dashboard
5. Monitor for data accuracy & performance
6. Tune refresh intervals based on load

---

## Success Metrics

- ✅ Dashboard page loads in < 2 seconds
- ✅ All 4 endpoints return data in < 500ms
- ✅ Charts render correctly with 1000+ rows
- ✅ RLS prevents cross-tenant data leakage
- ✅ Mobile experience is usable
- ✅ Ops team can answer "how many auto-approved?" in 30 seconds

---

## References

- Recharts: https://recharts.org/
- Nightly Job: Will use existing n8n infrastructure
- Approval Queue Schema: Phase 7 design
- CSV Ingestion Schema: Phase 8 design
