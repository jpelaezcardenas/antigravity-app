## ADDED Requirements

### Requirement: Hermes can discover pending operator tasks
The system SHALL expose `GET /api/v1/sell-machine/tasks/pending`, returning `operator_tasks` rows
with `status='pending'`, ordered oldest-first, each row carrying an explicit `tenant_id` field so
Hermes knows which tenant it is working for, so Hermes can poll for work without any inbound
connection from the cloud backend to Hermes. The endpoint SHALL accept an optional `tenant_id`
query parameter to filter results to a single tenant.

#### Scenario: Listing pending tasks returns unclaimed work with tenant_id
- **WHEN** Hermes calls `GET /api/v1/sell-machine/tasks/pending`
- **THEN** the response includes every `operator_tasks` row currently `status='pending'`, each
  with its `id`, `tenant_id`, `task_type`, `payload`, `status`, and `created_at`

#### Scenario: Filtering pending tasks by tenant
- **WHEN** Hermes calls `GET /api/v1/sell-machine/tasks/pending?tenant_id=<tenant-uuid>`
- **THEN** the response includes only `operator_tasks` rows with that `tenant_id`

### Requirement: Read-only task types can be created directly, without an approval draft
The system SHALL expose `POST /api/v1/sell-machine/tasks`, which SHALL create a new
`operator_tasks` row with `status='pending'` when `task_type` is one of `research`,
`metrics_pull`, `external_integration`, or `generate_doc`, and SHALL reject the request with a 400
error when `task_type` is `post_content` or `run_ads_ab` (side-effecting types, which require the
dispatch flow below). The request MAY include a `tenant_id`; when provided, the system SHALL
validate that a `tenants` row with that id exists and reject the request with a 404 error
otherwise. When `tenant_id` is omitted, the system SHALL fall back to the Cliente Cero tenant and
SHALL log a warning recording that an explicit tenant was not supplied.

#### Scenario: Creating a research task with an explicit tenant succeeds
- **WHEN** an admin calls `POST /api/v1/sell-machine/tasks` with
  `{"task_type": "research", "payload": {...}, "tenant_id": "<real-tenant-uuid>"}`
- **THEN** a new `operator_tasks` row is created with `status='pending'` and `tenant_id` equal to
  the supplied value, and no corresponding Approval Queue row is required or created

#### Scenario: Creating a task with an unknown tenant_id is rejected
- **WHEN** an admin calls `POST /api/v1/sell-machine/tasks` with a `tenant_id` that does not exist
  in `tenants`
- **THEN** the request is rejected with a 404 error and no `operator_tasks` row is created

#### Scenario: Creating a task without tenant_id falls back to Cliente Cero with a logged warning
- **WHEN** an admin calls `POST /api/v1/sell-machine/tasks` with no `tenant_id`
- **THEN** a new `operator_tasks` row is created stamped with the Cliente Cero tenant, and a
  warning is logged recording the fallback

#### Scenario: Directly creating a side-effecting task is rejected
- **WHEN** an admin calls `POST /api/v1/sell-machine/tasks` with `{"task_type": "post_content", ...}`
- **THEN** the request is rejected with a 400 error and no `operator_tasks` row is created

### Requirement: An approved campaign package can be dispatched into an operator task
The system SHALL expose `POST /api/v1/sell-machine/campaigns/{decision_id}/dispatch`, which SHALL
read the Approval Queue row for `decision_id`, verify it has `draft_type='campaign_package'` and
`status='approved'`, and SHALL create a new `operator_tasks` row whose `payload` carries the
campaign package's hooks/brief/segment/budget plus `source_decision_id`, and whose `tenant_id` is
the approval decision's own `tenant_id`. If the decision has no `tenant_id` (a legacy row),
the system SHALL fall back to the Cliente Cero tenant and SHALL log a warning. `task_type` SHALL be
`run_ads_ab` when the package's `budget_cents` is truthy, and `post_content` otherwise. The system
SHALL reject the request if the referenced draft is not an approved `campaign_package`.

#### Scenario: Dispatching derives tenant_id from the approval decision
- **WHEN** an admin calls `POST /api/v1/sell-machine/campaigns/{id}/dispatch` for an approved
  `campaign_package` decision whose `tenant_id` is `"<real-tenant-uuid>"`
- **THEN** the created `operator_tasks` row's `tenant_id` equals `"<real-tenant-uuid>"`, and the
  Cliente Cero resolver is not invoked

#### Scenario: Dispatching a legacy decision without tenant_id falls back to Cliente Cero
- **WHEN** an admin calls the dispatch endpoint for an approved decision whose `tenant_id` is null
- **THEN** the created `operator_tasks` row is stamped with the Cliente Cero tenant, and a warning
  is logged recording the fallback

#### Scenario: Dispatching an approved campaign package with no budget creates a post_content task
- **WHEN** an admin calls `POST /api/v1/sell-machine/campaigns/{id}/dispatch` for a decision whose
  `draft_type='campaign_package'`, `status='approved'`, and `budget_cents` is `None`
