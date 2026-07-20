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
Contexia as a regulated accounting firm, or robotic/jerga-opaca tone), SHALL request at most one
rewrite for a rejected hook, and SHALL return only the surviving hooks (rewritten where
applicable).

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
