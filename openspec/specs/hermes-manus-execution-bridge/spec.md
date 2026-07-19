## ADDED Requirements

### Requirement: Hermes can discover pending operator tasks
The system SHALL expose `GET /api/v1/sell-machine/tasks/pending`, returning all `operator_tasks`
rows with `status='pending'`, ordered oldest-first, so Hermes can poll for work without any
inbound connection from the cloud backend to Hermes.

#### Scenario: Listing pending tasks returns unclaimed work
- **WHEN** Hermes calls `GET /api/v1/sell-machine/tasks/pending`
- **THEN** the response includes every `operator_tasks` row currently `status='pending'`, each
  with its `id`, `task_type`, and `payload`

### Requirement: Read-only task types can be created directly, without an approval draft
The system SHALL expose `POST /api/v1/sell-machine/tasks`, which SHALL create a new
`operator_tasks` row with `status='pending'` when `task_type` is one of `research`,
`metrics_pull`, `external_integration`, or `generate_doc`, and SHALL reject the request with a 400
error when `task_type` is `post_content` or `run_ads_ab` (side-effecting types, which require the
dispatch flow below).

#### Scenario: Creating a research task succeeds without any approval draft
- **WHEN** an admin calls `POST /api/v1/sell-machine/tasks` with
  `{"task_type": "research", "payload": {...}}`
- **THEN** a new `operator_tasks` row is created with `status='pending'` and no corresponding
  Approval Queue row is required or created

#### Scenario: Directly creating a side-effecting task is rejected
- **WHEN** an admin calls `POST /api/v1/sell-machine/tasks` with `{"task_type": "post_content", ...}`
- **THEN** the request is rejected with a 400 error and no `operator_tasks` row is created

### Requirement: An approved campaign package can be dispatched into a post_content operator task
The system SHALL expose `POST /api/v1/sell-machine/campaigns/{decision_id}/dispatch`, which SHALL
read the Approval Queue row for `decision_id`, verify it has `draft_type='campaign_package'` and
`status='approved'`, and SHALL create a new `operator_tasks` row with `task_type='post_content'`
whose `payload` carries the campaign package's hooks/brief/segment/budget plus
`source_decision_id`. The system SHALL reject the request if the referenced draft is not an
approved `campaign_package`.

#### Scenario: Dispatching an approved campaign package creates a pending operator task
- **WHEN** an admin calls `POST /api/v1/sell-machine/campaigns/{id}/dispatch` for a decision whose
  `draft_type='campaign_package'` and `status='approved'`
- **THEN** a new `operator_tasks` row is created with `task_type='post_content'`, `status='pending'`,
  and `payload.source_decision_id` equal to that decision's id

#### Scenario: Dispatching a non-approved campaign package is rejected
- **WHEN** an admin calls the dispatch endpoint for a decision whose `status` is still
  `pending_approval` (not yet approved)
- **THEN** the request is rejected with an error and no `operator_tasks` row is created

### Requirement: Hermes can mark a task dispatched
The system SHALL expose `POST /api/v1/sell-machine/tasks/{id}/status`, which SHALL transition a
task's `status` from `pending` to `dispatched`, and SHALL reject any other transition attempted
through this endpoint.

#### Scenario: Marking a pending task dispatched succeeds
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/status` with `{"status": "dispatched"}`
  for a task currently `status='pending'`
- **THEN** the task's `status` becomes `dispatched`

#### Scenario: An invalid status transition is rejected
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/status` for a task that is already
  `dispatched` or `completed`
- **THEN** the request is rejected with a 409 error and the task's `status` is unchanged

### Requirement: Manus results are written back through Hermes
The system SHALL expose `POST /api/v1/sell-machine/tasks/{id}/result`, which SHALL accept a
`result` payload and a terminal `status` (`completed` or `failed`), and SHALL only accept this
transition from a task currently `status='dispatched'`.

#### Scenario: Reporting a successful result completes the task
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/result` with
  `{"status": "completed", "result": {...}}` for a task currently `status='dispatched'`
- **THEN** the task's `status` becomes `completed` and its `result` column stores the submitted
  payload

#### Scenario: Reporting a result for a never-dispatched task is rejected
- **WHEN** Hermes calls `POST /api/v1/sell-machine/tasks/{id}/result` for a task still
  `status='pending'`
- **THEN** the request is rejected with a 409 error
