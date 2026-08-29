# pulso-diario-agent-insight Specification

## Purpose
Lets a local Hermes agent push a computed "Pulso Diario" insight for a tenant with no Shadow GL
data yet, used as a fallback source by `pulso-financials-api`'s `GET /api/v1/financials` when a
resolved tenant's Shadow GL computation is empty.

## Requirements

### Requirement: Hermes can push a completed Pulso Diario insight for a tenant

The system SHALL expose `POST /api/v1/agents/pulso-diario/insights`, gated by the same
`require_hermes_bridge_token` bearer-token dependency used by the existing Sell Machine bridge
routes. The request body SHALL include `tenant_id`, `caja_real`, `dinero_disponible`,
`ventas_ayer`, `gastos_ayer` (all monetary fields as integer COP minor units). On success, the
system SHALL persist this as a `completed` `operator_tasks` row with `task_type =
"pulso_diario_insight"`, without passing through the `pending`/`dispatched` states (there is no
prior request this responds to — the insight is unsolicited push data from a local agent running
on its own schedule).

#### Scenario: A valid bridge-token request creates a completed insight task
- **WHEN** a request with a valid bearer token and a well-formed payload is submitted
- **THEN** an `operator_tasks` row is created with `status = "completed"`,
  `task_type = "pulso_diario_insight"`, and `result` containing the submitted monetary fields

#### Scenario: A missing or invalid bridge token is rejected
- **WHEN** the request has no `Authorization` header, or a token that does not match
  `HERMES_BRIDGE_TOKEN`
- **THEN** the endpoint returns `401`, and no `operator_tasks` row is created

#### Scenario: An unknown tenant_id is rejected
- **WHEN** the submitted `tenant_id` does not exist in the `tenants` table
- **THEN** the endpoint returns an error and no `operator_tasks` row is created

### Requirement: The latest completed insight per tenant is queryable and tenant-isolated

The system SHALL provide a way to retrieve the most recent completed `pulso_diario_insight`
operator task for a given tenant, used internally by the `pulso-financials-api` fallback. Two
tenants' insights SHALL NEVER be conflated.

#### Scenario: The most recent insight is returned when multiple exist
- **WHEN** a tenant has two completed `pulso_diario_insight` tasks with different `created_at`
  timestamps
- **THEN** the lookup returns the one with the later `created_at`

#### Scenario: A tenant with no insight yields no result
- **WHEN** a tenant has no completed `pulso_diario_insight` tasks
- **THEN** the lookup returns nothing (not an error) for that tenant

#### Scenario: Tenant isolation
- **WHEN** tenant `T1` has a completed insight and tenant `T2` does not
- **THEN** looking up `T2`'s latest insight never returns `T1`'s data