- **THEN** a new `operator_tasks` row is created with `task_type='post_content'`, `status='pending'`,
  and `payload.source_decision_id` equal to that decision's id

#### Scenario: Dispatching an approved campaign package with a budget creates a run_ads_ab task
- **WHEN** an admin calls the dispatch endpoint for a decision whose `budget_cents` is a positive
  integer
- **THEN** a new `operator_tasks` row is created with `task_type='run_ads_ab'`, `status='pending'`

#### Scenario: Dispatching a non-approved campaign package is rejected
- **WHEN** an admin calls the dispatch endpoint for a decision whose `status` is still
  `pending_approval` (not yet approved)
- **THEN** the request is rejected with an error and no `operator_tasks` row is created

### Requirement: Hermes can mark a task dispatched
The system SHALL expose `POST /api/v1/sell-machine/tasks/{id}/status`, which SHALL transition a
task's `status` from `pending` to `dispatched`, and SHALL reject any other transition attempted
through this endpoint. On success, the system SHALL record a best-effort entry in `agent_operations`
identifying the operation as originating from `agent_name="hermes-bridge"`.

#### Scenario: Marking a pending task dispatched succeeds
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/status` with `{"status": "dispatched"}`
  for a task currently `status='pending'`
- **THEN** the task's `status` becomes `dispatched`, and an `agent_operations` row is recorded with
  `agent_name="hermes-bridge"` and the task's `tenant_id`

#### Scenario: An invalid status transition is rejected
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/status` for a task that is already
  `dispatched` or `completed`
- **THEN** the request is rejected with a 409 error and the task's `status` is unchanged

### Requirement: Manus results are written back through Hermes
The system SHALL expose `POST /api/v1/sell-machine/tasks/{id}/result`, which SHALL accept a
`result` payload and a terminal `status` (`completed` or `failed`), and SHALL only accept this
transition from a task currently `status='dispatched'`. On success, the system SHALL record a
best-effort entry in `agent_operations` identifying the operation as originating from
`agent_name="hermes-bridge"`.

#### Scenario: Reporting a successful result completes the task
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/result` with
  `{"status": "completed", "result": {...}}` for a task currently `status='dispatched'`
- **THEN** the task's `status` becomes `completed`, its `result` column stores the submitted
  payload, and an `agent_operations` row is recorded with `agent_name="hermes-bridge"`

#### Scenario: Reporting a result for a never-dispatched task is rejected
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/result` for a task still
  `status='pending'`
- **THEN** the request is rejected with a 409 error

### Requirement: Operator-task bridge endpoints support optional machine bearer authentication
The system SHALL support an env-configured `HERMES_BRIDGE_TOKEN`. When unset, the 5 operator-task
endpoints (`GET /tasks/pending`, `POST /tasks`, `POST /campaigns/{id}/dispatch`,
`POST /tasks/{id}/status`, `POST /tasks/{id}/result`) SHALL behave exactly as they do today (no
auth required). When set, each of these endpoints SHALL require an `Authorization: Bearer <token>`
header matching the configured value, and SHALL reject requests missing or presenting an incorrect
token with a 401 error. In the canonical production environment, `HERMES_BRIDGE_TOKEN` SHALL be
configured, and the Hermes/Manus poller SHALL send a matching `Authorization: Bearer <token>`
header on every call to these 5 endpoints — the poller SHALL NOT send any other credential shape
(e.g. a self-signed JWT) as its means of authenticating to this bridge.

#### Scenario: Bridge token unset preserves today's open behavior
- **WHEN** `HERMES_BRIDGE_TOKEN` is not configured and Hermes calls any of the 5 operator-task
  endpoints with no `Authorization` header
- **THEN** the request succeeds exactly as before this change

#### Scenario: Bridge token set rejects an unauthenticated request
- **WHEN** `HERMES_BRIDGE_TOKEN` is configured and a caller omits the `Authorization` header
- **THEN** the request is rejected with a 401 error

#### Scenario: Bridge token set accepts a correctly authenticated request
- **WHEN** `HERMES_BRIDGE_TOKEN` is configured and a caller sends
  `Authorization: Bearer <matching-token>`
- **THEN** the request proceeds as normal

#### Scenario: The Hermes/Manus poller authenticates with a bearer token, not a JWT
- **WHEN** `HERMES_BRIDGE_TOKEN` is configured in both the canonical backend and the Hermes/Manus
  poller's local environment, and the poller polls `GET /tasks/pending`
- **THEN** the poller sends `Authorization: Bearer <token>` matching the configured value, and the
  request succeeds — the poller does not sign or send a JWT for this purpose

#### Scenario: Production requires the token to be configured
- **WHEN** the canonical production backend (`-175a`) is queried for its `HERMES_BRIDGE_TOKEN`
  configuration
- **THEN** the value is non-empty, and an unauthenticated call to any of the 5 operator-task
  endpoints against production is rejected with a 401 error
