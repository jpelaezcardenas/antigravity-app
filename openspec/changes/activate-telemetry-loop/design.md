## Context

`run_creative_loop(count, target_segment, use_telemetry)` in `sell_machine_service.py` already
does exactly what the 3-day closed-loop plan describes: when `use_telemetry=True`, it calls
`get_telemetry_report()` (aggregating completed `post_content`/`run_ads_ab` operator-task results
plus the `crm_leads` funnel snapshot) and feeds it into `generate_hooks`, then evaluates the result
via `evaluate_hooks`. It is fully unit-tested (`test_sell_machine_service.py`, including the
`use_telemetry=True` path) but `presentation/sell_machine_endpoints.py`'s `generate_hooks_endpoint`
calls the lower-level `generate_hooks` directly — `run_creative_loop` has no caller in the running
application at all.

This repo has no in-process scheduler (`ARCHITECTURE.md`/`HARNESS.md` decisions: Hermes runs
local/on-prem and owns scheduling, reaching the backend's public API — never the reverse). The
3-day loop's timer therefore must live Hermes-side; this backend's job is only to expose an
endpoint Hermes can call on its own schedule.

## Goals / Non-Goals

**Goals:**
- Make `run_creative_loop(use_telemetry=True)` reachable via a real endpoint, closing gap #6.

**Non-Goals:**
- **No in-backend scheduler/cron.** Per the settled architecture decision, scheduling lives with
  Hermes (local), not this Railway-deployed backend. This change only adds the endpoint Hermes
  would call; it does not configure Hermes itself (out of this repo's scope — Hermes config lives
  in the separate `hermes-workspace` repo).
- **No new Búnker UI.** Not requested; the endpoint is for Hermes/admin use, matching how the
  existing `/tasks/pending` polling endpoint (Change F) has no dedicated UI either.
- **Does not auto-create a campaign package from survivors.** Mirrors the existing
  `/hooks/generate` → `/hooks/evaluate` → `/campaigns` three-step HITL flow — this endpoint stops
  at "survivors," consistent with keeping campaign-package creation (which enqueues an Approval
  Queue draft) an explicit, separate step.

## Decisions

1. **One new endpoint (`POST /creative-loop/run`), not a change to `/hooks/generate`.**
   Alternative considered: add a `use_telemetry` query param to the existing
   `POST /hooks/generate`. Rejected — `/hooks/generate` returns only `hooks` (no evaluation), while
   `run_creative_loop` returns `survivors` (post-evaluation) — different response shapes for
   different callers (a human testing raw generation vs. Hermes running the real closed loop).
   Conflating them would make the existing endpoint's contract ambiguous.
2. **Request body accepts `count`, `target_segment` (optional), matching `run_creative_loop`'s
   existing parameters** — no new parameters invented.
3. **Reuses `SELL_MACHINE_CANONICAL`**, the same flag every other Sell Machine endpoint in this
   file already sits behind — no new flag needed.

## Risks / Trade-offs

- **[Risk] Nothing calls this endpoint yet either** (Hermes-side polling/scheduling for this
  specific endpoint isn't configured in this session) → **Mitigation**: out of scope — this
  change's job is to make the loop *reachable*, matching the existing precedent of
  `/tasks/pending` (Change F), which was also built before Hermes-side polling was configured.
  Documented as a follow-up, not treated as this change's responsibility.

## Migration Plan

No migration — one new endpoint. Stage 11: call the real endpoint live, confirm it returns
survivors (LLM output, so inspect for shape/plausibility) and that Railway logs show
`get_telemetry_report` was actually invoked (confirming `use_telemetry=True` took the telemetry
branch, not the generic one).
