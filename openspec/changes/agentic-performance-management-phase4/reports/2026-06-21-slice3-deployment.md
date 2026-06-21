# Slice 3 Deployment Report — Stage 11
**FASE 4: Agentic Performance Management Phase 4 — Pulso Diario + Radar Predictivo + Auditoría Sombra**

Date: 2026-06-21  
Scope: Read-only daily summaries (Pulso), risk scoring + cashflow forecast + HITL (Radar), audit PDF + signoff gate (Auditoría)  
Status: **DEPLOYED TO PRODUCTION**

---

## What Changed

### Slice 1+2 Recap (Already Deployed)
- Shadow GL substrate (`tenants`, `dian_xml_documents`, `erp_journal_entries`, `erp_journal_lines`)
- Reconciliation view (`shadow_gl_discrepancies`)
- DIAN XML manual ingestion endpoint
- `approval_queue` + `executor_outbox` tables
- Centinela Resolution poller + Resolution Agent + Critic retry loop
- Approval-triggered outbox jobs

### Slice 3 New Components

#### Backend Services

1. **`pulso_diario_service.py`** (Tasks 3.1–3.2)
   - `get_daily_summary(tenant_id, date)`: aggregates DIAN/ERP totals, discrepancies, alerts for a day
   - Read-only against Shadow GL tables
   - Returns BIGINT minor units (no float)

2. **`radar_service.py`** (Tasks 3.3–3.5)
   - `calculate_risk_score(tenant_id, date)`: deterministic 0-100 score
     - Discrepancy rate: 40 pts
     - Amount mismatch: 30 pts
     - Alert frequency this month: 20 pts
     - Days overdue: 10 pts
   - `calculate_cashflow_forecast(tenant_id, days=30)`: linear projection of net DIAN-ERP flux
   - `enqueue_risk_review_if_critical(tenant_id)`: HITL gate when score >= 80, dedupes pending entries

3. **`auditoria_sombra_service.py`** (Tasks 3.6–3.7)
   - `generate_audit_report(tenant_id, date_start, date_end, audience)`: PDF generation
     - Read-only against Shadow GL
     - Minimal valid PDF (PDF-1.4) with statistics
   - `request_audit_report(tenant_id, date_start, date_end, audience)`: HITL orchestrator
     - Internal: immediate download URL
     - External: enqueues `audit_report_signoff`, URL withheld until approved
   - `get_audit_report_status(approval_queue_id)`: post-approval query

#### API Endpoints (new in Slice 3)

- `GET /api/v1/agents/pulso-diario/summary?tenant_id=...&date=...`
- `GET /api/v1/agents/radar-predictivo/risk-score?tenant_id=...`
- `POST /api/v1/agents/auditoria-sombra/report` (body: tenant_id, date_start, date_end, audience)
- `GET /api/v1/agents/auditoria-sombra/report-status/{approval_queue_id}`

#### Database Changes

- No new tables (uses existing `approval_queue` with new `draft_type` values: `risk_review`, `audit_report_signoff`)
- No new migrations required

---

## Test Evidence

### RED → GREEN Progression

| Task | Test File | Status |
|------|-----------|--------|
| 3.1–3.2 | `test_pulso_diario.py` | 2 tests GREEN (data aggregation, zero-activity) |
| 3.3 | `test_radar.py` | 3 tests GREEN (zero, with discrepancies, deterministic) |
| 3.4 | `test_radar.py` | 2 tests GREEN (returns int, with history) |
| 3.5 | `test_radar.py` | 2 tests GREEN (creates entry, no duplicate) |
| 3.3–3.5 | `test_radar.py` | 1 endpoint test GREEN (valid JSON response) |
| 3.6 | `test_auditoria_sombra.py` | 3 tests GREEN (PDF bytes, statistics, read-only) |
| 3.7 | `test_auditoria_sombra.py` | 3 tests GREEN (internal URL, external signoff, rejected) |

**Total: 16 new tests passing (8 Radar + 6 Auditoría + 2 Pulso)**

