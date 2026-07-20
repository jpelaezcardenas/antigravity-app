## Context

Re-read the live code before scoping this change:
- `operator_task_service.py` (Change F) has `create_task`, `list_pending_tasks`,
  `mark_dispatched`, `report_result`, `dispatch_campaign_package` — no function to read back
  *completed* tasks. This is the exact gap Change F's proposal explicitly deferred ("consuming/
  analyzing `result` payloads... is Change G").
- `copywriter_service.generate_hooks(count)` and `sell_machine_service.run_creative_loop(count,
  target_segment=None)` take no prior-performance input today — every generation starts cold.
- `crm_service.py` has `VALID_LEAD_STAGES = ["NUEVOS","PROSPECTOS","POR_APROBAR",
  "LISTOS_CONTADORA"]` and reads `crm_leads` directly; a stage-count aggregation is a straightforward
  new read, no new table.
- **No scheduler/cron library exists anywhere in this repo** (confirmed via grep — only incidental
  text matches like "cronograma", no `APScheduler`/cron import). The Sell Machine plan
  (`eventual-snacking-ritchie.md`, section 2.6) places the 3-day timer **Hermes-side (local)**,
  consistent with `ARCHITECTURE.md` decision #1 (Hermes never in Railway). This repo only needs to
  expose the report a scheduler (Hermes, or a human) can call on any cadence.
- No real Manus results exist yet — the Hermes→Manus dispatch loop (Change F) has no live consumer
  configured. This change's telemetry report will, in production, aggregate whatever
  `operator_tasks.result` rows exist (today: zero or the Change F smoke-test rows), which is
  expected and correct — an empty/thin report is not a bug.

## Goals / Non-Goals

**Goals:**
- Read back completed operator-task results and summarize them per `task_type`.
- Read the current `crm_leads` funnel snapshot (counts per stage) as the conversion-side signal.
- Let the Copywriter optionally consume this report as prompt context, with zero behavior change
  when it's omitted (existing callers of `generate_hooks`/`run_creative_loop` are unaffected).
- Expose it as a single, simple `GET` endpoint any external caller (Hermes, curl, a human) can poll.

**Non-Goals:**
- Building a scheduler/cron — deliberately absent from this repo by design; the 3-day cadence is
  Hermes' job, not this backend's.
- Consuming real Manus ad-performance data — none exists yet; this change works correctly against
  whatever data is present, empty or not.
- A Búnker UI panel — optional, called out separately in tasks.md, not required for this change to
  be complete.
- Any change to Change F's HITL/dispatch behavior, or Change E's Critic/hard-ban gate — untouched.

## Decisions

**1. `list_completed_tasks` lives in the existing `operator_task_service.py`, not a new module.**
It's a natural sibling to `list_pending_tasks`, reads the same table, and Change F's own proposal
named this exact function as its deferred follow-up — no reason to split it elsewhere.

**2. The report aggregates by `task_type`, not by individual task.**
`GET /telemetry/report` returns `hook_performance: {post_content: {...}, run_ads_ab: {...}}` —
counts and any numeric fields found in each type's `result` payload (e.g. `impressions`, `clicks`,
if present) — rather than a raw list of every completed task. This keeps the report small and
directly promptable, and tolerates `result` payloads whose shape varies by `task_type` (as
Change F's design intentionally allows) without needing a rigid schema.

**3. `generate_hooks`/`run_creative_loop` take an optional `report` parameter — additive, not a
breaking signature change.**
`generate_hooks(count: int = 5, report: Optional[Dict] = None)`. When `report` is provided, it's
serialized into the LLM prompt as a short "lo que funcionó antes" section; when omitted (every
existing call site), behavior is byte-for-byte identical to today. `run_creative_loop` gains
`use_telemetry: bool = False` — when true, it calls the new telemetry function itself and passes
the result through; existing callers that don't pass this flag see no change.

**4. The funnel snapshot counts `crm_leads` by stage directly — no new aggregation table.**
A `SELECT stage, count(*) ... GROUP BY stage` (or the equivalent via the Supabase client) against
the existing table is sufficient; this is a read-only report, not a materialized view, since
`crm_leads` is small (tens to low hundreds of rows at this stage of the business).

**5. Reused flag: `SELL_MACHINE_CANONICAL`, not a new one.**
Same capability area as Changes E/F, already live in production — matches Change F's precedent
exactly (new routes under the same already-true flag), not Change D's precedent (new flag for a
genuinely new surface like a channel). A telemetry-read endpoint carries no side effect and no new
risk beyond what's already accepted for this flag.

## Risks / Trade-offs

- **[Risk] Report may be empty/thin in production (no real Manus data yet).** → Mitigation: this is
  expected and correct, not a bug — the endpoint returns an honest empty-ish report
  (`hook_performance: {}` or zero-counts) rather than fabricating data. Stage 11's live smoke test
  will populate representative completed-task rows itself, explicitly labeled as smoke-test data
  in the deployment report, not presented as real performance.
- **[Risk] `result` payload shape varies by `task_type` (Change F's own design choice) — aggregation
  logic must not assume a rigid schema.** → Mitigation: aggregation reads only well-known optional
  numeric fields (`impressions`, `clicks`, etc.) via `.get()`, tolerating missing fields; unknown/
  extra fields in `result` are ignored, never raise.
- **[Risk] Feeding a malformed or huge report into the LLM prompt could blow context/cost.** →
  Mitigation: the report is a small, pre-aggregated summary (counts and rates), not raw task
  dumps — bounded by construction, not by a length check.

## Migration Plan

1. `list_completed_tasks` (operator_task_service) + funnel-count query (crm_service or a small new
   helper), TDD, no migration.
2. `generate_hooks`/`run_creative_loop` optional-parameter extension, TDD, confirming zero
   regression for existing no-report call sites.
3. `GET /telemetry/report` endpoint under the existing `SELL_MACHINE_CANONICAL` flag.
4. Stage 11: commit, merge, verify Railway green (flag already true, so this is live immediately —
   same posture as Change F), live smoke test: create a couple of representative completed
   `operator_tasks` rows (explicitly labeled smoke-test data) via direct Supabase SQL, call
   `GET /telemetry/report` live and confirm it reflects them, confirm `generate_hooks` with a report
   still returns a valid hook shape, deployment report, archive.
- **Rollback**: purely additive; removing the new endpoint/parameters has no effect on any other
  code path.

## Open Questions

- Should the report additionally read Social Ops' existing `metricas`/`publicaciones` tables (organic
  content performance)? Deferred — the plan scopes this loop specifically to Manus/Meta ad
  telemetry + the B2C funnel, not organic Social Ops metrics, which already has its own dashboard
  (`get_metrics_dashboard`).
