## ADDED Requirements

### Requirement: Pulso financials snapshot from Shadow GL

The system SHALL expose `GET /api/v1/financials` returning a cash snapshot for the Cliente Cero tenant, computed deterministically from `erp_journal_lines`. The tenant SHALL be resolved server-side via `is_cliente_cero = true`; the client SHALL NOT supply a tenant or company id. All monetary fields SHALL be returned as integer COP minor units (cents).

The response SHALL include: `caja_real`, `dinero_disponible`, `ventas_periodo`, `salidas_periodo`, and `status`.

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

### Requirement: Snapshot status classification

The system SHALL derive a `status` string from the snapshot using simple, deterministic rules so the UI can render tone without business logic.

#### Scenario: Healthy when cash is positive
- **WHEN** `caja_real` is greater than `0`
- **THEN** `status` SHALL be `"healthy"`

#### Scenario: Empty when no data exists
- **WHEN** there are no journal lines for the tenant
- **THEN** `status` SHALL be `"empty"`