### Full Suite Status
- Before Slice 3: 106 passing, 1 skipped
- After Slice 3: 116+ passing, 1 skipped
- **Zero regressions**

---

## Stage 11 Checklist

### 11.1 git commit + push to main
- ✅ All Slice 3 commits on `main` branch:
  - `9f94b41` feat(pulso-diario) — Tasks 3.1–3.2
  - `b51b355` feat(radar): risk-score — Task 3.3
  - `2278e92` feat(radar): cashflow forecast — Task 3.4
  - `db08d51` feat(radar): risk_review HITL gate — Task 3.5
  - `5a30823` feat(radar): risk-score endpoint
  - `040e5ef` feat(auditoria-sombra): PDF generation — Task 3.6
  - `daa1fb0` fix(auditoria-sombra): PDF size threshold + content checks
  - `ea9d8e5` docs(tasks): 3.6 complete
  - `3ac3f06` feat(auditoria-sombra): external signoff gate — Task 3.7

### 11.2 Vercel build complete
- ✅ Frontend untouched in Slice 3 (backend-only changes)

### 11.3 Railway deploy active
- ⚠️ **BLOCKED — found mid-deployment, NOT resolved in this session (see below)**
- Service: `antigravity-app` (project `elegant-success`, env `production`), static URL `antigravity-app-production-175a.up.railway.app`

### 11.4 Production URL: changes visible and working
- ❌ **NOT YET VERIFIED** — endpoints return 404 in production. Root cause identified, fix deferred pending user decision (see below).

### 11.5 Deployment report
- ✅ This document (updated post-investigation)

---

## ⚠️ Stage 11 Blocker: Railway deploy branch mismatch (discovered 2026-06-21)

**What happened:**
1. Pushed all 22 commits (Slice 2 + Slice 3) to `origin/main` — succeeded (`609f16c..a4a48e9`).
2. Checked Railway: latest deployment (`0dbc7d5f`, 09:04 UTC) predated the push — no auto-deploy triggered.
3. Forced a rebuild via `FORCE_REBUILD` env var bump (`railway_set_variable` with `skip_deploys=false`) — new deployment `b176d9d1` reported `SUCCESS`, app started cleanly (`Uvicorn running on http://0.0.0.0:8080`).
4. Hit the new endpoints — all returned 404. Checked `/openapi.json`: it listed the **old** routes (`/api/v1/radar/scenarios`, `/api/v1/radar/health`) that Slice 3 replaced, and was missing `/agents/pulso-diario/summary`, `/agents/radar-predictivo/risk-score`, `/agents/auditoria-sombra/report` entirely.
5. Queried Railway's GraphQL API for deployment `meta`: the service is **not tracking `main`**. It tracks branch `claude/angry-sutherland-976d5d`, and the deployed commit (`563971b`, "Merge commit 'c9c29db' into tmp-175a-fix") does **not** have `main` merged in (`git merge-base --is-ancestor origin/main origin/claude/angry-sutherland-976d5d` → false).

**Root cause:** The Railway service `antigravity-app` (production-175a) is configured to deploy from `claude/angry-sutherland-976d5d`, not `main`, contradicting `CLAUDE.md`'s documented deploy branch (`main`). This appears to be drift from an earlier Railway-deploy-specific fix branch (`tmp-175a-fix` / `tmp-175a-deploy`) that was never reconciled back to `main`-based deploys. `git push origin main` silently does nothing for this service — Railway's dashboard would show no new deploy triggered by that push, which is easy to miss without explicitly checking deployment `meta.branch` and `meta.commitHash`.

**Decision:** Investigated and documented only — **no fix applied to production this session** (user explicitly chose "investigate only, don't touch production yet" when asked). `CHECKPOINTS.md` updated with a new Stage 7 checkpoint to catch this in future deploys (see `ai-specs/openspec-deployment-standard/CHECKPOINTS.md`, Stage 7 Pre-Deploy).

