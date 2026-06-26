# Phase 9: Metrics Dashboard — Tasks

**Status:** READY FOR IMPLEMENTATION  
**Target Completion:** 2026-07-03  
**Effort:** 5-7 days

---

## Stage 1: Database Schema & Snapshots (1 day)

**Goal:** Create `metrics_snapshots` table and nightly computation job.

### 1.1 Create migration: 0020_metrics_snapshots.sql
- [ ] `CREATE TABLE metrics_snapshots` with all fields
- [ ] Add RLS policies (tenant isolation)
- [ ] Create indexes: (tenant_id, snapshot_date DESC)
- [ ] Add CHECK constraints (date <= today)

### 1.2 Write migration test
- [ ] Verify table schema exists
- [ ] Verify RLS policies enabled
- [ ] Verify indexes created

### 1.3 Setup nightly computation job
- [ ] Create n8n workflow: compute-metrics-daily
- [ ] Trigger: 00:05 UTC daily
- [ ] Compute auto-approval metrics (by rule, daily counts)
- [ ] Compute CSV ingestion metrics (batches, rows, errors)
- [ ] Compute queue health (pending, review time)
- [ ] UPSERT into metrics_snapshots (idempotent)
- [ ] Error handling: log failures, alert on repeated failures

### 1.4 Populate historical data (last 30 days)
- [ ] Backfill metrics_snapshots from approval_queue + ingestion_batches
- [ ] Test: verify counts match reality
- [ ] Document: how to backfill if job fails

**Acceptance:** metrics_snapshots contains 30 days of historical data, nightly job runs successfully.

---

## Stage 2: Backend API Endpoints (1 day)

**Goal:** Implement 4 GET endpoints for metrics retrieval.

### 2.1 Create services/metrics_service.py
- [ ] `get_auto_approval_metrics(tenant_id, days=7)` → dict
- [ ] `get_csv_ingestion_metrics(tenant_id, days=7)` → dict
- [ ] `get_queue_health(tenant_id)` → dict
- [ ] `get_top_vendors(tenant_id, limit=10)` → list

### 2.2 Create response models (Pydantic)
- [ ] `AutoApprovalMetricsResponse`
- [ ] `CSVIngestionMetricsResponse`
- [ ] `QueueHealthResponse`
- [ ] `VendorMetricsResponse`

### 2.3 Create presentation/metrics_endpoints.py
- [ ] `GET /metrics/auto-approval/last-7-days`
- [ ] `GET /metrics/csv-ingestion/last-7-days`
- [ ] `GET /metrics/approval-queue/health`
- [ ] `GET /metrics/accounts/vendors/top-10`
- [ ] Error handling (404 if tenant not found, 500 on DB error)

### 2.4 Write backend tests (TDD)
- [ ] Test each endpoint with sample data
- [ ] Test RLS: tenant A can't see tenant B's metrics
- [ ] Test edge cases: zero data, large datasets
- [ ] Test response schema validation

### 2.5 Register metrics router
- [ ] Add to presentation/router.py: include metrics router with prefix `/metrics`
- [ ] Verify in main.py that router is loaded

**Acceptance:** All 4 endpoints respond with correct JSON, RLS enforced, tests passing.

---

## Stage 3: Frontend Dashboard Layout (1 day)

**Goal:** Create dashboard page structure and card components.

### 3.1 Create pages/dashboard/metrics.tsx
- [ ] Import Recharts + components
- [ ] Create responsive grid (2x2 on desktop, 1 column on mobile)
- [ ] Create 4 card components (placeholders)
- [ ] Add refresh button + timestamp of last refresh
- [ ] Add loading & error states

### 3.2 Create Card component (reusable)
- [ ] Props: title, subtitle, children (chart content), isLoading, error
- [ ] Styling: card shadow, padding, responsive
- [ ] Error display: show error message if fetch fails

### 3.3 Create useMetrics hook
- [ ] Fetch all 4 endpoints on mount
- [ ] Refresh logic: manual button + 5-minute auto-refresh
- [ ] State management: loading, error, data
- [ ] Handle race conditions (cancel previous request on unmount)

### 3.4 Add route to PWA
- [ ] Add `/dashboard/metrics` route in Next.js router
- [ ] Require auth (wrap with ProtectedRoute)
- [ ] Add link to sidebar/nav

### 3.5 Test layout responsively
- [ ] Desktop (1440px): 2x2 grid visible
- [ ] Tablet (768px): 2-column layout
- [ ] Mobile (375px): 1-column, vertical scroll
- [ ] Spacing/typography correct

**Acceptance:** Dashboard page loads, cards display (placeholder content), responsive on all screen sizes.

---

## Stage 4: Chart Rendering & Data Binding (1 day)

**Goal:** Render charts with real API data.

### 4.1 Auto-Approval Card
- [ ] PieChart: by_rule breakdown (recurring, vendor, micro)
- [ ] Stats: total count, confidence scores
- [ ] Daily trend: LineChart (last 7 days)
- [ ] Color code: each rule has distinct color

### 4.2 CSV Ingestion Card
- [ ] BarChart: completed vs error batches
- [ ] Stats: success rate percentage, total rows
- [ ] Daily trend: LineChart (uploaded vs completed)

