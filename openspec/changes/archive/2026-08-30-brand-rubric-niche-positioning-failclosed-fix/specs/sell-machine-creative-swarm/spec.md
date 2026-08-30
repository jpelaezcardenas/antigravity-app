## MODIFIED Requirements

### Requirement: Copywriter generates a bounded batch of marketing hooks
The system SHALL expose `POST /api/v1/sell-machine/hooks/generate`, which SHALL generate N
marketing hooks (default N=5, `{headline, body, cta, pain_tag}` each) via the LLM engine, grounded
in niche/value content (dropshipping margin, creator multi-platform income, freelancer honorarios,
caja/pasarelas — DIAN only as practical context, never the cold-start default) retrieved via
`services.kb_seeding_service.retrieve_similar` against the shared `"__global__"` KB pool, and
SHALL fall back to a deterministic hook set if all LLM providers fail (never erroring the
request). The generation prompt SHALL target an approximate 60% nicho/valor, 25% claridad
financiera transversal, 15% protección/cumplimiento mix per batch. KB retrieval failure or an
empty result SHALL NOT block generation — hooks are still produced without the grounding section
in that case.

#### Scenario: Generating hooks returns the requested count
- **WHEN** an admin calls `POST /api/v1/sell-machine/hooks/generate` with `{"count": 5}`
- **THEN** the response includes 5 hooks, each with `headline`, `body`, `cta`, and `pain_tag`

#### Scenario: LLM provider failure falls back to a deterministic hook set
- **WHEN** `POST /api/v1/sell-machine/hooks/generate` is called and all configured LLM providers
  fail
- **THEN** the response still returns a non-empty set of hooks (the deterministic fallback), and
  the request does not error

#### Scenario: Hook generation is grounded in retrieved KB content
- **WHEN** `retrieve_similar` returns one or more niche/value chunks for the generation query
- **THEN** those chunks are included in the LLM prompt as grounding context before hooks are
  generated

#### Scenario: KB retrieval failure does not block hook generation
- **WHEN** `retrieve_similar` raises or returns zero chunks
- **THEN** hook generation proceeds without a grounding section, producing the same shape of
  result as before this requirement existed

#### Scenario: The cold-start grounding query defaults to niche/value, not DIAN
- **WHEN** no prior telemetry report is available to derive a grounding query
- **THEN** the default query targets dropshipping margin, creator income, freelancer honorarios,
  pasarelas and caja — and does not target DIAN/Renta-Natural pain points

### Requirement: Content Critic filters hooks against the brand rubric with one rewrite pass
The system SHALL expose `POST /api/v1/sell-machine/hooks/evaluate`, which SHALL score each
submitted hook against the brand rubric (hard-reject on any "Never" rule violation — e.g. framing
Contexia as a regulated accounting firm, leading with the regulatory disclaimer instead of
"contadoras tituladas con licencia + tecnología", or robotic/jerga-opaca tone — **or an unsourced
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
such citation SHALL still be rejected.** **If the LLM tone check is unavailable (raises or times
out), the hook SHALL be rejected (fail-closed) — it SHALL NOT be approved on the basis of passing
only the deterministic hard-ban/Claim-Ledger checks.**

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
  check's result, and it is never bypassed by a fail-open fallback (there is none)

#### Scenario: A hook citing a correctly-sourced UVT figure passes the Claim Ledger check
- **WHEN** a submitted hook's text contains a peso amount that correctly derives from a value in
  `core.constants` (e.g. the minimum sanction computed from `UVT_2026`)
- **THEN** the Claim Ledger check does not reject the hook on that basis

#### Scenario: An LLM outage during tone check rejects the hook instead of approving it
- **WHEN** `_llm_tone_check` raises (all LLM providers unavailable) for a hook that violates no
  hard-ban and no Claim Ledger rule
- **THEN** `evaluate_hook` returns `approved: False` with a reason indicating the Content Critic
  was unavailable — the hook is held for review, not silently approved
