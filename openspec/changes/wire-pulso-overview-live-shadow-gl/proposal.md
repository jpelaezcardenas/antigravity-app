## Why

The consumer app at `contexia.online/app` is a mock-only visual demo: the Pulso/Overview screen shows a hardcoded `$42.850.000` Caja Real from `lib/mock/pulso.ts` and never reflects real data. Meanwhile, manual file ingestion already works end-to-end — CSV Siigo and DIAN XML persist to the Shadow GL tables for Cliente Cero — but no production UI surfaces it. This change closes the loop for the single most important number (Caja Real), proving the MVP works with real ingested data before scaling to the other screens.

## What Changes

- Rebuild the orphaned `GET /api/v1/financials` endpoint to compute the Pulso cash snapshot from `erp_journal_lines` for the Cliente Cero tenant, instead of reading the non-existent `company_financials` table.
  - `caja_real` = balance of bank account `1110` (sum of debits − credits).
  - `ventas_periodo` = sum of credits on income accounts (`4100`, `4105`) in the period.
  - `salidas_periodo` = sum of debits on expense accounts (`5xxx`, `6xxx`) in the period.
  - All amounts returned as integer COP minor units.
- Convert the `CashTodayCard` on `contexia-app` Overview from `pulsoMock.cash` to a client-side `fetch` of `/api/v1/financials`, with loading / error / empty states. (Static export `output:export` supports browser fetch.)
- **BREAKING (charter):** Supersede the `contexia-app` "sin backend, sin fetch, sin DB" rule for data-bound screens; introduce an API base-URL config pointing at the Railway production backend.
- Deploy (Stage 11): rebuild the static export, sync `out/` into `app/`, redeploy, and verify the live Caja Real reflects ingested Shadow GL data.

## Capabilities

### New Capabilities
- `pulso-financials-api`: Backend endpoint that aggregates the Pulso cash snapshot (Caja Real, ventas, salidas) from Shadow GL journal lines for the Cliente Cero tenant.
- `pulso-overview-live-data`: Frontend Overview Caja Real card bound to live financials data via client-side fetch, replacing the mock value, with loading/error/empty states.

### Modified Capabilities
<!-- None: no existing spec's requirements change. The orphaned financials endpoint has no spec. -->

## Impact

- **Backend**: `apps/backend/presentation/financials_endpoints.py` (rewritten), new aggregation logic/service, new tests (TDD). No DB migration (reads existing Shadow GL tables).
- **Frontend**: `contexia-app` (branch `temp-layout-fix` — must become canonical) — `app/app/overview/page.tsx`, `components/pulso/CashTodayCard.tsx`, new API client + base-URL config, updated `CLAUDE.md` charter.
- **Build/Deploy**: rebuild `contexia-app` static export → sync to `antigravity-app/app/` → redeploy (Railway/static host). CORS already allows `contexia.online`.
- **Out of scope**: Fiscal / Radar / Patrimonio screens stay on mocks (future slices); no auth changes; no write paths.
