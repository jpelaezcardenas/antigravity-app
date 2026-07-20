## Why

Gap #6 from the plan-vs-build audit: `services/sell_machine_service.py`'s `run_creative_loop`
(generate → evaluate, with an opt-in `use_telemetry=True` that feeds prior Manus/campaign
performance back into the Copywriter's prompt) is fully implemented and unit-tested — but has zero
callers outside its own test file. `presentation/sell_machine_endpoints.py`'s
`generate_hooks_endpoint` calls the lower-level `generate_hooks(count=payload.count)` directly, with
no telemetry and no evaluation step. The 3-day closed learning loop the original plan described
(`sell-machine-telemetry-loop`, Change G) is built but permanently dormant — nothing ever actually
runs it with `use_telemetry=True` in production.

## What Changes

- A new endpoint, `POST /api/v1/sell-machine/creative-loop/run`, calls
  `run_creative_loop(count, target_segment, use_telemetry=True)` and returns the surviving hooks —
  making the already-built, already-tested telemetry-aware loop actually reachable. This repo has
  no in-process scheduler/cron by design (Hermes, running locally, owns scheduling and reaches the
  backend's public API — see ARCHITECTURE.md decision #1); an endpoint is what Hermes needs to
  trigger the 3-day loop, not a background job inside this backend.
- The existing `POST /hooks/generate` and `POST /hooks/evaluate` endpoints are unchanged — this is
  a new, additive endpoint, not a replacement.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `sell-machine-telemetry-loop`: adds the requirement that the telemetry-aware creative loop is
  reachable via an endpoint, not just a tested-but-uncalled function.

## Impact

- `apps/backend/presentation/sell_machine_endpoints.py` — one new endpoint.
- `apps/backend/services/sell_machine_service.py` — reused as-is (`run_creative_loop`), not
  modified.
- No migration, no frontend change (Hermes calls this directly; no Búnker UI requested for this).
