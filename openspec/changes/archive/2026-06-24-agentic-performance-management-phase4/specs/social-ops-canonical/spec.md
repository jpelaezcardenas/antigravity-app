## ADDED Requirements

### Requirement: Social Ops agents serve from FastAPI canonical tables, not n8n
The system SHALL implement Content Ideas, Lead Reply, Sales Closure, and Metrics Analyzer as FastAPI endpoints reading/writing the existing `social_command_drafts`, `social_reply_drafts`, `social_sales_drafts`, and `service_desk_reply_drafts` tables, with n8n no longer the source of truth.

#### Scenario: Content idea created via FastAPI
- **WHEN** a client calls `POST /api/v1/agents/social-ops/ideas`
- **THEN** a row is inserted into `social_command_drafts`
- **AND** no call is made to the legacy n8n webhook

#### Scenario: Lead reply draft enqueued through shared Approval Queue
- **WHEN** Lead Reply agent proposes a reply to a lead
- **THEN** the draft is inserted into `social_reply_drafts` AND enqueued to `approval_queue` with `draft_type = 'social_reply'`

#### Scenario: Metrics Analyzer reads existing drafts without mutation
- **WHEN** a client calls `GET /api/v1/agents/social-ops/metrics`
- **THEN** system aggregates counts/status from the four canonical tables
- **AND** no rows are mutated by the metrics call

### Requirement: Social Ops cutover from n8n is a flag flip, not a data migration
The system SHALL support running n8n and FastAPI Social Ops in parallel behind a feature flag, with cutover controlled by flipping the flag rather than migrating historical data.

#### Scenario: Flag off routes to n8n
- **WHEN** the `social_ops_canonical` flag is disabled
- **THEN** existing n8n workflows continue to handle Social Ops traffic unchanged

#### Scenario: Flag on routes to FastAPI canonical
- **WHEN** the `social_ops_canonical` flag is enabled
- **THEN** all four Social Ops agents serve traffic from the FastAPI endpoints
- **AND** n8n workflows for these four agents are not invoked
