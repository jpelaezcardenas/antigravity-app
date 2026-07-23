## MODIFIED Requirements

### Requirement: Overview Caja Real bound to live financials

The Overview (`/app/overview`) `CashTodayCard` SHALL display Caja Real from the live `GET
/api/v1/financials` response instead of `pulsoMock.cash`. The fetch SHALL run client-side and
target the configured Contexia backend base URL. The remaining Overview cards (note, health) MAY
continue to use mocks in this slice; alerts are covered by a separate requirement below.

#### Scenario: Live value replaces the mock
- **WHEN** the Overview screen loads and the financials endpoint returns `caja_real`
- **THEN** the card SHALL render the formatted live value in COP and SHALL NOT render the hardcoded
  `$42.850.000` mock

#### Scenario: Loading state
- **WHEN** the financials request is in flight
- **THEN** the card SHALL render a loading indicator and SHALL NOT render a stale or mock figure

#### Scenario: Error state renders honestly, never a mock value
- **WHEN** the financials request fails (network error or non-2xx response)
- **THEN** the card SHALL render an explicit, unobtrusive error state (e.g. "No pudimos actualizar
  tu Caja Real") and SHALL NOT render `pulsoMock.cash` or any other fabricated figure under a
  `"ready"`-looking state — this was previously violated by a silent mock fallback and is corrected
  by this change

#### Scenario: Empty state
- **WHEN** the endpoint returns `status` = `"empty"` with zero amounts
- **THEN** the card SHALL render an explicit "sin datos aún" empty state

## ADDED Requirements

### Requirement: Overview active alerts bound to the tenant-scoped alerts feed

The Overview `ActiveAlerts` section SHALL fetch `GET /api/v1/centinela/alerts` client-side instead
of receiving a static `alerts` prop from `pulsoMock.alerts`, following the same self-feeding
`"use client"` + `useEffect` pattern as `CashTodayCard`.

#### Scenario: Live alerts replace the mock
- **WHEN** the Overview screen loads and `GET /api/v1/centinela/alerts` returns one or more alerts
- **THEN** the section renders those alerts (mapped to the existing card UI) and SHALL NOT render
  `pulsoMock.alerts`

#### Scenario: No alerts or a fetch error renders nothing, not a mock or a crash
- **WHEN** the fetch returns zero alerts, or fails
- **THEN** the section renders nothing (matching the existing "hide when empty" behavior for
  `alerts.length === 0`) — it SHALL NOT fall back to `pulsoMock.alerts` and SHALL NOT crash the
  Overview screen
