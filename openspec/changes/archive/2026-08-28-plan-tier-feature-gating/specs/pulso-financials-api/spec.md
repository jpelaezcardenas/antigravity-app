## MODIFIED Requirements

### Requirement: Pulso financials snapshot from Shadow GL

The system SHALL expose `GET /api/v1/financials` returning a cash snapshot for the Cliente Cero tenant, computed deterministically from `erp_journal_lines`. The tenant SHALL be resolved server-side via `is_cliente_cero = true`; the client SHALL NOT supply a tenant or company id. All monetary fields SHALL be returned as integer COP minor units (cents).

The response SHALL include: `caja_real`, `dinero_disponible`, `ventas_periodo`, `salidas_periodo`, and `status`.

Before computing the snapshot for a resolved tenant, the system SHALL check whether that tenant's
`plan_tier` includes the `pulso_diario` feature (via `core/plan_features.py::has_feature`). If not,
the endpoint SHALL return a `not_in_plan`-shaped response instead of computing the snapshot. As of
this change, every plan tier (including `freemium`) includes `pulso_diario`, so this check is a
no-op in practice today — it exists so a future tier that excludes `pulso_diario` does not require
touching this endpoint again.

#### Scenario: Caja Real equals bank account balance
- **WHEN** the Cliente Cero ledger has lines on account `1110` (Bancos) totaling 11,250,000.00 in debits and 7,730,000.00 in credits
- **THEN** `caja_real` SHALL equal `352000000` (i.e., 3,520,000.00 COP) expressed in minor units (`sum(debit_minor) - sum(credit_minor)` for account `1110`)

#### Scenario: Ventas period sums income credits
- **WHEN** the snapshot is computed for the current calendar month
- **THEN** `ventas_periodo` SHALL equal the sum of `credit_minor` over lines whose `account_code` is in the income set (`4100`, `4105`) with an entry date in that month

#### Scenario: Salidas period sums expense debits
- **WHEN** the snapshot is computed for the current calendar month
- **THEN** `salidas_periodo` SHALL equal the sum of `debit_minor` over lines whose `account_code` starts with `5` or `6` with an entry date in that month

#### Scenario: Empty ledger returns zeroes, not an error
- **WHEN** the Cliente Cero tenant has no journal lines
- **THEN** the endpoint SHALL return `200` with all monetary fields equal to `0` and `status` = `"empty"`

#### Scenario: No tenant/company id required from client
- **WHEN** the request is made with no query parameters
- **THEN** the endpoint SHALL resolve the Cliente Cero tenant server-side and return its snapshot

#### Scenario: A tenant without the pulso_diario feature gets an explicit not_in_plan response
- **WHEN** a resolved tenant's `plan_tier` does not include the `pulso_diario` feature (not
  reachable by any tier that exists as of this change, but exercised by tests via a stubbed
  `has_feature`)
- **THEN** the endpoint returns a `not_in_plan`-shaped response instead of computing a snapshot,
  and does not query `erp_journal_lines`

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

Before computing the bridge for a resolved tenant, the system SHALL check whether that tenant's
`plan_tier` includes the `liquidity_bridge` feature (via `core/plan_features.py::has_feature`). A
`freemium` tenant does not include this feature; the endpoint SHALL return a `not_in_plan`-shaped
response (`status: "not_in_plan"`) instead of computing the bridge, and SHALL NOT query
`erp_journal_lines` in that case.

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

#### Scenario: A freemium tenant gets an explicit not_in_plan response, never a zeroed bridge
- **WHEN** a resolved tenant's `plan_tier` is `"freemium"` calls `GET
  /api/v1/financials/liquidity-bridge`
- **THEN** the response is `{ initial_balance: 0, inflows: 0, outflows: 0, final_balance: 0,
  period: "YYYY-MM", status: "not_in_plan" }`, distinct from the `"empty"` status used when a
  paid tenant genuinely has no ledger activity
