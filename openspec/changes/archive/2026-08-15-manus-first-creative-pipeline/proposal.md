## Why

`HANDOFF-RENTA-NATURAL-2026.md` §7 agreed the creative loop should be **Manus produces, Contexia's
internal agents refine and gate** — not the other way around. Today `run_creative_loop()` always
generates hooks from scratch via `copywriter_service.generate_hooks()` (an LLM call); there is no
path for a Manus-authored draft to enter the loop and be refined/evaluated by the Content Critic
before reaching the Approval Queue. The Manus↔poller circuit (`hermes-manus-poller-activation`,
already operational per founder confirmation 2026-08-14) can already round-trip a `research` task
to Manus and read its result back — nothing currently consumes that result as creative input.

## What Changes

- `services/sell_machine_service.py::run_creative_loop()` gains an optional `manus_draft_hooks`
  parameter: a list of raw hook dicts (`{headline, body, cta, pain_tag}`, the same shape
  `generate_hooks()` already returns). When provided, LLM-from-scratch generation is skipped
  entirely and the raw hooks go straight into the existing `evaluate_hooks()` pipeline (hard-ban +
  Claim Ledger + LLM tone check + one rewrite pass, unchanged from `brand-voice-canonization`).
  When omitted, behavior is identical to today — every existing caller is unaffected.
- New `services/sell_machine_service.py::get_latest_manus_draft()`: reads the most recent completed
  `research`-type operator task via the existing `operator_task_service.list_completed_tasks()`
  and extracts its hook list from `result`, returning `None` if none exists or the shape is
  unrecognized (never raises — a missing/malformed Manus draft falls back to generation-from-scratch,
  not an error).
- No changes to the Approval Queue, `operator_tasks`, the poller, or Manus dispatch — a surviving
  hook (whether Manus-sourced or LLM-generated) flows into `create_campaign_package()` exactly as
  it does today.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `sell-machine-creative-swarm`: `run_creative_loop()`'s generation step becomes optional/
  pluggable — it can consume an externally-produced (Manus) draft instead of always generating via
  the LLM engine, while the evaluation/rewrite/survivor contract is unchanged.

## Impact

- `apps/backend/services/sell_machine_service.py` (modified: `run_creative_loop()` signature; new:
  `get_latest_manus_draft()`)
- `openspec/specs/sell-machine-creative-swarm/spec.md` (delta: generation step is now optional)
- No API contract change to any existing endpoint (`sell_machine_endpoints.py` is untouched in this
  change — wiring an HTTP trigger for the Manus-draft path is a follow-up, not required to close
  the loop end-to-end for a manual/scripted first sprint)
- No migration, no new external dependency
