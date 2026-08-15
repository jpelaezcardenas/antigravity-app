## MODIFIED Requirements

### Requirement: A finished Manus task is reported back
The system SHALL provide a local-only service that periodically polls
`GET /api/v1/sell-machine/tasks/pending`, dispatches each task to the Manus API, and reports the
terminal result back via `POST /api/v1/sell-machine/tasks/{id}/result`, carrying `task_url` and
`credit_usage` as before, plus the task's actual output retrieved via `GET /v2/task.listMessages`:
a well-shaped `hooks` list when Manus returned a successful structured output containing one, or
the concatenated assistant message text under `manus_message` otherwise. A missing/malformed
structured output SHALL NOT produce a `hooks` key — only a genuinely well-shaped list is included.

#### Scenario: A finished Manus task is reported back with status metadata
- **WHEN** a dispatched task's Manus status becomes `stopped`
- **THEN** the operator task is reported as `completed`, carrying `task_url` and `credit_usage`

#### Scenario: A structured hooks result is retrieved and included
- **WHEN** a terminal Manus task's message history contains a `structured_output_result` with
  `success: true` and a `value` containing a well-shaped `hooks` list
- **THEN** the reported result includes that `hooks` list verbatim

#### Scenario: A fenced JSON block in free text is recognized as a fallback structured source
- **WHEN** a terminal Manus task has no successful `structured_output_result`, but its
  `assistant_message` text contains a fenced ` ```json ... ``` ` block that parses to a dict with
  a well-shaped `hooks` list
- **THEN** the reported result includes that `hooks` list, extracted from the fenced block

#### Scenario: Unstructured output is surfaced for human review, not promoted to hooks
- **WHEN** a terminal Manus task's message history contains only `assistant_message` text, with no
  successful `structured_output_result` and no parseable fenced-JSON `hooks` block
- **THEN** the reported result includes that text under `manus_message`, and does NOT include a
  `hooks` key

#### Scenario: A failed Manus task is reported back
- **WHEN** a dispatched task's Manus status becomes `error`
- **THEN** the operator task is reported as `failed`

## ADDED Requirements

### Requirement: A creative-brief research task requests structured hook output from Manus
The system SHALL, when dispatching a `research`-type task whose payload contains a
`creative_brief` key, instruct Manus (via the dispatched prompt) to return its result as
structured output in the exact shape `{"hooks": [{"headline", "body", "cta", "pain_tag"}, ...]}`.
Research tasks without a `creative_brief` payload key SHALL be prompted exactly as before this
requirement existed.

#### Scenario: A creative-brief research task's prompt requests structured JSON
- **WHEN** a `research`-type task's payload contains a `creative_brief` key
- **THEN** the dispatched Manus prompt explicitly instructs a `{"hooks": [...]}` structured output
  shape

#### Scenario: A non-creative research task's prompt is unaffected
- **WHEN** a `research`-type task's payload does not contain a `creative_brief` key
- **THEN** the dispatched Manus prompt is identical to its pre-existing behavior
