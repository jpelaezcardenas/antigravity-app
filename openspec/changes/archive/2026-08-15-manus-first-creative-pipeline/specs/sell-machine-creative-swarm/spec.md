## ADDED Requirements

### Requirement: The creative loop can consume an externally-produced (Manus) draft
The system SHALL allow `run_creative_loop()` to accept an optional list of raw draft hooks
(`manus_draft_hooks`, shape `{headline, body, cta, pain_tag}` matching the existing generated-hook
shape). When provided, hook generation via the internal Copywriter SHALL be skipped, and the
provided draft hooks SHALL be passed directly into the existing evaluate/rewrite/survivor pipeline
unchanged. When omitted, `run_creative_loop()`'s behavior SHALL be identical to its pre-existing
generation-from-scratch behavior.

#### Scenario: A Manus draft skips generation and is evaluated directly
- **WHEN** `run_creative_loop()` is called with `manus_draft_hooks` set to a list of 3 raw hooks
- **THEN** the Copywriter's generation step is not invoked, and each of the 3 hooks is passed
  through the existing hard-ban/Claim Ledger/tone-check/rewrite pipeline, with only survivors
  returned

#### Scenario: Omitting the Manus draft preserves existing behavior
- **WHEN** `run_creative_loop()` is called with no `manus_draft_hooks` argument
- **THEN** hooks are generated via the Copywriter exactly as before this requirement existed

### Requirement: The latest completed Manus research task can be read back as a creative draft
The system SHALL provide `get_latest_manus_draft()`, which reads the most recently completed
`research`-type operator task (via the existing operator-task read-back path) and extracts a hook
list from its result if present and correctly shaped, returning `None` (never raising) if no such
task exists or its result does not contain a recognizable hook list.

#### Scenario: A well-shaped Manus research result is read back as a draft
- **WHEN** the most recent completed `research` task's result contains
  `{"hooks": [{"headline": ..., "body": ..., "cta": ...}, ...]}`
- **THEN** `get_latest_manus_draft()` returns that list of hooks

#### Scenario: No completed research task returns None, not an error
- **WHEN** no `research`-type operator task has completed
- **THEN** `get_latest_manus_draft()` returns `None`

#### Scenario: A malformed research result returns None, not a guess
- **WHEN** the most recent completed `research` task's result does not contain a recognizable
  `hooks` list (e.g. it is unrelated prose, or missing the expected keys)
- **THEN** `get_latest_manus_draft()` returns `None` rather than attempting to interpret it
