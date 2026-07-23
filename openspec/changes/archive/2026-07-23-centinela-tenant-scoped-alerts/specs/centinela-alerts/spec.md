## ADDED Requirements

### Requirement: Alert persistence SHALL require an explicit tenant_id

`CentinelaService.save_alerts()` SHALL require an explicit `tenant_id` argument for every write to
`centinela_alerts` and SHALL NOT fall back to Cliente Cero (or any other implicit default) when one
is not supplied. The same rule applies to `centinela_resolution_service._alert_payload` /
`poll_shadow_gl_discrepancies`.

#### Scenario: Alert saved with an explicit tenant_id
- **WHEN** `save_alerts(alerts, tenant_id="tenant-medic")` is called with a non-empty `tenant_id`
- **THEN** every inserted row's `tenant_id` column equals `"tenant-medic"`
- **AND** no lookup of the Cliente Cero tenant is performed

#### Scenario: Alert save raises without a tenant_id
- **WHEN** `save_alerts(alerts, tenant_id=None)` or `save_alerts(alerts, tenant_id="")` is called
- **THEN** the system raises `TenantResolutionError` before any insert is attempted
- **AND** no row is written to `centinela_alerts`

#### Scenario: The tenant_id parameter is authoritative over a per-alert value
- **WHEN** an alert dict already contains its own `tenant_id` key different from the parameter
- **THEN** the parameter's value is stamped on the row, overriding the per-alert key

### Requirement: The evaluate endpoint SHALL resolve the caller's tenant before saving

`POST /api/v1/centinela/evaluate` SHALL resolve the authenticated caller's tenant using the same
3-branch pattern proven by `GET /api/v1/financials` (resolved tenant → use it; no-auth staging
identity → explicit Cliente Cero; authenticated-unresolved → degrade). It SHALL evaluate rules
regardless of tenant resolution (evaluation is pure) but SHALL only persist alerts when a tenant was
resolved.

#### Scenario: Authenticated caller with a resolved tenant saves under their own tenant
- **WHEN** an authenticated request with `resolved_tenant_id="tenant-medic"` calls `/evaluate` with
  `save_alerts=true`
- **THEN** any generated alerts are persisted with `tenant_id="tenant-medic"`
- **AND** the response's `save_skipped_reason` is `null`

#### Scenario: No-auth staging identity saves under the explicit Cliente Cero tenant
- **WHEN** `AUTH_ENFORCED=False` and no bearer token is supplied
- **THEN** the system resolves the real Cliente Cero tenant UUID explicitly
- **AND** persists any generated alerts under it

#### Scenario: Authenticated caller with an unresolved tenant does not persist
- **WHEN** an authenticated request has no `resolved_tenant_id`
- **THEN** the system still returns the evaluated alerts in the response body
- **AND** does NOT call `save_alerts`
- **AND** the response's `saved_alert_ids` is empty and `save_skipped_reason` is `"tenant_unresolved"`
- **AND** the Cliente Cero tenant resolver is never invoked for this request

#### Scenario: Unauthenticated request is rejected in production
- **WHEN** `AUTH_ENFORCED=True` and no valid bearer token is supplied
- **THEN** the endpoint returns `401 Unauthorized` before any evaluation or save occurs

### Requirement: Alert reads SHALL be scoped to the caller's tenant

`GET /api/v1/centinela/alerts/{company_id}` and `CentinelaService.get_alerts_for_company` SHALL
filter results by both `company_id` and the caller's resolved tenant. An authenticated caller whose
tenant does not resolve SHALL receive an empty result, never Cliente Cero's alerts.

#### Scenario: Caller sees only their own tenant's alerts
- **WHEN** an authenticated request with `resolved_tenant_id="tenant-medic"` calls
  `GET /alerts/{company_id}`
- **THEN** only rows matching both `company_id` and `tenant_id="tenant-medic"` are returned

#### Scenario: Two tenants sharing a company_id do not see each other's alerts
- **WHEN** tenant A and tenant B both have alerts stored against the same `company_id`
- **THEN** tenant A's request returns only tenant A's alerts
- **AND** tenant B's request returns only tenant B's alerts

#### Scenario: Authenticated caller with an unresolved tenant reads an empty list
- **WHEN** an authenticated request has no `resolved_tenant_id`
- **THEN** the response's `alert_count` is `0` and `source` is `"none"`
- **AND** the Cliente Cero tenant resolver is never invoked for this request

### Requirement: Internal alert readers SHALL filter by company_id AND tenant_id

`radar_service` and `pulso_diario_service`, which read `centinela_alerts` on behalf of a known
tenant, SHALL filter by both the correct `company_id` (resolved from the tenant, not the raw tenant
UUID) and the tenant's own `tenant_id`.

#### Scenario: Radar's alert factor is tenant-scoped
- **WHEN** Radar computes its risk factor for a tenant with alerts stored under its own `tenant_id`
- **THEN** the query includes an explicit `tenant_id` filter alongside the resolved `company_id`

#### Scenario: Pulso Diario's alert count uses the correct identity columns
- **WHEN** Pulso Diario computes today's alert count for a given tenant
- **THEN** the query resolves `tenants.id → tenants.company_id` before filtering (not the tenant
  UUID directly in the `company_id` column)
- **AND** also filters by `tenant_id`
- **AND** returns the tenant's real alert count instead of always `0`
