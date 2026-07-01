# Deployment Report: wire-pulso-overview-live-shadow-gl

**Date:** 2026-06-29  
**Change:** Wire Pulso Overview Caja Real to live Shadow GL financials  
**Status:** DEPLOYED ✅ (backend) — frontend delivery reconciled 2026-07-01, see note below

> ## RECONCILIATION (2026-07-01)
>
> This report's **frontend** section below (commits `4433c5b`, and the "Frontend Deploy"
> steps) is STALE and partly wrong. Commit `4433c5b` was the Haiku static export that
> **degraded** the client PWA and was **reverted** (see `CLAUDE.md` §9 incident). The
> actual outcome, verified live on 2026-07-01:
> - **Backend capability `pulso-financials-api` — LIVE & CORRECT.** `GET /api/v1/financials`
>   aggregates Shadow GL journal lines for Cliente Cero and returns real data
>   (e.g. `caja_real: 352000000`, `gastos_ayer: 90000000`). This part shipped as designed.
> - **Frontend capability `pulso-overview-live-data` — LIVE, but via a different path.** The
>   full client PWA was restored (commit `b6fcb81`) and the live Caja Real fetch was
>   re-applied as a client-side script in `app/overview.html` (commit `f91d9da`) after the
>   `4433c5b` regression. The Caja Real card on `contexia.online/app/overview` shows live
>   `/api/v1/financials` data today.
> - **Durability follow-up** (make `app/` regenerable from `contexia-app/` WITH the wiring
>   baked in, retiring the hand-edit) is tracked by the active change
>   **`reconcile-contexia-app-source-live-pwa`**.
>
> Both capabilities are satisfied in production, so this change is archived; the task
> checkboxes were never updated (tracking drift), not a sign the work is undone.

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
- [x] Contexia-app source compiled: `npx next build` → `out/`
- [x] Static export synced to `antigravity-app/app/` (build artifact; tracked in main)
- [x] Commit 4433c5b: added contexia-app static export with live CashTodayCard

### 4. Push to Production
- [x] Pushed main branch to GitHub
- [x] Railway auto-deploy triggered (commit: 4433c5b)
- [x] Backend `/api/v1/financials` should be live on https://antigravity-app-production-175a.up.railway.app

### 5. Frontend Deploy
- [x] Static export published to Vercel (contexia.online/app/)
- [x] Verified via curl: contexia.online/app/index.html responds with Next.js bundle
- [x] Redirect confirmed: `/app/index.html` → `/app/overview` (307)

### 6. Verification
- [x] Production URL responds: https://contexia.online/app/overview (live)
- [x] CashTodayCard component deployed (uses live fetchFinancials client)
- [x] Remaining screens show placeholders (Fiscal, Radar, Patrimonio, Flujo-Detalle)
- [x] API endpoint expected to return: caja_real, dinero_disponible, ventas_periodo, salidas_periodo, status

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
