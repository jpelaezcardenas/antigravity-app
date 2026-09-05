## Why

`/app/radar` is currently a mock screen (Informe Técnico del Hub de Innovación) with no
real backend behind its cash-forecast narrative. The Shadow GL already computes Caja Real
daily for Pulso Diario — the same data can be aggregated weekly to give PyME owners a
13-week cash runway view (Agicap-style), the first module of the "Pulso Diario v2" cash
management roadmap. It closes the gap between "we show a mock chart" and "we show a real
projection with an honest confidence level," without touching the existing daily Pulso.

## What Changes

- New backend endpoint `GET /api/v1/radar/proyeccion-caja`, tenant-resolved from the
  authenticated caller (no query-param tenant), reusing the Shadow GL access pattern
  already in `services/radar_service.py::calculate_cashflow_forecast`.
- Projection methodology is `solo_historico` (weekly net-flux trend from
  `erp_journal_lines`/`dian_xml_documents`) — no accounts-receivable/payable tables with
  due dates exist in the data model today, so `historico_mas_cxc_cxp` is explicitly out of
  reach this sprint and the response says so via a `metodologia` field.
- Decreasing confidence per week band, capped at `"media"` (no `"alta"` claim without
  CxC/CxP grounding): weeks 1-4 `"media"`, weeks 5-13 `"baja"`.
- `impuesto_futuro_estimado` is returned as `null` with an explicit note — no real tax
  projection exists in the backend yet; it must not be mocked or invented.
- Honest empty state (`"sin_historico_suficiente"`) when a tenant has fewer than 4-8 weeks
  of `erp_journal_entries` — never fabricate a projection.
- New `/app/radar` section: 13-point line chart as plain inline SVG (reusing the technique
  already in `components/radar/CashProjectionCard.tsx` — no new dependency, per
  `contexia-app/CLAUDE.md`'s standing "no UI libraries without strong reason" rule) + a
  large "amiga contadora" narrative alert, mobile-first, confidence-coded. Documented as
  the 9th data-bound exception in `contexia-app/CLAUDE.md`.
- Adoption tracking is **descoped this sprint**: `contexia-app` has no existing
  analytics/tracking pattern to reuse (verified by grep — see tasks.md 6.2), and building
  one from scratch here would itself be an unauthorized new dependency. The "≥40% weekly
  adoption" KPI needs a deliberate, separate change to introduce tracking infrastructure.

## Non-Goals

- No multi-source/multi-gateway consolidation (depends on the Conciliador Multi-Pasarelas
  reaching real data first — future Module 2).
- No conversational scenario simulator via Taty (future Module 3).
- No rebalancing, payment, or execution action of any kind — this module is read/projection
  only, per the "Nous Never Approves" rule; nothing here writes to `approval_queue` as an
  actionable draft.
- No change to the existing `/api/v1/radar/risk-score` endpoint or to Pulso Diario
  (`/app/overview`) behavior.

## Capabilities

### New Capabilities
- `radar-cash-projection`: 13-week cash projection endpoint + `/app/radar` chart/narrative
  UI, tenant-scoped, `solo_historico` methodology with decreasing confidence and an honest
  insufficient-history state.

### Modified Capabilities
(none — `radar-predictivo` risk-score behavior is untouched; this is an additive sibling
endpoint in the same router)

## Impact

- Backend: `apps/backend/presentation/radar_endpoints.py` (new route),
  `apps/backend/services/radar_service.py` (new function, reused Shadow GL queries), new
  test file mirroring `test_radar_alert_count_tenant_scoping.py` for tenant isolation.
- Frontend: `contexia-app/` — new component(s) under `app/app/(shell)/radar/` (or wherever
  the existing `/app/radar` route lives in `contexia-app`), new dependency on `recharts`.
- No new tables/migrations — reads existing `erp_journal_entries`, `erp_journal_lines`,
  `dian_xml_documents`.
- Deploy: Railway (`antigravity-app-production-175a`) for the backend route, Vercel for the
  frontend build — Stage 11 required before archiving (CLAUDE.md §8).
