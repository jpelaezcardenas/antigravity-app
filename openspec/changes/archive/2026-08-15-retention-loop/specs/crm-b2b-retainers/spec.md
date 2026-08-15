## MODIFIED Requirements

### Requirement: CRM/Ventas Búnker section renders the live B2B grid
The Búnker "CRM / Ventas" section SHALL render a tab shell with a "B2B / Retainers" tab showing the
live client × month grid and totals sourced from `GET /api/v1/crm/b2b/payments`, a retention-alerts
panel sourced from `GET /api/v1/crm/b2b/retention-alerts` (retention-loop), and a "B2C / Renta
Natural" tab present as a placeholder only. The section SHALL show explicit loading, error, and
data-source states and SHALL NOT display the previous static mock client list.

#### Scenario: Admin opens CRM/Ventas and sees live data
- **WHEN** an authenticated admin navigates to `/app/bunker` and selects "CRM / Ventas" → "B2B /
  Retainers"
- **THEN** the grid renders the 10 real clients across Jan–Jun 2026 with correct totals, and no
  reference to the old mock clients (e.g. "Contexia Marketing", "Studio 4") remains

#### Scenario: Backend unreachable shows an explicit error state, not a blank screen
- **WHEN** the B2B endpoints are unreachable from the frontend
- **THEN** the "B2B / Retainers" tab shows a visible error message rather than rendering blank or
  throwing

#### Scenario: The retention-alerts panel shows current at-risk clients
- **WHEN** the retention-alerts endpoint returns one or more current alerts
- **THEN** the "B2B / Retainers" tab's alerts panel lists each at-risk client with its alert type
  and message

#### Scenario: No current alerts shows an explicit empty state, not a blank panel
- **WHEN** the retention-alerts endpoint returns no current alerts
- **THEN** the panel shows an explicit "no alerts" state rather than rendering blank
