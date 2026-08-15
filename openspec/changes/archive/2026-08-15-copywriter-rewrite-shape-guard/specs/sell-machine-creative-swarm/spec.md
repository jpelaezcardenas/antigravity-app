## MODIFIED Requirements

### Requirement: Content Critic filters hooks against the brand rubric with one rewrite pass
The system SHALL expose `POST /api/v1/sell-machine/hooks/evaluate`, which SHALL score each
submitted hook against the brand rubric (hard-reject on any "Never" rule violation, or an
unsourced peso/UVT numeric claim per the Claim Ledger), SHALL request at most one rewrite for a
rejected hook, and SHALL return only the surviving hooks (rewritten where applicable). A rewrite
response that is not a well-shaped single hook (e.g. a list, or an object missing
`headline`/`body`/`cta`) SHALL NOT crash evaluation — the original hook SHALL be used for
re-evaluation instead, matching the existing LLM-unavailable fallback contract.

#### Scenario: A malformed rewrite response falls back to the original hook
- **WHEN** a rejected hook's rewrite attempt returns a response that is not a well-shaped single
  hook object (e.g. a JSON array, or an object missing required fields)
- **THEN** evaluation proceeds using the original (unrewritten) hook rather than crashing, and the
  hook's survival is determined by re-evaluating that original hook

#### Scenario: A list-wrapped rewrite response is unwrapped when its first element is well-shaped
- **WHEN** a rejected hook's rewrite attempt returns a JSON array whose first element is a
  well-shaped hook object
- **THEN** that first element is used as the rewritten hook for re-evaluation