**Options for resolution (not yet decided):**
1. Merge `main` → `claude/angry-sutherland-976d5d` and push (keeps current Railway config, no dashboard access needed).
2. Reconfigure the Railway service's deploy branch to `main` directly (aligns with `CLAUDE.md`, but needs Railway dashboard/settings access not confirmed available via current MCP tools).

**Status: Slice 3 code is complete, tested (122 passing, 1 skipped), and committed to `main` — but NOT live in production pending this branch resolution.**

---

## Verification Commands (to run once the branch issue is resolved)

```bash
# Pulso Diario summary
curl https://antigravity-app-production-175a.up.railway.app/api/v1/agents/pulso-diario/summary?tenant_id=<CLIENTE_CERO_UUID>

# Radar Predictivo risk-score + forecast
curl https://antigravity-app-production-175a.up.railway.app/api/v1/agents/radar-predictivo/risk-score?tenant_id=<CLIENTE_CERO_UUID>

# Auditoría Sombra internal report
curl -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/agents/auditoria-sombra/report \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"<CLIENTE_CERO_UUID>","date_start":"2026-05-22","date_end":"2026-06-21","audience":"internal"}'
```

Expected once resolved: All return 200 with valid JSON payloads (not the pre-Slice-3 routes currently served).

---

## Architecture Notes

### Determinism + HITL Pattern
All three agents follow the established pattern:
- **Deterministic computation** (no LLM) for core decisions (risk score, statistics)
- **HITL gating** for high-stakes actions (risk_review on critical scores, audit_report_signoff for external delivery)
- **Read-only on Shadow GL** — none of the new services mutate Shadow GL tables; they only consume the view + base tables

### `approval_queue` extension
Slice 3 introduces two new `draft_type` values that reuse the existing `approval_queue` table:
- `risk_review` (Radar) — payload: `{risk_score, forecast_30d_minor, tenant_id, threshold}`
- `audit_report_signoff` (Auditoría Sombra) — payload: `{tenant_id, date_start, date_end, audience, report_id, pdf_size_bytes}`

This validates D1 from `design.md` (JSONB payload approach scales without new tables).

### Cashflow Forecast Simplification
Per spec, "short-horizon cashflow forecast" — implemented as a linear projection of last-30-days net flux. More sophisticated time-series modeling deferred to future iteration once we have real Contexia data over a longer window.

---

## What's Deferred

- **PDF rendering quality**: current PDF uses minimal valid PDF structure (~900 bytes with stats text). Production-quality reports would need `reportlab` or `weasyprint` (not yet installed in venv). Tracked for Slice 5 polish.
- **Audit report storage**: download URLs are placeholders. Real S3/Supabase Storage upload deferred to external-connection phase.
- **`draft_id` schema cleanup**: discovered Slice 3 that `approval_queue.draft_id` is NOT NULL. New `risk_review` and `audit_report_signoff` types now satisfy this constraint with synthetic IDs. Worth revisiting in archive whether `draft_id` should be nullable for non-document approval types.
- **Tenant context propagation**: still hardcoded to Cliente Cero per Slice 2 note. Slice 4 (Taty) will wire tenant resolution from HTTP context.

---

## Rollback Plan

Per Stage 11 standard, once the branch issue is resolved and a real deploy lands:
1. `git revert <commit-hash>` for offending commit
2. Push to whichever branch Railway actually tracks → Railway auto-redeploys
3. No schema migrations to roll back (Slice 3 reused existing tables)

---

## Slice 3 Status: ⚠️ CODE COMPLETE, DEPLOY BLOCKED

All Tasks 3.1–3.7 complete and tested (122 passing, 1 skipped, committed to `main`).
**Task 3.8 (Stage 11 deploy) is blocked** on resolving the Railway deploy-branch mismatch documented above — production is still serving pre-Slice-3 code. Do not start Slice 4 deployment work, or mark this change ready for `/opsx:archive`, until 3.8 is genuinely closed with a verified production response from all three new endpoints.
