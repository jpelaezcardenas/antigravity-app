### Requirement: B2B client roster is persisted and queryable
The system SHALL persist a roster of Contexia's B2B retainer clients (`b2b_clients`), scoped to the
Cliente Cero tenant, with at least `name`, `status` (`activo` | `inactivo`), and an optional nominal
`monthly_fee_cents`. The roster SHALL be retrievable via `GET /api/v1/crm/b2b/clients`.

#### Scenario: Listing clients returns all seeded B2B clients
- **WHEN** an admin calls `GET /api/v1/crm/b2b/clients` with `CRM_CANONICAL` enabled and Supabase
  reachable
- **THEN** the response includes `source: "supabase"` and an `items` array containing all 10 seeded
  clients with their `id`, `name`, `status`

#### Scenario: Supabase unreachable falls back to demo data
- **WHEN** `GET /api/v1/crm/b2b/clients` is called and Supabase credentials are not configured or the
  query fails
- **THEN** the response includes `source: "demo_fallback"` and a non-empty `items` array, and the
  request does not error

### Requirement: B2B payment history is a normalized, per-month ledger
The system SHALL persist one row per `(client, calendar month)` in `b2b_payments`, with
`amount_cents`, tied to a `b2b_clients` row. The system SHALL guarantee at most one payment row per
client per period (uniqueness constraint) so re-seeding is idempotent.

#### Scenario: Seed data matches the source ledger
- **WHEN** the January–June 2026 seed migration is applied
- **THEN** each of the 10 clients has exactly the payment rows matching its source monthly amounts,
  and Repuestos Don Álvaro's March 2026 amount is 1,200,000 COP (not 12,000,000 COP)

#### Scenario: Re-applying the seed does not duplicate rows
- **WHEN** the seed migration is applied a second time
- **THEN** the total row count in `b2b_payments` is unchanged and amounts remain correct (upsert, not
  insert)

### Requirement: B2B payment grid is computed server-side
The system SHALL expose `GET /api/v1/crm/b2b/payments` returning a grid shaped for direct rendering:
the set of clients, the set of periods in range, a cell lookup of `amount_cents` by client and
period, and totals (grand total, by period, by client).

#### Scenario: Grid totals match the sum of underlying payments
- **WHEN** an admin calls `GET /api/v1/crm/b2b/payments` for the Jan–Jun 2026 range
- **THEN** the returned `totals.grand_total` equals the sum of all `b2b_payments.amount_cents` for
  that range, and `totals.by_client[client_id]` equals the sum of that client's payments in range

### Requirement: B2B retainer data is admin-only
Access to `b2b_clients` and `b2b_payments` at the database layer SHALL be restricted by Row Level
Security to users with an admin-tier role (`admin`, `superadmin`, or `contexia_admin`) on the owning
tenant.

#### Scenario: Non-admin database role cannot read B2B tables directly
- **WHEN** a Supabase query against `b2b_clients` or `b2b_payments` is executed as a user without an
  admin-tier `user_roles.role` entry for the tenant
- **THEN** Row Level Security denies the read (no rows returned)

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
