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

When the Shadow GL computation itself yields `status: "empty"` for a resolved tenant (the tenant
exists and was resolved, but has no `erp_journal_lines` rows), the system SHALL check for that
tenant's latest completed `pulso_diario_insight` operator task (see the `pulso-diario-agent-
insight` capability) before returning the zeroed snapshot. If one exists, the system SHALL return
its payload instead, with `status: "healthy"` and an additional `source: "agent_insight"` field.
This fallback SHALL NOT apply to the "no tenant resolved" case (an authenticated caller whose
tenant never resolved SHALL still receive the zeroed, non-leaking `_empty_snapshot()` regardless
of any operator task data that may exist for any tenant).

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

#### Scenario: An empty Shadow GL tenant with a completed agent insight gets that insight instead
- **WHEN** a resolved tenant's Shadow GL computation returns `status: "empty"` AND a completed
  `pulso_diario_insight` operator task exists for that tenant
- **THEN** the endpoint returns that task's result payload with `status: "healthy"` and
  `source: "agent_insight"`, instead of the zeroed empty snapshot

#### Scenario: An empty Shadow GL tenant with no agent insight still gets the zeroed empty snapshot
- **WHEN** a resolved tenant's Shadow GL computation returns `status: "empty"` AND no completed
  `pulso_diario_insight` operator task exists for that tenant
- **THEN** the endpoint returns the original zeroed `status: "empty"` snapshot, unchanged from
  prior behavior

#### Scenario: An unresolved tenant never receives an agent insight fallback
- **WHEN** an authenticated caller's tenant does not resolve at all
- **THEN** the endpoint returns the zeroed, non-leaking empty snapshot regardless of whether any
  operator task data exists for any tenant

### Requirement: Snapshot status classification

The system SHALL derive a `status` string from the snapshot using simple, deterministic rules so the UI can render tone without business logic.

#### Scenario: Healthy when cash is positive
- **WHEN** `caja_real` is greater than `0`
- **THEN** `status` SHALL be `"healthy"`

#### Scenario: Empty when no data exists
- **WHEN** there are no journal lines for the tenant
- **THEN** `status` SHALL be `"empty"`
