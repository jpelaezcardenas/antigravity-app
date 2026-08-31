## ADDED Requirements

### Requirement: Internal router authenticated by HERMES_BRIDGE_TOKEN
The system SHALL expose a `/internal/` route group protected by a `verify_hermes_token` FastAPI dependency. The dependency SHALL compare the `Authorization: Bearer <token>` header against the `HERMES_BRIDGE_TOKEN` environment variable using `secrets.compare_digest`. Any request without a matching token SHALL receive HTTP 403. If `HERMES_BRIDGE_TOKEN` is not set in the environment the dependency SHALL raise a startup error (fail closed — never open by default).

#### Scenario: Valid token accepted
- **WHEN** Hermes sends `GET /internal/pulso/all-active` with `Authorization: Bearer <HERMES_BRIDGE_TOKEN>`
- **THEN** the endpoint returns HTTP 200 with a JSON body

#### Scenario: Missing token rejected
- **WHEN** a request reaches `/internal/` without an `Authorization` header
- **THEN** the endpoint returns HTTP 403

#### Scenario: Invalid token rejected
- **WHEN** a request reaches `/internal/` with an incorrect Bearer token
- **THEN** the endpoint returns HTTP 403

#### Scenario: Missing env var fails closed
- **WHEN** `HERMES_BRIDGE_TOKEN` is not set in the environment
- **THEN** the application fails to start (startup validation error), not silently accepting all requests

---

### Requirement: Active PWA client resolver
The system SHALL provide `core/pwa_clients.py::get_active_pwa_clients(supabase_client)` that queries `b2b_clients` and returns a list of `ActiveClient` objects for clients where `status = 'activo'` AND `provision_status = 'provisioned'`. Each `ActiveClient` SHALL include at minimum: `company_id`, `tenant_id`, `nombre` (company display name).

#### Scenario: Multiple active clients returned
- **WHEN** Supabase has 3 rows in `b2b_clients` with `status='activo'` and `provision_status='provisioned'`
- **THEN** `get_active_pwa_clients()` returns a list of 3 `ActiveClient` objects

#### Scenario: Inactive clients excluded
- **WHEN** a `b2b_clients` row has `status='inactivo'`
- **THEN** that client is NOT included in the returned list

#### Scenario: Unprovisioned clients excluded
- **WHEN** a `b2b_clients` row has `status='activo'` but `provision_status='not_provisioned'`
- **THEN** that client is NOT included in the returned list

#### Scenario: Empty list on no active clients
- **WHEN** no `b2b_clients` rows match the active criteria
- **THEN** `get_active_pwa_clients()` returns an empty list without raising an error

---

### Requirement: Aggregated Pulso endpoint
The system SHALL expose `GET /internal/pulso/all-active` that calls `PulsoDiarioService` for each active client and returns a consolidated response with `clientes`, `total`, and `timestamp`.

#### Scenario: Returns data for all active clients
- **WHEN** Hermes calls `GET /internal/pulso/all-active` with a valid token and 2 active clients exist
- **THEN** the response body contains `clientes` array with 2 entries, each with `company_id`, `nombre`, and `pulso` payload
- **AND** `total` equals 2
- **AND** `timestamp` is an ISO 8601 UTC datetime string

#### Scenario: Empty client list returns valid response
- **WHEN** no active clients exist
- **THEN** the response is `{"clientes": [], "total": 0, "timestamp": "<iso>"}` with HTTP 200

#### Scenario: Per-client query filtered by tenant_id
- **WHEN** the aggregator fetches Pulso data for a client
- **THEN** the Supabase query includes an explicit `tenant_id` filter equal to that client's `tenant_id`
- **AND** data from other tenants is never included in that client's response entry

---

### Requirement: Aggregated Centinela endpoint
The system SHALL expose `GET /internal/centinela/all-active` that calls `CentinelaService` for each active client and returns a consolidated response with `clientes`, `total`, and `timestamp`.

#### Scenario: Returns alerts for all active clients
- **WHEN** Hermes calls `GET /internal/centinela/all-active` with a valid token
- **THEN** each entry in `clientes` contains `company_id`, `nombre`, and `centinela` payload with the client's active alerts

#### Scenario: Client with no alerts included with empty alerts list
- **WHEN** an active client has zero centinela alerts
- **THEN** that client appears in `clientes` with `centinela: {"alerts": []}`

---

### Requirement: Aggregated Radar endpoint
The system SHALL expose `GET /internal/radar/all-active` that calls `RadarService` for each active client.

#### Scenario: Returns radar data for all active clients
- **WHEN** Hermes calls `GET /internal/radar/all-active` with a valid token
- **THEN** each entry in `clientes` contains `company_id`, `nombre`, and `radar` payload

---

### Requirement: Aggregated Auditoría Sombra endpoint
The system SHALL expose `POST /internal/auditoria-sombra/all-active` that triggers `AuditoriaSombraService` in `mode="nightly"` for each active client. The endpoint SHALL call the underlying service directly, not via an internal HTTP self-call.

#### Scenario: Nightly audit triggered for all active clients
- **WHEN** Hermes calls `POST /internal/auditoria-sombra/all-active` with a valid token
- **THEN** `AuditoriaSombraService` is invoked once per active client with `mode="nightly"` and the client's `company_id`

---

### Requirement: Aggregated Social Ops endpoint
The system SHALL expose `GET /internal/social-ops/all-active` that calls `SocialOpsService.get_briefing()` for each active client.

#### Scenario: Returns briefing for all active clients
- **WHEN** Hermes calls `GET /internal/social-ops/all-active` with a valid token
- **THEN** each entry in `clientes` contains `company_id`, `nombre`, and `social_ops` payload

#### Scenario: Service not tenant-aware returns null payload gracefully
- **WHEN** `SocialOpsService.get_briefing()` raises an exception for a specific client
- **THEN** that client's entry contains `social_ops: null` and an `error` field with the error message
- **AND** the other clients' entries are unaffected
