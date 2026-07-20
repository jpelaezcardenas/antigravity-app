## Context

`dispatch_campaign_package(decision_id)` reads an approved `campaign_package` Approval Queue draft
and inserts a row into `operator_tasks` with `task_type` hardcoded to `"post_content"`. The
package's payload (built by `services/sell_machine_service.py`'s `create_campaign_package`)
already carries `budget_cents: Optional[int]` — set whenever the founder specifies an ad spend at
campaign-creation time — but nothing ever reads it back to decide dispatch behavior.
`SIDE_EFFECTING_TASK_TYPES = {"post_content", "run_ads_ab"}` already registers `run_ads_ab` as a
valid type; it's simply never produced by any code path (confirmed via repo-wide grep).

## Goals / Non-Goals

**Goals:**
- Make an approved campaign with a budget actually dispatch as `run_ads_ab`, closing gap #7 using
  data that already exists on the approved package — no new HITL decision required.

**Non-Goals:**
- **No new field on `CreateCampaignRequest`/`create_campaign_package`.** The founder already
  decides whether to set a budget when creating the campaign package (existing, unmodified flow);
  this change only makes dispatch respect that existing decision instead of ignoring it.
- **No change to what Hermes/Manus actually does with a `run_ads_ab` task** — that's
  Hermes-side/Manus-side execution, out of this repo's scope (per the settled Hermes/Manus
  architecture — Manus owns Meta/FB/IG posting and ads execution).
- **No retroactive fix for already-dispatched `post_content` tasks** that had a budget — this
  change only affects dispatch going forward.

## Decisions

1. **Infer from `budget_cents`, don't add a new explicit field.** Alternative considered: add a
   `task_type` or `campaign_type` field to `CreateCampaignRequest` so the founder explicitly picks
   at creation time. Rejected for now — `budget_cents` already unambiguously signals "this has ad
   spend, not just organic reach," and inventing a second, redundant field the founder would need
   to keep in sync with their own budget field is unnecessary complexity. If the founder later
   wants campaigns with a budget that still post organically (e.g. budget for boosting an existing
   post, not a fresh A/B test), that's a real product distinction to revisit — but nothing in the
   current data model or plan suggests that distinction exists yet.
2. **Threshold is truthiness, not `> 0` explicitly** — `budget_cents` is `Optional[int]`; `None` or
   `0` both mean "no ad spend," `Truthy` (any positive int) means "has ad spend." Simple, matches
   how the field is already optional throughout the codebase.

## Risks / Trade-offs

- **[Risk] A campaign with a token budget (e.g. `budget_cents=1`) dispatches as `run_ads_ab` even
  if that wasn't the founder's intent** → **Mitigation**: accepted — the founder controls
  `budget_cents` when creating the package; if they don't want an ads test, they leave it unset.
  No validation exists today to distinguish "meaningful" vs "trivial" budgets, and inventing a
  minimum-budget threshold would be an arbitrary, unrequested business rule.

## Migration Plan

No migration — pure logic change to one existing function. Stage 11: dispatch two real approved
campaign packages live — one with a budget, one without — and confirm the resulting
`operator_tasks.task_type` is `run_ads_ab` and `post_content` respectively.
