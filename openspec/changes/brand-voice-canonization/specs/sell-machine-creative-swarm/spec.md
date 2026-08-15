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
copy of fiscal figures).

#### Scenario: A hook violating a hard rule is rejected without a survivor
- **WHEN** a submitted hook's text asserts that Contexia is a regulated accounting firm that signs
  financial statements
- **THEN** the Content Critic rejects it, and — even after one rewrite attempt — if the violation
  persists the hook does not appear in the evaluation response's surviving set

#### Scenario: A hook that passes is returned unchanged
- **WHEN** a submitted hook contains no rubric violations
- **THEN** it appears in the surviving set with its original `headline`/`body`/`cta` unchanged

#### Scenario: A rejected hook is rewritten once and re-evaluated
- **WHEN** a submitted hook is rejected for a fixable tone issue (e.g. robotic phrasing, not a hard
  "Never" rule)
- **THEN** the Copywriter is asked to rewrite it exactly once, the Critic re-evaluates the
  rewrite, and the (possibly rewritten) hook appears in the surviving set only if that
  re-evaluation passes

#### Scenario: A hook citing an unsourced peso or UVT figure is rejected unconditionally
- **WHEN** a submitted hook's text contains a peso amount (e.g. `$471.000`) or a UVT-derived figure
  that does not match any value in the Claim Ledger's known-value allowlist (sourced from
  `core.constants`)
- **THEN** the Content Critic rejects it with a reason naming the unrecognized figure, and this
  rejection is non-overridable — it does not depend on and cannot be reversed by the LLM tone
  check's result, and it is never bypassed by the tone check's fail-open fallback

#### Scenario: A hook citing a correctly-sourced UVT figure passes the Claim Ledger check
- **WHEN** a submitted hook's text contains a peso amount that correctly derives from a value in
  `core.constants` (e.g. the minimum sanction computed from `UVT_2026`)
- **THEN** the Claim Ledger check does not reject the hook on that basis
