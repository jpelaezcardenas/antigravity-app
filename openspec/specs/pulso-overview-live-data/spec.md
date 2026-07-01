# pulso-overview-live-data Specification

## Purpose
TBD - created by archiving change wire-pulso-overview-live-shadow-gl. Update Purpose after archive.
## Requirements
### Requirement: Overview Caja Real bound to live financials

The Overview (`/app/overview`) `CashTodayCard` SHALL display Caja Real from the live `GET /api/v1/financials` response instead of `pulsoMock.cash`. The fetch SHALL run client-side and target the configured Contexia backend base URL. The remaining Overview cards (note, health, alerts) MAY continue to use mocks in this slice.

#### Scenario: Live value replaces the mock
- **WHEN** the Overview screen loads and the financials endpoint returns `caja_real`
- **THEN** the card SHALL render the formatted live value in COP and SHALL NOT render the hardcoded `$42.850.000` mock

#### Scenario: Loading state
- **WHEN** the financials request is in flight
- **THEN** the card SHALL render a loading indicator and SHALL NOT render a stale or mock figure

#### Scenario: Error state falls back gracefully
- **WHEN** the financials request fails (network or non-200)
- **THEN** the card SHALL render an unobtrusive error/placeholder state and SHALL NOT crash the screen or show a misleading mock value

#### Scenario: Empty state
- **WHEN** the endpoint returns `status` = `"empty"` with zero amounts
- **THEN** the card SHALL render an explicit "sin datos aún" empty state

### Requirement: Configurable API base URL

The frontend SHALL read the backend base URL from a build-time public environment variable (`NEXT_PUBLIC_API_BASE_URL`), defaulting to the Railway production URL, so local and production builds target different backends without code changes.

#### Scenario: Production build targets Railway backend
- **WHEN** the static export is built without overriding the variable
- **THEN** client fetches SHALL target the Railway production backend URL

#### Scenario: Local override
- **WHEN** `NEXT_PUBLIC_API_BASE_URL` is set to a local URL at build time
- **THEN** client fetches SHALL target that local URL

