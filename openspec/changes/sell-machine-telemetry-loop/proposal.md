## Why

The Sell Machine creative loop (Change E) generates hooks with no memory of what worked before,
and the Hermes/Manus execution bridge (Change F) collects `result` data on completed
`post_content`/`run_ads_ab` operator tasks that nothing ever reads back. The plan's closed loop
(section 2.6) calls for a 3-day cycle where an Analyst pulls that telemetry plus the B2C funnel's
conversion signal (`crm_leads` stage counts) and feeds it into the Copywriter's next prompt, so hook
quality improves without the founder manually explaining what worked. This is buildable now against
whatever real or simulated `operator_tasks.result` data exists — no new external credentials
required, since it only reads what Changes E/F already write.

## What Changes

- New `GET /api/v1/sell-machine/telemetry/report` endpoint: aggregates completed
  `post_content`/`run_ads_ab` operator-task results (Change F) and current `crm_leads` stage
  counts (Change B) into a single report (`{hook_performance, funnel_snapshot, generated_at}`).
- New `services/operator_task_service.list_completed_tasks(task_type=None)` function — the
  read-back capability Change F explicitly deferred to this change.
- Extend `services/copywriter_service.generate_hooks(count, report=None)` with an optional `report`
  parameter that, when provided, is woven into the LLM prompt as prior-performance context — the
  Copywriter's existing deterministic-fallback behavior is unchanged when `report` is omitted or
  the LLM is unavailable.
- Extend `services/sell_machine_service.run_creative_loop(count, target_segment=None,
  use_telemetry=False)` with an opt-in flag that, when true, fetches the telemetry report and
  passes it to `generate_hooks`.
- **Scheduling is explicitly out of scope** — no cron/scheduler exists in this repo (confirmed by
  design.md), and the plan places the 3-day timer Hermes-side (local), not here. This change only
  builds the report + the opt-in consumption point Hermes/a human can trigger on any cadence.

## Capabilities

### New Capabilities
- `sell-machine-telemetry-loop`: aggregated performance report over completed operator tasks +
  funnel snapshot, and the Copywriter's optional consumption of that report.

### Modified Capabilities
(none — Change E's `generate_hooks`/`run_creative_loop` and Change F's `operator_task_service`
keep their existing behavior unchanged when telemetry isn't requested; this only adds new,
optional parameters and a new read-only endpoint)

## Impact

- **New endpoint**: `GET /api/v1/sell-machine/telemetry/report`, under the existing
  `SELL_MACHINE_CANONICAL` flag (reused, matching Change F's precedent — this is the same
  capability area, not a new surface).
- **New/modified services**: `operator_task_service.py` (new function), `copywriter_service.py`
  (new optional parameter), `sell_machine_service.py` (new optional parameter).
- **No new tables/migrations** — reuses `operator_tasks` (Change F) and `crm_leads` (Change B)
  as-is.
- **No frontend change required** for this change to be complete and useful (Hermes/a human can
  call the endpoint directly); a "Última Actualización de Telemetría" panel in the existing Sell
  Machine Búnker section is a nice-to-have, called out as optional in tasks.md, not required.
- **Real-data caveat**: since no real Manus results exist yet (Hermes-side integration is out of
  scope, per Change F), this change's live Stage 11 verification will populate its own
  representative completed-task rows for the smoke test, explicitly labeled as such — not
  presented as real ad performance data.
