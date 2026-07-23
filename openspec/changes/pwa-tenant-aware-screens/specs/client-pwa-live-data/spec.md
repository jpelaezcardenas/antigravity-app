## ADDED Requirements

### Requirement: Flujo-detalle liquidity bridge bound to live financials

The Flujo-detalle screen's `MonthlyLiquidityBridgeCard` SHALL fetch `GET
/api/v1/financials/liquidity-bridge` client-side instead of receiving a static `bridge` prop from
`flujoDetalleMock.liquidityBridge`, following the same self-feeding `"use client"` + `useEffect`
pattern as `CashTodayCard`, with amounts converted from COP minor units (cents) via `formatCop`.
The screen's other cards (`StructuralInsightCard`, `FlowCompositionCard`,
`FinancialHealthStatusGrid`) MAY continue to use mocks in this slice — no backend data with their
promised granularity exists.

#### Scenario: Live bridge replaces the mock
- **WHEN** the Flujo-detalle screen loads and the liquidity-bridge endpoint returns a `"ready"`
  snapshot
- **THEN** the card renders the live `initial_balance`/`inflows`/`outflows`/`final_balance` (÷100,
  formatted with `formatCop`) and SHALL NOT render `flujoDetalleMock.liquidityBridge`

#### Scenario: Loading state
- **WHEN** the liquidity-bridge request is in flight
- **THEN** the card SHALL render a loading indicator, not a stale or mock figure

#### Scenario: Unavailable state renders honestly, never a mock value
- **WHEN** the request fails, or returns `status: "empty"`
- **THEN** the card SHALL render an explicit "datos no disponibles" state and SHALL NOT render
  `flujoDetalleMock.liquidityBridge` or any other fabricated figure
