## MODIFIED Requirements

### Requirement: An approved campaign package can be dispatched into an operator task
The system SHALL expose `POST /api/v1/sell-machine/campaigns/{decision_id}/dispatch`, which SHALL
read the Approval Queue row for `decision_id`, verify it has `draft_type='campaign_package'` and
`status='approved'`, and SHALL create a new `operator_tasks` row whose `payload` carries the
campaign package's hooks/brief/segment/budget plus `source_decision_id`. `task_type` SHALL be
`run_ads_ab` when the package's `budget_cents` is truthy, and `post_content` otherwise. The system
SHALL reject the request if the referenced draft is not an approved `campaign_package`.

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
