# Tasks: contexia-pwa-data-layer-mvp

## Slice 0: Supabase Schema (15 min) ✅ COMPLETE

- [x] Connect to Supabase project (ID: wzqymuzpjbagnbgsiqig)
- [x] Create `company_financials` table with schema
- [x] Create `transactions_pending` table with schema
- [x] Enable RLS on both tables
- [x] Create RLS policies (SELECT, INSERT, UPDATE for company_id = auth.uid())
- [x] Insert seed data for Contexia (client zero)
- [x] Insert 5 sample pending transactions
- [x] Verify data: SELECT from both tables returns results

**Notes:**
- Used MCP Supabase tool (execute_sql)
- Contexia UUID: `a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0`
- Data matches PWA mock: $42.850.000 caja, $38.500.000 dinero disponible, 5 pending tx

---

## Slice 1: Railway Endpoint (25 min) ✅ CODE COMPLETE, ⏳ DEPLOY PENDING

### 1.1 Create endpoint file
- [x] Create `apps/backend/presentation/financials_endpoints.py`
- [x] Implement `GET /api/v1/financials` route
- [x] Implement `GET /api/v1/pending-transactions` route
- [x] Use supabase_client from infrastructure module
- [x] Add proper error handling (404, 500 responses)
- [x] Type hints for request/response

**Code Location:**
```
apps/backend/presentation/financials_endpoints.py
  - router: APIRouter()
  - get_financials(company_id: str) → {caja_real, dinero_disponible, ...}
  - get_pending_transactions(company_id: str) → {count, transactions[]}
```

### 1.2 Register router
- [x] Import financials_router in `presentation/router.py`
- [x] Add `api_router.include_router(financials_router, prefix="/financials", tags=["financials"])`
- [x] Router mounted at `/api/v1/financials`

### 1.3 Test locally (not yet - no local env)
- [ ] Start backend: `cd apps/backend && python -m uvicorn main:app --reload`
- [ ] Test: `curl http://localhost:8000/api/v1/financials`
- [ ] Verify response includes: caja_real, dinero_disponible, ventas_ayer, salidas_plata, iva_vencimiento_dias, status

### 1.4 Commit
- [x] `git add apps/backend/presentation/financials_endpoints.py apps/backend/presentation/router.py`
- [x] `git commit -m "feat: add financials endpoints for MVP data layer"`
- [x] Commit message references Stage 11 deployment readiness

---

## Slice 2: Railway Deployment (Auto via Git) ⏳ PENDING

