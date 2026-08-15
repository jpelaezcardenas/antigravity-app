## ADDED Requirements

### Requirement: Research task dispatch requests native structured output
The system SHALL, when dispatching a `research`-type task, pass a `structured_output_schema`
(`RESEARCH_HOOKS_SCHEMA`) to `task.create` so Manus can return hooks via the API's native
structured-output mechanism. Non-`research` task types SHALL be dispatched without a schema.

#### Scenario: A research task is dispatched with the native hooks schema
- **WHEN** a `research`-type pending task is dispatched
- **THEN** `manus_client.create_task()` is called with `structured_output_schema` set to
  `RESEARCH_HOOKS_SCHEMA`

#### Scenario: A non-research task is dispatched without a schema
- **WHEN** a `post_content`, `run_ads_ab`, or other non-`research` pending task is dispatched
- **THEN** `manus_client.create_task()` is called with `structured_output_schema` set to `None`

### Requirement: Side-effecting prompts demand a structured evidence report
The `post_content`/`run_ads_ab` prompt banner SHALL instruct Manus to report a structured
`{post_url, post_id, published_at, status}` result, detect and skip republishing an identical post
already published in the last 24 hours (`duplicate_detected`), and stop without dispatching if the
payload appears to contain B2B client PII.

#### Scenario: The approved-content banner includes the evidence contract
- **WHEN** a `post_content` or `run_ads_ab` task is dispatched
- **THEN** its prompt includes instructions for a structured evidence report and the
  24-hour duplicate-detection rule
