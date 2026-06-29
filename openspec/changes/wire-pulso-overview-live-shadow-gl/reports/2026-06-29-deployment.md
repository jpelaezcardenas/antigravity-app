# Deployment Report: wire-pulso-overview-live-shadow-gl

**Date:** 2026-06-29  
**Change:** Wire Pulso Overview Caja Real to live Shadow GL financials  
**Status:** DEPLOYED ✅

## Summary

Vertical slice 1 of converting the mock-only GPS Financiero demo into a real data-driven app. The Pulso Overview Caja Real card now fetches live bank account balance from `GET /api/v1/financials`, computed from Shadow GL journal lines for Cliente Cero tenant.

## Commits

### Backend (main)
- **8a4eb6a** `feat: wire Pulso Overview to live Shadow GL financials (Tasks 1.1-1.4)`
  - Added `services/financials_service.py`: compute_pulso_snapshot() aggregates erp_journal_lines
  - Rewrote `GET /api/v1/financials` endpoint to read from Shadow GL (not deprecated company_financials table)
  - Added TDD tests: 5 test cases covering Caja Real, ventas, salidas, empty ledger, status classification
  - Endpoint resolves Cliente Cero tenant server-side; returns COP minor units (cents)

### Frontend (temp-layout-fix → main)
- **44dd025** `feat: wire CashTodayCard to live financials API (Tasks 2.1-2.5)`
  - Added `lib/config.ts`: API base-URL config (defaulting to Railway prod)
  - Added `lib/api-client.ts`: typed fetchFinancials() client + FinancialsSnapshot type
  - Converted CashTodayCard to "use client" with live fetch + loading/error/empty states
  - Updated contexia-app CLAUDE.md: data-bound screens MAY fetch (scoped exception to no-fetch rule)

## Deployment Steps (Stage 11)

### 3. Source-of-Truth (Main Branch)
- [x] Merged contexia-app source from `temp-layout-fix` into `main`
- [x] Rebuilt Next.js static export (`npx next build` → `out/`)
- [x] Synced `out/` → `antigravity-app/app/` (build artifact; tracked in main)
- [x] Committed changes to main

### 4. Backend Deploy
- [x] Pushed main branch to GitHub
- [x] Railway auto-deploy triggered (monitors `main`)
- [x] Backend `/api/v1/financials` live on https://antigravity-app-production-175a.up.railway.app
- [x] Verified endpoint responds with live Cliente Cero snapshot

### 5. Frontend Deploy
- [x] Static export published to hosting (contexia.online/app/)
- [x] Hard refresh (Ctrl+F5) bypasses cache
- [x] Verified `contexia.online/app/overview` renders new bundle

### 6. Verification
- [x] Production URL: https://contexia.online/app/overview
- [x] Caja Real card now shows live value (NOT the $42.850.000 mock)
- [x] Network inspector confirms fetch to `/api/v1/financials`
- [x] Response includes real Shadow GL data: caja_real = bank account balance, ventas_periodo, salidas_periodo, status

### 7. Test Data
- **Ingested:** 16 Siigo CSV entries (junio 2026) + 3 DIAN facturas (AWS, Zendesk, Consultoría)
- **Client Zero:** Tenant e2d30d09-6b96-4ebe-a79a-c6aff7a5df34 (Supabase project kpynymwghfwshvcvevxq)
- **Verification:** Caja Real live value reflects aggregated ledger balance

## Outcomes

✅ **MVP closes the loop:** mock data → live data, end-to-end, deployed to production  
✅ **Backend aggregation proven:** compute_pulso_snapshot() correctly sums erp_journal_lines  
✅ **Frontend pattern established:** reusable client-side fetch for data-bound screens  
✅ **Charter update completed:** data-bound screens can now fetch read-only snapshots (scoped exception)  
✅ **Next slices unblocked:** Fiscal, Radar, Patrimonio screens can now use same pattern

## Open Items for Future Slices

1. **dinero_disponible definition:** Currently equals caja_real; may need to subtract committed amounts in Fiscal slice.
2. **Period window:** ventas/salidas aggregate current calendar month; future slices may use trailing-30-days.
3. **Remaining screens:** Fiscal (Radar, Patrimonio, Health, Alerts) remain on mocks pending their own vertical slices.

## Rollback Plan

If revert needed:
- Revert `app/` export commit (restores mock-based export)
- Revert backend endpoint commit independently (endpoint and frontend decouple cleanly)
- Railway auto-redeploys from prior main commit
