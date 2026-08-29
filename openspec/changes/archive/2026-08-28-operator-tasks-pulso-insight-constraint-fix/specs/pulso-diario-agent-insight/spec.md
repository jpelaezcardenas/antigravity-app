## MODIFIED Requirements

### Requirement: Hermes can push a completed Pulso Diario insight for a tenant

The system SHALL expose `POST /api/v1/agents/pulso-diario/insights`, gated by the same
`require_hermes_bridge_token` bearer-token dependency used by the existing Sell Machine bridge
routes. The request body SHALL include `tenant_id`, `caja_real`, `dinero_disponible`,
`ventas_ayer`, `gastos_ayer` (all monetary fields as integer COP minor units). On success, the
system SHALL persist this as a `completed` `operator_tasks` row with `task_type =
"pulso_diario_insight"`, without passing through the `pending`/`dispatched` states (there is no
prior request this responds to — the insight is unsolicited push data from a local agent running
on its own schedule). The `operator_tasks.task_type` CHECK constraint SHALL permit
`"pulso_diario_insight"` as a valid value — this insert MUST NOT fail at the database layer.

#### Scenario: A valid bridge-token request creates a completed insight task
- **WHEN** a request with a valid bearer token and a well-formed payload is submitted
- **THEN** an `operator_tasks` row is created with `status = "completed"`,
  `task_type = "pulso_diario_insight"`, and `result` containing the submitted monetary fields
- **AND** the insert succeeds without violating the `task_type` CHECK constraint

#### Scenario: A missing or invalid bridge token is rejected
- **WHEN** the request has no `Authorization` header, or a token that does not match
  `HERMES_BRIDGE_TOKEN`
- **THEN** the endpoint returns `401`, and no `operator_tasks` row is created

#### Scenario: An unknown tenant_id is rejected
- **WHEN** the submitted `tenant_id` does not exist in the `tenants` table
- **THEN** the endpoint returns an error and no `operator_tasks` row is created
