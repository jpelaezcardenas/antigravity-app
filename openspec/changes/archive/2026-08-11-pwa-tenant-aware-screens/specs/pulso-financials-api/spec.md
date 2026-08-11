## ADDED Requirements

### Requirement: Monthly liquidity bridge derived from Caja Real ledger

The system SHALL expose `GET /api/v1/financials/liquidity-bridge`, tenant-scoped identically to
`GET /api/v1/financials` (own resolved tenant; Cliente Cero only for the staging identity; empty
for an authenticated caller with no resolved tenant). It SHALL compute, for the current calendar
month, from account `1110` (Bancos) lines in `erp_journal_lines`: `initial_balance` (cumulative
1110 balance as of the day before the month starts), `inflows` (sum of 1110 debits within the
month), `outflows` (sum of 1110 credits within the month), and `final_balance` (`initial_balance +
inflows - outflows`). All amounts SHALL be integer COP minor units (cents). `final_balance` SHALL
equal the cumulative 1110 balance as of the last day of the month (the same computation
`/financials`'s `caja_real` uses for that date) — the two independently-derived values SHALL NOT
diverge.

#### Scenario: Final balance matches the equivalent Caja Real balance
- **WHEN** the liquidity bridge is computed for a tenant for the current month
- **THEN** `final_balance` equals `caja_real` as `/financials` would report it if `as_of_date` were
  the last day of that month

#### Scenario: Empty tenant returns a zeroed, non-error snapshot
- **WHEN** the resolved tenant has no `erp_journal_lines` rows on account `1110` at all
- **THEN** the response is `{ initial_balance: 0, inflows: 0, outflows: 0, final_balance: 0,
  period: "YYYY-MM", status: "empty" }`, not a 4xx/5xx error

#### Scenario: Tenant isolation
- **WHEN** tenant `T1` and tenant `T2` both have account-`1110` movements in the current month
- **THEN** `T1`'s bridge reflects only `T1`'s lines and `T2`'s bridge reflects only `T2`'s lines

### Requirement: Synthetic Shadow GL "yesterday" rows stay fresh via rolling reseed

The synthetic per-client Shadow GL seed (migration `0028_seed_client_tenants_and_shadow_gl.sql`)
SHALL be kept demo-fresh by a daily process that re-dates each tenant's `SYNTH-*-SALE` and
`SYNTH-*-EXPENSE` `erp_journal_entries` row (identified by `external_reference_id` suffix and the
`memo` prefix `SYNTH:per-tenant-client-access`) to `entry_date = CURRENT_DATE - 1`. The
`SYNTH-*-OPEN` opening-balance row SHALL NOT be re-dated by this process.

#### Scenario: Ventas/gastos de ayer never go stale
- **WHEN** one or more days have elapsed since the synthetic seed or the last reseed run
- **THEN** each client tenant's `SYNTH-*-SALE` and `SYNTH-*-EXPENSE` rows are dated exactly
  yesterday relative to the current date, so `/financials`'s `ventas_ayer`/`gastos_ayer` remain
  non-zero for tenants that were seeded

#### Scenario: Opening balance is never disturbed by the reseed
- **WHEN** the daily reseed runs
- **THEN** `SYNTH-*-OPEN` rows keep their original `entry_date`, and the cumulative `caja_real`
  balance for each tenant is unaffected by the reseed
