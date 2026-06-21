# OpenSpec Change: contexia-pwa-data-layer-mvp

## Executive Summary

**What:** Connect Contexia PWA (currently showing mocked financial data) to real data from Supabase via Railway API endpoints.

**Why:** Client Zero (Contexia) needs to see live financial data: cash position, available funds, pending transactions.

**Impact:** PWA dashboard transitions from hardcoded values to live Supabase data. Data reflects company_financials and transactions_pending tables.

---

## What Changes

### 1. Supabase Schema & Seed Data ✅ DONE
- ✅ Created `company_financials` table
- ✅ Created `transactions_pending` table  
- ✅ Enabled RLS with proper policies
- ✅ Seeded Contexia (client zero: `a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0`) with initial data:
  - Caja Real: $42.850.000
  - Dinero disponible: $38.500.000
  - Ventas ayer: $1.250.000
  - Salidas plata: $345.000
  - IVA vencimiento: 3 días
  - 5 transacciones pendientes

### 2. Railway Endpoint ✅ IN PROGRESS
- ✅ Created `apps/backend/presentation/financials_endpoints.py`
- ✅ Implemented:
  - `GET /api/v1/financials` → company_financials snapshot
  - `GET /api/v1/pending-transactions` → unclassified transactions
- ✅ Registered in presentation/router.py
- ⏳ Pending: Railway deployment (git push → auto-deploy)

### 3. PWA Update ⏳ BLOCKED - ARCHITECTURE DECISION NEEDED
**Issue:** PWA HTML is compiled Next.js static asset (minified). Cannot patch directly.

**Options:**
- **A) Convert page to Client Component** — modify source React component to call API on mount
  - Source location unclear (worktree vs. main branch structure mismatch)
  - Would require Next.js rebuild
  
- **B) Inject JavaScript at runtime** — load data via fetch, update DOM selectors
  - Non-standard, fragile against layout changes
  - Fast for MVP but technical debt
  
- **C) Wait for frontend refactor** — properly route financial data through component props
  - Proper architecture but blocks MVP
  
**Recommendation for MVP:** 
- Proceed with Plans A+B (Supabase + Railway API)
- Deploy both to production
- PWA will continue showing mocked data but API is ready for frontend to consume
- Mark as "API Ready, Frontend TBD" in Stage 11 report

---

## Done Criteria (Stage 11)

- [x] Supabase tables created + RLS configured
- [x] Seed data inserted (Contexia financials + 5 pending transactions)
- [x] Railway endpoint code written (`financials_endpoints.py`)
- [x] Endpoints registered in main router
- [ ] Code committed to main branch
- [ ] Railway autodeploy activated (git push)
- [ ] Endpoint health check: `GET https://antigravity-app-production-175a.up.railway.app/api/v1/financials`
- [ ] Supabase connectivity verified
- [ ] Stage 11 Report created with test results
- [ ] Change archived

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| A. Supabase Schema | 15 min | ✅ Complete |
| B. Railway Endpoint | 25 min | ✅ Code Done, ⏳ Deploy Pending |
| C. PWA Integration | 20 min | ⏳ Blocked (Architecture TBD) |
| D. OpenSpec Artifacts | 15 min | ⏳ In Progress |
| Stage 11. Deploy + Test | 15 min | ⏳ Pending |
| **Total** | **90 min** | ~60% complete |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Supabase env vars missing on Railway | ❌ API fails | Verify SUPABASE_URL, SUPABASE_KEY in Railway settings before deploy |
| CORS blocked between PWA (contexia.online) and API (railway.app) | ❌ Fetch fails | Ensure FastAPI has cors_origins including contexia.online |
| Pending transactions count is 5 but UI hardcodes "5" | ℹ️ Mock coherence | Matches seed data exactly, can update if needed |

---

## Related Artifacts

- `tasks.md` — Checklist for implementation
- `reports/YYYY-MM-DD-deployment.md` — Stage 11 test results (TBD)