### 4.3 Queue Health Card
- [ ] Gauge: pending count (visual indicator)
- [ ] Stats: avg review time, approval rate
- [ ] Age breakdown: bar chart (0-30m, 30-60m, 60+m pending)

### 4.4 Top 10 Vendors Card
- [ ] Table: vendor code, name, frequency
- [ ] Sortable by frequency
- [ ] Pagination if > 10 vendors
- [ ] Visual: bar chart or inline sparkline per vendor

### 4.5 Chart customization
- [ ] Responsive chart sizing (container-based)
- [ ] Tooltip on hover (show values)
- [ ] Legend (clickable to toggle series)
- [ ] Color scheme: consistent with Contexia branding

### 4.6 Error & loading states
- [ ] Loading skeleton while fetching
- [ ] Error message: "Failed to load metrics. Retry?"
- [ ] Empty state: "No data available for period"

**Acceptance:** All charts render with real data, interactive, responsive, no console errors.

---

## Stage 5: Testing & Production Deployment (1-2 days)

**Goal:** Comprehensive testing and production rollout.

### 5.1 Unit tests (backend)
- [ ] `test_metrics_service.py`: query correctness (8+ tests)
- [ ] Test fixture: 30-day sample dataset
- [ ] Verify counts match expected values
- [ ] Test RLS policies (tenant isolation)

### 5.2 Component tests (frontend)
- [ ] `test_metrics_page.tsx`: page renders without crashing (3+ tests)
- [ ] Test useMetrics hook: fetch + refresh logic
- [ ] Test Card component: loading/error/success states
- [ ] Test responsiveness: grid layout at various breakpoints

### 5.3 E2E tests
- [ ] Navigate to `/dashboard/metrics`
- [ ] Page loads, all charts visible
- [ ] Refresh button triggers reload
- [ ] Data updates in charts
- [ ] Mobile navigation works

### 5.4 Performance testing
- [ ] Dashboard load time < 2 seconds
- [ ] API endpoints respond < 500ms
- [ ] Charts render without lag (Lighthouse)
- [ ] Memory usage stable (no leaks)

### 5.5 Staging deployment
- [ ] Deploy to staging environment
- [ ] Verify all endpoints accessible
- [ ] Test with production-like data volumes
- [ ] A/B test (10% traffic) if applicable

### 5.6 Production deployment (MANDATORY STAGE 11)
- [ ] Create deployment checklist
- [ ] Push commits to main
- [ ] Verify Railway build succeeds
- [ ] Verify endpoint accessibility
- [ ] Monitor error rates (first hour)
- [ ] Create deployment report
- [ ] Document known limitations

### 5.7 Post-deployment monitoring
- [ ] Check nightly job completion logs
- [ ] Verify metrics_snapshots table has today's data
- [ ] Monitor API response times
- [ ] Check for user-reported issues

**Acceptance:** 
- ✅ All 13+ tests passing
- ✅ Dashboard live in production
- ✅ Metrics updating daily
- ✅ Team can access and use dashboard
- ✅ Deployment report filed

---

## Detailed Breakdown

| Stage | Task | Tests | Lines of Code | Days |
|-------|------|-------|---------------|------|
| 1 | Schema + Job | 3 | ~150 SQL | 1 |
| 2 | Backend API | 8 | ~300 Python | 1 |
| 3 | Frontend Layout | 3 | ~400 React | 1 |
| 4 | Charts | 5 | ~600 React | 1 |
| 5 | Testing + Deploy | 13+ | ~200 tests | 1-2 |
| **Total** | | **32+** | **~1650** | **5-7** |

---

## Definition of Done

Each stage is complete when:

1. **Code written** (all acceptance criteria met)
2. **Tests written** (TDD: tests written before implementation)
3. **Tests passing** (100% pass rate)
4. **Code reviewed** (peer review completed)
5. **Deployed** (changes live in production)
6. **Documented** (docstrings, design notes)

---

## Rollback Plan

If issues arise in production:

1. **Disable dashboard:** Remove `/dashboard/metrics` route temporarily
2. **Disable job:** Pause nightly metrics computation (no data loss)
3. **Revert commits:** `git revert <commit>` and redeploy
4. **Data preservation:** metrics_snapshots table remains for audit trail

---

## Dependencies

- ✅ Phase 7: approval_queue + auto-approval logic
- ✅ Phase 8: ingestion_batches + CSV ingestion
- ⚠️ n8n for nightly job (assuming available)
- ⚠️ Recharts library (add to frontend dependencies)

---

## Success Metrics (Post-Deployment)

- ✅ Dashboard loads in < 2 seconds (avg response time)
- ✅ Ops team uses dashboard daily
- ✅ 0 RLS violations (no data leaks)
- ✅ Nightly job 100% success rate
- ✅ API endpoint p95 latency < 500ms
- ✅ Mobile experience rated ≥4/5 by team

---

## Next Steps

1. **Kickoff:** 2026-06-27 (create git branch, start Stage 1)
2. **Daily standup:** Track progress, unblock issues
3. **Completion:** Expect 2026-07-03 (5 business days)
4. **Phase 10:** Plan next initiative after deployment

---

## References

- Design: `design.md`
- Proposal: `proposal.md`
- Approval Queue Schema: Phase 7 design
- CSV Ingestion Schema: Phase 8 design
- Recharts Docs: https://recharts.org/
