# Spec — Agent Operations Governance

## ADDED Requirements

### Requirement: JWT identity resolution to canonical tenant/user identifiers
The system SHALL resolve the caller's JWT identifiers to the canonical UUIDs used by the governance tables (`usuarios.id`, `tenants.id`) before performing the tenant-membership check, the cost recording, or the audit write. User identity SHALL be resolved by `usuarios.email`, falling back to the JWT `sub` when it is already a UUID. Tenant identity SHALL be resolved from the JWT `workspace_id` as a UUID, else as `tenants.company_id`, else from the caller's single active `user_tenants` membership. If either identity cannot be resolved unambiguously, the system SHALL treat the invocation as `blocked` (reason `identity_unresolved`) and SHALL NOT execute the agent.

#### Scenario: String JWT identities are resolved to UUIDs
- **WHEN** a user authenticates with a JWT whose `sub` is a non-UUID string (e.g. a demo id) and whose `email` matches a `usuarios` row, and whose `workspace_id` matches a `tenants.company_id`
- **THEN** the system resolves the user to `usuarios.id` and the tenant to `tenants.id`
- **AND** the membership check, cost recording, and audit row all use those resolved UUIDs

#### Scenario: Unresolvable identity is blocked
- **WHEN** the caller's user or tenant identity cannot be resolved to a canonical UUID
- **THEN** the agent does NOT execute and the result is `blocked` with reason `identity_unresolved`

#### Scenario: Tenant derived from membership when workspace claim is unusable
- **WHEN** the JWT `workspace_id` is neither a valid tenant UUID nor a known `company_id`, but the resolved user has exactly one active `user_tenants` membership
- **THEN** the system uses that membership's `tenant_id` as the canonical tenant

### Requirement: Tenant membership enforcement on agent invocation
The system SHALL verify, before executing any agent, that the calling `user_id` is a member of the requested `tenant_id` (i.e. exists in `user_tenants` with that `tenant_id`). If membership cannot be confirmed, the system SHALL NOT execute the agent and SHALL return a `blocked` result.

#### Scenario: Member invokes an agent in their own tenant
- **WHEN** a user who belongs to tenant `T` invokes the `pulso` agent with `tenant_id = T`
- **THEN** the access-control gate passes and the agent executes
- **AND** an `agent_operations` row is recorded with `status = "success"`

#### Scenario: Non-member is blocked from another tenant
- **WHEN** a user who belongs only to tenant `A` invokes any agent with `tenant_id = B`
- **THEN** the agent does NOT execute
- **AND** the WebSocket response is an `agent_error` with a permission-denied message
- **AND** an `agent_operations` row is recorded with `status = "blocked"` and `cost = 0`

#### Scenario: Missing tenant context is rejected
- **WHEN** an invocation arrives with no resolvable `tenant_id` (absent `workspace_id`)
- **THEN** the agent does NOT execute and the result is `blocked`

### Requirement: Per-operation audit logging
The system SHALL persist every agent invocation attempt to the `agent_operations` table, capturing `agent_name`, `user_id`, `tenant_id`, `operation_type`, `status` (one of `success`, `failed`, `blocked`), `duration_ms`, `cost`, `input_data`, `output_data`, and `error_message` when present. An audit-write failure SHALL NOT fail the user-facing agent call.

#### Scenario: Successful operation is logged with timing
- **WHEN** an agent executes successfully
- **THEN** an `agent_operations` row exists with `status = "success"`, a non-null `duration_ms`, and the resolved `cost`

#### Scenario: Failed agent execution is logged
- **WHEN** an agent endpoint returns an error or raises
- **THEN** an `agent_operations` row exists with `status = "failed"` and a populated `error_message`
- **AND** the WebSocket still returns a structured error to the client

#### Scenario: Audit write failure does not break the call
- **WHEN** the `agent_operations` insert fails (e.g. DB unavailable)
- **THEN** the agent result is still returned to the client
- **AND** the failure is logged server-side (not raised to the user)

### Requirement: Agent operation cost recording
The system SHALL resolve a deterministic cost for each agent operation from a versioned cost matrix and record it on the `agent_operations.cost` column for that invocation, scoped by `tenant_id`. Unknown operations SHALL resolve to a documented default cost rather than failing. (There is no separate `cost_tracking` table in this database; per-tenant cost reporting is an aggregation over `agent_operations`.)

#### Scenario: Known operation records its matrix cost
- **WHEN** the `centinela` agent runs operation `generate_draft`
- **THEN** the `agent_operations` row for that invocation has `cost` equal to the matrix cost for `centinela:generate_draft`

#### Scenario: Unknown operation uses the default cost
- **WHEN** an agent runs an operation absent from the cost matrix
- **THEN** the default cost is recorded and no error is raised

#### Scenario: Blocked operation records zero cost
- **WHEN** an invocation is blocked by the access-control gate
- **THEN** the recorded `cost` is 0

### Requirement: Cost surfaced in WebSocket response (backward compatible)
The system SHALL include `cost` (this operation) and `session_cost` (accumulated for the connection) in the `agent_output` WebSocket message, while preserving the existing `status`, `agent`, and `data` fields unchanged.

#### Scenario: Response carries cost without breaking existing fields
- **WHEN** an agent returns output over WebSocket
- **THEN** the message contains `data` exactly as before
- **AND** additionally contains numeric `cost` and `session_cost` fields

### Requirement: Cross-tenant isolation of audit and cost data
The system SHALL ensure that agent operation and cost records of one tenant are not readable by users of another tenant. `agent_operations` SHALL have RLS enabled with a tenant-isolation SELECT policy, and full audit visibility SHALL be limited to `admin`/`finance` roles.

#### Scenario: Tenant A cannot read tenant B operations
- **WHEN** a tenant-A user queries agent operations under tenant-A scope
- **THEN** no tenant-B `agent_operations` rows are returned

#### Scenario: Non-privileged role cannot read full audit
- **WHEN** a user without `admin` or `finance` role requests the full audit view
- **THEN** access is denied / rows are not returned
