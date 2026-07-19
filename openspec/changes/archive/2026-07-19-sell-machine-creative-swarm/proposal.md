## Why

The Sell Machine vision (Antigravity handoff docs) calls for an autonomous creative loop: a
Copywriter agent drafts marketing hooks, a Critic agent filters out weak/off-brand ones, and only
the survivors reach Juan David for approval — instead of him reviewing every raw draft. This is
Change E of the staged plan: it's buildable now (no Wompi/WhatsApp/Meta keys needed) because it
runs entirely against simulated execution — Manus (Change F) will later dispatch approved
campaigns to Meta, but this change only builds the generate → evaluate → approve loop itself.

## What Changes

- Add a **Copywriter** agent service: generates N marketing hooks per request, using the existing
  `llm_engine.get_ai_response_with_profile()` pattern (same idiom as Social Ops' idea-draft
  generator), grounded in the `ai-specs/social-content-ops/` brand corpus (tone, "never" rules).
- Add a **Content Critic** agent service (new module — the existing `agent_critic.py` is a
  deterministic double-entry accounting validator, unrelated): scores each hook against a brand
  rubric derived from `content_ops_rules.md` §7–8 (bans "jerga opaca," robotic tone, misstating
  Contexia as a regulated accounting firm), discards failing hooks, forces at most one rewrite
  pass, returns the surviving hooks.
- Wire the surviving hooks into a **campaign package** draft (hooks + brief + target segment +
  budget placeholder) and enqueue it into the existing Supabase **Approval Queue**
  (`draft_type='campaign_package'`) — reusing the queue's existing generic approve/reject
  endpoints; only the enqueue path is new (the current `/approval-queue/enqueue` REST endpoint is
  hardcoded to journal-entry shapes, so this change calls `ApprovalQueueService.enqueue_draft()`
  directly, matching how `taty_escalation`/`social_reply` already do it).
- Add a new Búnker sidebar section, "Sell Machine" (a new top-level item, not a CRM/Ventas sub-tab
  — matches the existing precedent of Social Content Ops and Onboarding as standalone sections),
  showing generated hooks, evaluation results, and pending campaign-package approvals.
- New endpoints under a new `SELL_MACHINE_CANONICAL` feature flag: `POST
  /api/v1/sell-machine/hooks/generate`, `POST /api/v1/sell-machine/hooks/evaluate`, `POST
  /api/v1/sell-machine/campaigns` (enqueues the approved package), `GET
  /api/v1/sell-machine/campaigns` (lists `campaign_package` drafts from the Approval Queue).

## Capabilities

### New Capabilities
- `sell-machine-creative-swarm`: a Copywriter → Content Critic generate-and-filter loop producing
  campaign packages that flow through the existing Approval Queue HITL gate, surfaced in a new
  Búnker "Sell Machine" section.

### Modified Capabilities
(none — this adds a new capability and a new consumer of the existing Approval Queue; it does not
change the Approval Queue's own requirements, since this change only calls its existing
`enqueue_draft`/`approve_draft`/`reject_draft` service functions as already specified)

## Impact

- **Backend**: new `services/copywriter_service.py`, `services/content_evaluator.py`,
  `services/sell_machine_service.py` (orchestrates generate → evaluate → enqueue),
  `presentation/sell_machine_endpoints.py`; a new `SELL_MACHINE_CANONICAL` flag in `config.py`; a
  new LLM profile entry (or reuse of `social-ops-v1`, TBD in design) in `llm_engine.py`'s
  `PROFILE_CONFIGS`. No changes to `approval_queue_service.py`/`approval_queue_endpoints.py`
  themselves — this change is purely a new caller of their existing functions.
- **Frontend**: new `BunkerSidebar.tsx` entry, new `components/bunker/sell-machine/` section +
  sub-components, new `lib/sell-machine-api.ts` client.
- **Out of scope (future changes)**: real Meta Ads dispatch / Hermes→Manus bridge (Change F), real
  Wompi integration (Change C), Taty/WhatsApp (Change D). This change produces an *approved
  campaign package* and stops there — nothing gets posted anywhere.