### 2.1 Verify environment
- [ ] Check Railway settings for:
  - [ ] `SUPABASE_URL` (https://wzqymuzpjbagnbgsiqig.supabase.co)
  - [ ] `SUPABASE_KEY` (service_role or anon key with table access)
  - [ ] Both env vars must be set before deploy

### 2.2 Deploy
- [ ] `git push origin main`
- [ ] Railway auto-detects push, triggers build
- [ ] Wait for deployment to complete (check Railway dashboard)
- [ ] Verify: Status shows "✅ Healthy" or "Deployed"

### 2.3 Test endpoint
- [ ] `curl https://antigravity-app-production-175a.up.railway.app/api/v1/financials`
  - Expected: `{"caja_real": 42850000, "dinero_disponible": 38500000, ...}`
- [ ] `curl https://antigravity-app-production-175a.up.railway.app/api/v1/pending-transactions`
  - Expected: `{"count": 5, "transactions": [...]}`
- [ ] Check response time: should be <200ms
- [ ] Verify no errors in Railway logs

---

## Slice 3: PWA Frontend Integration ⏳ BLOCKED - ARCHITECTURE TBD

### Architecture Decision Needed

Current state:
- ✅ Supabase has real data
- ✅ Railway API can serve it
- ❌ PWA page is compiled Next.js static HTML (minified, no server code)
- ❌ Data is hardcoded in JSX at build time

**Option A: Client Component + useEffect** (Recommended for MVP++, but source unclear)
```tsx
"use client";
import { useEffect, useState } from "react";

export default function OverviewPage() {
  const [cash, setCash] = useState(null);
  
  useEffect(() => {
    const API = "https://antigravity-app-production-175a.up.railway.app/api/v1";
    fetch(`${API}/financials`)
      .then(r => r.json())
      .then(data => setCash(data))
      .catch(err => console.error(err));
  }, []);
  
  return <CashTodayCard cash={cash || pulsoMock.cash} />;
}
```

**Option B: Runtime DOM patching** (Quick but fragile)
```html
<script>
async function loadData() {
  const API = "https://...railway.app/api/v1";
  const data = await fetch(`${API}/financials`).then(r => r.json());
  document.querySelector('[data-cash-real]').textContent = `$${data.caja_real.toLocaleString()}`;
  // ... patch other fields
}
window.addEventListener('DOMContentLoaded', loadData);
</script>
```

**Option C: Wait for proper architecture**
- Keep PWA showing mocked data
- Plan separate frontend refactor task
- API ready for future integration

**Current Recommendation:** 
- **For Stage 11:** Execute Options A or B
  - **A** requires finding source file and rebuilding (unclear structure)
  - **B** quick but needs HTML instrumentation (overview.html is minified)
- **Fallback:** Leave PWA on mocks, document API is ready in report

**Tasks (If Option A proceedes):**
- [ ] Locate source `app/app/overview/page.tsx` or equivalent
- [ ] Add `"use client"` directive
- [ ] Import useEffect, useState
- [ ] Fetch from API on component mount
- [ ] Fallback to pulsoMock if fetch fails
- [ ] Test in dev server
- [ ] Commit & push
- [ ] Vercel auto-redeploy

**Tasks (If Option B proceeds):**
- [ ] Create `public/scripts/load-financials.js`
- [ ] Wr ite DOM selector query for values to patch
- [ ] Inject `<script>` tag in overview.html before deploy
- [ ] Test in production after Vercel deploy

---

## Slice 4: Stage 11 - Deploy to Production (15 min) ⏳ PENDING

### 4.1 Backend Deploy (Railway)
- [ ] Verify code committed to main
- [ ] Push to GitHub: `git push origin main`
- [ ] Wait for Railway build (check dashboard)
- [ ] Endpoint responds: `curl https://...railway.app/api/v1/financials`
- [ ] No errors in Railway logs

### 4.2 Frontend Deploy (Vercel)
- [ ] Code on main branch (if Option A/B executed)
- [ ] Vercel auto-detects push, triggers build
- [ ] Build succeeds (check Vercel dashboard)
- [ ] Visit https://contexia.online/app/overview
- [ ] Hard refresh: `Ctrl+F5` to bypass cache
- [ ] Check:
  - [ ] Page loads without errors
  - [ ] Values display correctly (real or mocked depending on Option)
  - [ ] Console shows no 404/fetch errors

### 4.3 Integration Test
- [ ] Navigate to https://contexia.online/app/overview
- [ ] Open DevTools → Network tab
- [ ] Verify requests:
  - [ ] Fetch to `antigravity-app-production-175a.up.railway.app/api/v1/financials` succeeds (200 OK)
  - [ ] Response includes real data: `{"caja_real": 42850000, ...}`
  - [ ] DOM displays values correctly
  
### 4.4 Supabase Verification
- [ ] Supabase dashboard → Query editor
- [ ] `SELECT * FROM company_financials WHERE company_id = 'a0a0a0a0-...'`
  - Expected: 1 row with caja_real=42850000
- [ ] `SELECT COUNT(*) FROM transactions_pending WHERE company_id = 'a0a0a0a0-...'`
  - Expected: count=5

### 4.5 Create Stage 11 Report
- [ ] Create `reports/2026-06-21-deployment.md`
- [ ] Document:
  - Supabase table creation ✅
  - Seed data verification ✅
  - Railway endpoint health check
  - PWA frontend status (mocked or live)
  - Links to deployed resources
  - Screenshot of working dashboard
  - Any blocking issues

### 4.6 Commit Report
- [ ] `git add openspec/changes/contexia-pwa-data-layer-mvp/reports/2026-06-21-deployment.md`
- [ ] `git commit -m "docs: Stage 11 deployment report for contexia-pwa-data-layer-mvp"`
- [ ] `git push origin main`

---

## Verification Checklist

### ✅ When All Complete

- [ ] Supabase: `company_financials` table exists with Contexia data
- [ ] Supabase: `transactions_pending` table exists with 5 rows
- [ ] Railway: `GET /api/v1/financials` returns 200 OK + financial data
- [ ] Railway: `GET /api/v1/pending-transactions` returns 200 OK + transaction list
- [ ] PWA: Loads without console errors
- [ ] PWA: Shows correct values (mocked or live depending on Option)
- [ ] Contexia.online: Accessible and healthy
- [ ] Railway: Logs show no errors
- [ ] Stage 11 Report: Complete with evidence

### ⚠️ Blocking Issues

If any of these fail, escalate before marking done:
- Railway can't connect to Supabase (verify env vars)
- PWA can't fetch API (verify CORS in FastAPI)
- Vercel build fails (check deployment logs)

---

## Notes

- **Client Zero UUID:** `a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0` (hardcoded for MVP, move to auth in Phase 2)
- **CORS:** FastAPI main.py includes contexia.online in allow_origins
- **RLS:** Policies require auth.uid() to match company_id — for MVP, client zero testing only
- **PWA Frontend:** Source file location unclear (worktree vs. main mismatch). May need Investigation task.
