## ADDED Requirements

### Requirement: A telemetry report aggregates completed operator-task results and the funnel snapshot
The system SHALL expose `GET /api/v1/sell-machine/telemetry/report`, returning
`{hook_performance, funnel_snapshot, generated_at}`, where `hook_performance` aggregates completed
`post_content`/`run_ads_ab` operator-task results by `task_type`, and `funnel_snapshot` reports the
current `crm_leads` count per stage.

#### Scenario: Report reflects completed operator tasks
- **WHEN** one or more `operator_tasks` rows exist with `status="completed"` and `task_type`
  `post_content` or `run_ads_ab`
- **THEN** `hook_performance` includes an entry for that `task_type` summarizing those completions

#### Scenario: Report is well-formed with no completed tasks yet
- **WHEN** no `operator_tasks` rows are `status="completed"`
- **THEN** the endpoint still returns `200` with an empty/zeroed `hook_performance`, never an error

#### Scenario: Funnel snapshot reflects current lead-stage counts
- **WHEN** `crm_leads` has rows across multiple stages
- **THEN** `funnel_snapshot` reports the count of leads in each of `NUEVOS`, `PROSPECTOS`,
  `POR_APROBAR`, `LISTOS_CONTADORA`

### Requirement: Completed operator tasks are listable
The system SHALL expose `list_completed_tasks(task_type=None)` in `operator_task_service`,
returning `operator_tasks` rows with `status="completed"`, optionally filtered by `task_type`.

#### Scenario: Listing completed tasks by type
- **WHEN** `list_completed_tasks(task_type="post_content")` is called
- **THEN** it returns only `status="completed"` rows with `task_type="post_content"`

### Requirement: The Copywriter can optionally consume a telemetry report without changing existing behavior
`generate_hooks` SHALL accept an optional `report` parameter; when provided, the report SHALL be
included as prior-performance context in the LLM prompt. When `report` is omitted, `generate_hooks`
SHALL behave identically to its pre-existing signature (including the deterministic-fallback
behavior on LLM failure).

#### Scenario: Existing callers without a report see no behavior change
- **WHEN** `generate_hooks(count=5)` is called without a `report` argument
- **THEN** hook generation proceeds exactly as before this change

#### Scenario: A report is woven into hook generation
- **WHEN** `generate_hooks(count=5, report=telemetry_report)` is called
- **THEN** the LLM prompt includes the report's summary content, and generation still falls back
  to the deterministic hook set if the LLM is unavailable
