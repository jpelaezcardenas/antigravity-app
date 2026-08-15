## MODIFIED Requirements

### Requirement: Content Critic filters hooks against the brand rubric with one rewrite pass
The system SHALL expose `POST /api/v1/sell-machine/hooks/evaluate`, which SHALL score each
submitted hook against the brand rubric (hard-reject on any "Never" rule violation — e.g. framing
Contexia as a regulated accounting firm, or robotic/jerga-opaca tone — **or an unsourced
peso/UVT numeric claim, per the Claim Ledger**), SHALL request at most one rewrite for a rejected
hook, and SHALL return only the surviving hooks (rewritten where applicable). The hard-ban phrase
list and the Claim Ledger's known-value allowlist SHALL live in a single tracked module
(`apps/backend/agents/brand_rubric.py`), imported by the Content Critic rather than duplicated
inline, and the Claim Ledger allowlist SHALL derive from `core.constants` (not a separate hardcoded
copy of fiscal figures). A rewrite response that is not a well-shaped single hook (e.g. a list, or
an object missing `headline`/`body`/`cta`) SHALL NOT crash evaluation — the original hook SHALL be
used for re-evaluation instead, matching the existing LLM-unavailable fallback contract. **A
peso/UVT figure that is not a known fiscal constant SHALL still be accepted if it is visibly cited
alongside a recognized market-research source name (e.g. CCCE, DANE) — an unsourced figure with no
such citation SHALL still be rejected.**

#### Scenario: A hook violating a hard rule is rejected without a survivor
- **WHEN** a submitted hook's text asserts that Contexia is a regulated accounting firm that signs
  financial statements
- **THEN** the Content Critic rejects it, and — even after one rewrite attempt — if the violation
  persists the hook does not appear in the evaluation response's surviving set

#### Scenario: A hook that passes is returned unchanged
- **WHEN** a submitted hook contains no rubric violations
- **THEN** it appears in the surviving set with its original `headline`/`body`/`cta` unchanged

#### Scenario: A malformed rewrite response falls back to the original hook
- **WHEN** a rejected hook's rewrite attempt returns a response that is not a well-shaped single
  hook object (e.g. a JSON array, or an object missing required fields)
- **THEN** evaluation proceeds using the original (unrewritten) hook rather than crashing, and the
  hook's survival is determined by re-evaluating that original hook

#### Scenario: A list-wrapped rewrite response is unwrapped when its first element is well-shaped
- **WHEN** a rejected hook's rewrite attempt returns a JSON array whose first element is a
  well-shaped hook object
- **THEN** that first element is used as the rewritten hook for re-evaluation

#### Scenario: A cited market figure is accepted even though it is not a fiscal constant
- **WHEN** a hook cites a peso figure immediately followed by a parenthetical naming a recognized
  market-research source (e.g. `"$105,4 billones (+26,7% vs 2023, CCCE)"`)
- **THEN** the Claim Ledger does not reject that figure for being unsourced

#### Scenario: An uncited figure from an unrecognized source is still rejected
- **WHEN** a hook cites a peso figure with no adjacent citation, or with a parenthetical that does
  not name a recognized source
- **THEN** the Claim Ledger rejects it exactly as before this change
