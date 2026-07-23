## Why

`per-tenant-client-access` (archived 2026-07-22) made `CashTodayCard` (Pulso/Overview) show each
B2B client's real Caja Real. Every other end-user PWA surface still renders identical static mocks
from `contexia-app/lib/mock/*`: a logged-in client (e.g. Medic) sees their real cash next to
invented alerts (`pulsoMock.alerts`) and an invented liquidity bridge
(`flujoDetalleMock.liquidityBridge`) — the same fabricated numbers every other client sees. The
brief that kicked off this change assumed two sibling changes
(`centinela-tenant-scoped-alerts`, `agent-endpoints-real-tenant-filtering`) had already made the
backend tenant-aware for these surfaces; verified against `git log main` and
`openspec/changes/` — **neither exists**. `GET /api/v1/financials` remains the only tenant-aware
endpoint in the backend. This change does its own backend tenant-scoping for the two screens in
scope, rather than assuming it.

Separately: the synthetic Shadow GL seed (migration 0028, `per-tenant-client-access`) dated its
"yesterday" sale/expense rows relative to 2026-07-22. `ventas_ayer`/`gastos_ayer` are already back
to $0 for every client. Without a rolling reseed, every future demo shows a dead card.

Also found in scope (violates the already-archived `pulso-overview-live-data` spec, which requires
the error state to never show "a misleading mock value"): `CashTodayCard`'s fetch-error handler
silently falls back to `pulsoMock.cash` (the fabricated `$42.850.000`) while reporting `ready`
status. A real client hitting a transient backend error today sees fabricated money, not an error
state. This change brings the code into compliance with its own existing spec.

## What Changes

- `GET /api/v1/centinela/alerts` (new, alongside the existing unauthenticated
  `/centinela/alerts/{company_id}` used by the Hermes tool — untouched): tenant-scoped via
  `Depends(get_current_user)`, same resolution policy as `/financials` (own tenant / Cliente Cero
  for the staging identity / empty for an authenticated-but-unresolved caller — **never** Cliente
  Cero's alerts leaked to an unrelated client). No demo fallback on this route.
- `GET /api/v1/financials/liquidity-bridge`: new endpoint + service function, tenant-scoped
  identically, computing initial/final balance and inflows/outflows for account `1110` (Bancos)
  over the current month from `erp_journal_lines` — the same ledger `/financials` already
  aggregates.
- `components/pulso/ActiveAlerts.tsx` becomes self-feeding (`"use client"` + `useEffect`,
  `lib/api-client.ts::fetchCentinelaAlerts`), replacing its `alerts` prop.
- `components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx` becomes self-feeding
  (`fetchLiquidityBridge`), replacing its `bridge` prop.
- `CashTodayCard`'s error path stops falling back to `pulsoMock.cash`; renders an explicit,
  honest error state instead (bringing the code in line with the `pulso-overview-live-data` spec
  that already requires this).
- Migration `0033_rolling_reseed_synthetic_shadow_gl.sql`: one-shot re-date of the `SYNTH-*-SALE`
  / `SYNTH-*-EXPENSE` rows to `CURRENT_DATE - 1`, plus a daily pg_cron job doing the same, so the
  demo data stays fresh without manual intervention. `SYNTH-*-OPEN` rows (opening balance) are
  untouched.

## Non-goals (stays mock — no backend data with the promised granularity exists)

- `HealthQuadrant` (Pulso health KPIs) — no backend health-score computation exists.
- Fiscal/Centinela screen's other four cards (`ExAnteDetectionCard`, `ShadowAuditCard`,
  `TaxThresholdsCard`, `TatyEscalationCard`) — no backend source.
- Radar (all cards) — `radar_service.py` computes real per-tenant risk scores but not the
  scenario/projection shape the mock promises; out of scope for this wave.
- Patrimonio (all cards) — no `patrimonio` endpoint or data model exists at all.
- Flujo-detalle's `FlowCompositionCard` (operación/inversión/financiación %) and
  `FinancialHealthStatusGrid` — no account classification for this breakdown exists; only the
  Liquidity Bridge (account `1110` only) is honestly computable from today's Shadow GL.

Per `contexia-app/CLAUDE.md`'s hard rule: never relabel data that doesn't have the promised
granularity. Where the backend can't honestly support a card, it stays mock.

## Capabilities

### New Capabilities
(none — this modifies existing capabilities only)

### Modified Capabilities
- `centinela-alerts`: adds the tenant-scoped `GET /api/v1/centinela/alerts` read route.
- `pulso-financials-api`: adds `GET /api/v1/financials/liquidity-bridge` and the rolling reseed of
  synthetic Shadow GL data.
- `pulso-overview-live-data`: `ActiveAlerts` becomes data-bound; `CashTodayCard`'s error state is
  corrected to match this capability's own existing spec.
- `client-pwa-live-data`: `MonthlyLiquidityBridgeCard` (Flujo-detalle) becomes data-bound.

## Impact

- Backend: `apps/backend/presentation/centinela_endpoints.py`,
  `apps/backend/presentation/financials_endpoints.py`,
  `apps/backend/services/financials_service.py`, `apps/backend/core/tenant_context.py` (new
  shared resolver, extracted from `financials_endpoints.py`), `apps/backend/migrations/0033_*.sql`,
  two new test files.
- Frontend (`contexia-app/` canonical source only — `app/` build artifact never hand-edited):
  `lib/config.ts`, `lib/api-client.ts`, `components/pulso/ActiveAlerts.tsx`,
  `components/pulso/CashTodayCard.tsx`, `components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx`,
  the two page files that currently pass props into these components, `public/sw.js`
  (`CACHE_VERSION` bump), `contexia-app/CLAUDE.md` (data-bound screens list).
- No breaking changes to any existing public contract; `/centinela/alerts/{company_id}` (Hermes)
  and `/financials` (existing shape) are unchanged.
