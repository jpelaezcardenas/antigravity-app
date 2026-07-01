## 1. Backend — financials aggregation (TDD)

- [ ] 1.1 Write failing tests for the Shadow GL cash aggregation: `caja_real` = account `1110` (sum debit_minor − sum credit_minor), `ventas_periodo` = income credits (`4100`,`4105`) in current month, `salidas_periodo` = expense debits (`5xxx`,`6xxx`) in current month, empty-ledger → all `0` + `status="empty"`. Use Cliente Cero tenant fixture.
- [ ] 1.2 Implement the aggregation in a service function (e.g. `services/financials_service.py`) reading `erp_journal_lines` joined to `erp_journal_entries`, resolving tenant via `is_cliente_cero = true` (reuse the `_resolve_tenant_id` pattern). Return integer COP minor units.
- [ ] 1.3 Implement `status` classification (`healthy` when `caja_real > 0`, `empty` when no lines) per spec.
- [ ] 1.4 Rewrite `apps/backend/presentation/financials_endpoints.py` `GET /api/v1/financials` to call the service; preserve existing keys (`caja_real`, `dinero_disponible`, `status`) and add `ventas_periodo`, `salidas_periodo`. Remove the `company_financials`/`a0a0a0a0` path.
- [ ] 1.5 Run backend tests → green. Verify locally with `curl` against the live Cliente Cero data (Caja Real ≠ mock).

## 2. Frontend — Overview Caja Real live (contexia-app)

- [ ] 2.1 Add API base-URL config reading `NEXT_PUBLIC_API_BASE_URL`, defaulting to the Railway production URL (`lib/config.ts` or similar).
- [ ] 2.2 Add a typed financials client + response type in `lib/` that calls `GET /api/v1/financials`.
- [ ] 2.3 Convert `components/pulso/CashTodayCard.tsx` to `"use client"` and bind Caja Real to the live fetch, with loading / error / empty states per spec. Keep other Overview cards on mocks.
- [ ] 2.4 Update `app/app/overview/page.tsx` to pass live data into `CashTodayCard` (other cards unchanged).
- [ ] 2.5 Update `contexia-app/CLAUDE.md` charter: data-bound screens MAY fetch read-only snapshots from the Contexia backend (scoped supersede of the no-fetch rule).
- [ ] 2.6 Run `next build` (static export) locally; confirm the Overview card fetches and renders without console errors.

## 3. Source-of-truth & build sync

- [ ] 3.1 Land the `contexia-app` source (branch `temp-layout-fix`) onto the canonical branch (`main`) so the deployed export is reproducible from `main`.
- [ ] 3.2 Document/confirm the build → `antigravity-app/app/` sync step (manual or script) so `app/` is regenerated from `main`, not hand-edited.

## 4. Verification

- [ ] 4.1 E2E against Cliente Cero real data: ingest a known CSV, hit `/api/v1/financials`, assert `caja_real` matches the ledger.
- [ ] 4.2 Frontend states verified: loading, success (live value), error fallback, empty.

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/overview
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main (backend endpoint + contexia-app source + rebuilt `app/` export)
- [ ] 11.2 Static export published: `contexia.online/app/overview` serves the new bundle (hard refresh / bundle version bump)
- [ ] 11.3 Railway deploy active: backend `/api/v1/financials` returns the live snapshot in production
- [ ] 11.4 Production URL: Caja Real on `/app/overview` reflects real ingested Shadow GL data (NOT the `$42.85M` mock); confirm the network call to `/api/v1/financials` fires
- [ ] 11.5 Create report: `openspec/changes/wire-pulso-overview-live-shadow-gl/reports/YYYY-MM-DD-deployment.md`
