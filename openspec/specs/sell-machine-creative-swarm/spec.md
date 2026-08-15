## ADDED Requirements

### Requirement: Copywriter generates a bounded batch of marketing hooks
The system SHALL expose `POST /api/v1/sell-machine/hooks/generate`, which SHALL generate N
marketing hooks (default N=5, `{headline, body, cta, pain_tag}` each) via the LLM engine, grounded
in DIAN-pains content retrieved via `services.kb_seeding_service.retrieve_similar` against the
shared `"__global__"` KB pool, and SHALL fall back to a deterministic hook set if all LLM providers
fail (never erroring the request). KB retrieval failure or an empty result SHALL NOT block
generation — hooks are still produced without the grounding section in that case.

#### Scenario: Generating hooks returns the requested count
- **WHEN** an admin calls `POST /api/v1/sell-machine/hooks/generate` with `{"count": 5}`
- **THEN** the response includes 5 hooks, each with `headline`, `body`, `cta`, and `pain_tag`

#### Scenario: LLM provider failure falls back to a deterministic hook set
- **WHEN** `POST /api/v1/sell-machine/hooks/generate` is called and all configured LLM providers
  fail
- **THEN** the response still returns a non-empty set of hooks (the deterministic fallback), and
  the request does not error

#### Scenario: Hook generation is grounded in retrieved KB content
- **WHEN** `retrieve_similar` returns one or more DIAN-pains chunks for the generation query
- **THEN** those chunks are included in the LLM prompt as grounding context before hooks are
  generated

#### Scenario: KB retrieval failure does not block hook generation
- **WHEN** `retrieve_similar` raises or returns zero chunks
- **THEN** hook generation proceeds without a grounding section, producing the same shape of
  result as before this requirement existed

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

### Requirement: Surviving hooks become a campaign package awaiting approval
The system SHALL expose `POST /api/v1/sell-machine/campaigns`, which SHALL accept a set of
surviving hooks plus a creative brief, target segment, and budget placeholder, and SHALL enqueue
them as a single draft into the existing Approval Queue with `draft_type='campaign_package'` and
`status='pending_approval'` — reusing the queue's existing generic approve/reject machinery
unmodified.

#### Scenario: Creating a campaign package enqueues a pending draft
- **WHEN** an admin calls `POST /api/v1/sell-machine/campaigns` with 3 surviving hooks, a creative
  brief, a target segment, and a budget
- **THEN** a new row appears in the Approval Queue with `draft_type='campaign_package'`,
  `status='pending_approval'`, and a `payload` containing the submitted hooks/brief/segment/budget

#### Scenario: Approving a campaign package uses the existing Approval Queue endpoint unmodified
- **WHEN** an admin calls the existing `POST /api/v1/approval-queue/approve` for a
  `campaign_package` draft's decision id
- **THEN** the draft's status becomes `approved`, with no code changes required to the Approval
  Queue's own service/endpoint

### Requirement: Pending and past campaign packages are listable
The system SHALL expose `GET /api/v1/sell-machine/campaigns`, returning `campaign_package` drafts
from the Approval Queue (optionally filtered by status), for display in the Búnker.

#### Scenario: Listing campaigns returns pending packages
- **WHEN** an admin calls `GET /api/v1/sell-machine/campaigns?status=pending_approval`
- **THEN** the response includes every `campaign_package` draft currently `pending_approval`,
  each with its hooks, brief, target segment, and budget

### Requirement: Búnker exposes a standalone Sell Machine section
The Búnker sidebar SHALL include a "Sell Machine" section (a new top-level item, not a sub-tab of
CRM/Ventas) showing generated/evaluated hooks and pending campaign-package approvals, with explicit
loading, error, and empty states, following the existing data-bound screen conventions
(`@theme` tokens only, no new libraries).

#### Scenario: Admin opens Sell Machine and sees pending campaign packages
- **WHEN** an authenticated admin navigates to `/app/bunker` and selects "Sell Machine"
- **THEN** any `pending_approval` campaign packages are listed with their hooks, and an
  approve/reject action is available per package

#### Scenario: Backend unreachable shows an explicit error state, not a blank screen
- **WHEN** the Sell Machine endpoints are unreachable from the frontend
- **THEN** the section shows a visible error message rather than rendering blank or throwing

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
