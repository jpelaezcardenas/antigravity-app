## Why

Change E (`sell-machine-creative-swarm`, archived) produces approved `campaign_package` drafts in
the Approval Queue, but nothing turns an approval into real execution — there is no consumer.
Separately, Manus (the founder's paid Pro agent) is confirmed as the "operador ejecutivo" for a
broad set of non-core-dev operational work (social posting/ads, creator/partnership search,
research, metrics pulls, external integrations, operational docs) — not just Meta posting. Hermes
(local, on-prem) is the only agent allowed to call Manus, since Manus keys and Meta credentials
must stay off Railway (data sovereignty, `ARCHITECTURE.md` decision #1). Today there is no seam for
Hermes to discover pending work or report results back.

## What Changes

- New tenant-scoped table `operator_tasks`, generic across a `task_type` enum
  (`post_content | run_ads_ab | research | metrics_pull | external_integration | generate_doc`) —
  not Meta-specific — so Manus's full confirmed scope fits without a later redesign.
- New backend endpoints under the existing `SELL_MACHINE_CANONICAL` flag (reused, not a new flag —
  see design.md): `GET /api/v1/sell-machine/tasks/pending` (Hermes polls), `POST
  /api/v1/sell-machine/tasks/{id}/status` (Hermes marks dispatched), `POST
  /api/v1/sell-machine/tasks/{id}/result` (Manus write-back via Hermes).
- A new service function that converts an **approved** `campaign_package` Approval Queue draft into
  a pending `operator_task` (`task_type='post_content'`) — the seam between Change E's output and
  this change's input.
- HITL gate applies only to side-effecting task types (`post_content`, `run_ads_ab`) — those are
  the ones created from an approved Approval Queue draft, so they are already gated by the time
  they reach `operator_tasks`. Read-only task types (`research`, `metrics_pull`,
  `generate_doc`) can be created directly via a task-creation endpoint without an approval draft,
  since they have no outbound side effect.
- **Explicitly out of scope**: the actual Hermes-side Manus API client/config (lives in the
  separate `hermes-workspace` repo) and the Analyst/telemetry consumption of results (Change G,
  `sell-machine-telemetry-loop`, later). This change only builds the backend contract/seam.

## Capabilities

### New Capabilities
- `hermes-manus-execution-bridge`: generic operator-task queue (creation, listing, status
  transitions, result write-back) bridging approved Sell Machine output to external execution via
  Hermes/Manus, without exposing Manus or Hermes credentials to the cloud backend.

### Modified Capabilities
(none — this change adds a new capability and does not alter the requirements of
`sell-machine-creative-swarm` or the Approval Queue's own behavior; it only reads approved rows)

## Impact

- **New migration**: `operator_tasks` table + RLS (admin-only, tenant-scoped to Cliente Cero,
  matching the pattern from `0020`/`0022`/prior migrations).
- **New service**: `apps/backend/services/operator_task_service.py`.
- **New/modified endpoints**: extends `apps/backend/presentation/sell_machine_endpoints.py` (or a
  new `operator_task_endpoints.py`, decided in design.md) under the existing `SELL_MACHINE_CANONICAL`
  flag.
- **No frontend change planned** in this change (Hermes is the consumer, not the Búnker) — if a
  minimal read-only "Operator Tasks" view is added it will be called out explicitly in tasks.md as
  optional.
- **No changes** to `apps/backend/services/approval_queue_service.py`'s existing behavior — it is
  only read from (querying approved `campaign_package` drafts), never modified.
