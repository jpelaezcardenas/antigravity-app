# Phase 9: Metrics Dashboard — Tasks

**Status:** DEPLOYED (Stage 11 complete 2026-08-31)

---

## Stage 1: Database Schema & Snapshots

### 1.1 Create migration: 0045_metrics_snapshots.sql
- [x] `CREATE TABLE metrics_snapshots` with all fields
- [x] Add RLS policies (tenant isolation + service_role bypass)
- [x] Create indexes: (tenant_id, snapshot_date DESC) + UNIQUE (tenant_id, snapshot_date)

### 1.2 Migration applied
- [x] Applied via Supabase SQL Editor (2026-08-30) — confirmed "Success. No rows returned"

### 1.3 Setup nightly computation job
- [ ] Configure n8n workflow or Railway cron — **DEFERRED** (endpoint exists, automation pending)

### 1.4 Populate historical data
- [ ] Backfill via `POST /api/v1/metrics/snapshot/compute` per tenant — **PENDING first run**

---

## Stage 2: Backend API Endpoints

### 2.1 Create services/metrics_service.py
- [x] `get_auto_approval_metrics(tenant_id, days=7)` → dict
- [x] `get_csv_ingestion_metrics(tenant_id, days=7)` → dict
- [x] `get_queue_health(tenant_id)` → dict
- [x] `get_top_vendors(tenant_id, limit=10)` → list
- [x] `compute_and_upsert_snapshot(tenant_id, date)` → dict

### 2.2 Create response models (Pydantic) — models/metrics.py
- [x] `AutoApprovalMetricsResponse`
- [x] `CSVIngestionMetricsResponse`
- [x] `QueueHealthResponse`
- [x] `VendorEntry`
- [x] `SnapshotComputeResponse`

### 2.3 Create presentation/metrics_endpoints.py
- [x] `GET /metrics/auto-approval/last-7-days`
- [x] `GET /metrics/csv-ingestion/last-7-days`
- [x] `GET /metrics/queue-health`
- [x] `GET /metrics/top-vendors`
- [x] `POST /metrics/snapshot/compute`
- [x] Import error fixed (commit `2426484`) — uses `user: dict = Depends(get_current_user)` pattern

### 2.4 Backend unit tests
- [x] `tests/test_metrics_service.py` — 7 tests passing

### 2.5 Register metrics router
- [x] Added to `main.py` with defensive try/except wrapper

---

## Stage 3: Frontend Dashboard

### 3.1 Components created
- [x] `AutoApprovalCard.tsx` — total approved, by-rule breakdown, false positive rate, 7-day bar chart
- [x] `CSVIngestionCard.tsx` — batches, rows OK/error, daily breakdown with color-coded error rate
- [x] `QueueHealthCard.tsx` — pending count (green/yellow/red), avg review time
- [x] `TopVendorsCard.tsx` — top 10 vendors with proportional bar chart
- [x] `MetricsDashboardSection.tsx` — 2-column responsive grid assembling all 4 cards

### 3.2 Frontend wiring
- [x] `lib/metrics-client.ts` — typed fetch functions using authenticatedFetch
- [x] `lib/config.ts` — 4 endpoint constants added
- [x] `app/app/bunker/page.tsx` — MetricsDashboardSection integrated in dashboard section
- [x] `contexia-app/CLAUDE.md` — 9th data-bound exception documented

---

## Stage 11: Deploy to Production (MANDATORY)

- [x] 11.1 git commit + push to main (`d64274f`, `2426484`)
- [x] 11.2 Vercel build auto-triggered from main
- [x] 11.3 Railway deploy auto-triggered — 502 from import error fixed in `2426484`
- [x] 11.4 Endpoints live under `/api/v1/metrics/`
- [x] 11.5 Deployment report: `reports/2026-08-31-deployment.md`

---

## Pending (non-blocking, not required to archive)

- [x] Configure nightly snapshot job — Hermes cron `metrics-snapshot.sh` @ 00:05 COT (`5 5 * * *`), `no_agent: true`, `deliver: local` (manage dashboard). Job id `a3f9c2d1e4b7` in `~/.hermes/profiles/contexia/cron/jobs.json`. Backend endpoint: `POST /internal/metrics/snapshot/all-active`. ✅ 2026-08-31
- [x] Trigger first manual snapshot per tenant — all 11 clients: `2026-08-31` ✅ E2E verified
- [x] Verify cards display data in Búnker after snapshot is populated — 2026-09-01: cards renderizan correctamente; muestran "Sin datos disponibles" en estado error cuando no hay token en localStorage (correcto por diseño). Con login real los 4 cards cargan. Datos 2026-08-31 verificados en 11 tenants vía E2E del cron.
