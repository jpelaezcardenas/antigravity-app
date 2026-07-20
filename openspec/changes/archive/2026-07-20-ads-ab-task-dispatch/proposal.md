## Why

Gap #7 from the plan-vs-build audit: `operator_task_service.py`'s `dispatch_campaign_package`
always hardcodes `task_type: "post_content"` when converting an approved `campaign_package` draft
into a pending operator task — `run_ads_ab` is a registered, valid `SIDE_EFFECTING_TASK_TYPES`
member (confirmed in the same file) that no code path ever actually creates. There's no way for an
approved campaign with an ad budget to ever become an A/B ads test task; it always dispatches as a
plain organic post.

## What Changes

- `dispatch_campaign_package` infers `task_type` from the approved package's own `budget_cents`
  field (already present on every `campaign_package` draft, per `create_campaign_package`): a
  truthy `budget_cents` dispatches as `run_ads_ab`; `None`/`0`/absent dispatches as `post_content`
  (unchanged from today). No new field, no new decision the founder/HITL approver needs to make —
  the presence of a budget on the already-approved package is itself the signal, and budget is
  exactly what distinguishes "boost this with ad spend" from "just post it organically."

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `hermes-manus-execution-bridge`: "An approved campaign package can be dispatched as an operator
  task" gains task_type inference; the dispatch precondition (must be `approved`) and payload shape
  are unchanged.

## Impact

- `apps/backend/services/operator_task_service.py` — the only file touched.
- No migration, no new endpoint, no frontend change.
