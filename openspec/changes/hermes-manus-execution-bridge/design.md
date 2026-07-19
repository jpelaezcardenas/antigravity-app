## Context

Change E (`sell-machine-creative-swarm`, archived) creates `campaign_package` drafts in the
existing Supabase `approval_queue` table and lets an admin approve them via the generic
`/api/v1/approval-queue/approve` endpoint. Nothing consumes an approval afterward. Separately, the
project's Sell Machine plan (`eventual-snacking-ritchie.md`, Decision 5 + section 2.5) confirms
Manus as a broad "operador ejecutivo" (posting, ads, creator search, research, metrics, external
integrations, docs) driven exclusively by Hermes (local/on-prem, per `ARCHITECTURE.md` decision
#1: Hermes never runs in the cloud, and Manus/Meta credentials stay local with it). The cloud
backend (Railway) must expose a pull/push surface Hermes can call from outside — it must never be
called into.

The only existing outbox-like table, `executor_outbox`, is a 1:1 companion to `tax_correction`
Approval Queue drafts (`approval_decision_id uuid NOT NULL`, no `task_type` column, created inline
inside `ApprovalQueueService.approve_draft` — verified by reading `approval_queue_service.py` and
the live schema via Supabase MCP `execute_sql`). It has no generic task-type notion and conflating
it with Sell Machine's needs would require adding a nullable FK plus a new enum to a table another
draft type already depends on — riskier than a new table.

## Goals / Non-Goals

**Goals:**
- Give Hermes a pull-based way to discover work (`GET /tasks/pending`), claim it
  (`POST /tasks/{id}/status`), and report results (`POST /tasks/{id}/result`), without Railway ever
  reaching into Hermes.
- Model the task contract generically (`task_type` enum spanning posting, ads, research, metrics,
  integrations, docs) so Manus's full confirmed scope fits without a later schema change.
- Provide the seam that turns an **already-approved** `campaign_package` into a `post_content`
  operator task, without modifying `approval_queue_service.py`.
- Keep the side-effecting/read-only HITL split explicit and enforced server-side, not just by
  convention.

**Non-Goals:**
- Building the Hermes-side Manus API client or any Manus/Meta credential handling — that lives in
  the separate `hermes-workspace` repo, out of scope for this repo.
- Consuming/analyzing `result` payloads (CTR, CPC, research reports) — that is Change G
  (`sell-machine-telemetry-loop`).
- Any Búnker UI for operator tasks — Hermes is the consumer of this API, not a human. If a
  read-only "Operator Tasks" admin view is added later it is a separate, optional change.
- Retrying/backoff logic for dispatched-but-never-resulted tasks — out of scope; `status` transitions
  are recorded as reported, no automatic timeout/retry.

## Decisions

**1. New table `operator_tasks`, not an extension of `executor_outbox`.**
`executor_outbox` is hard-wired 1:1 to `tax_correction` approvals (NOT NULL `approval_decision_id`,
no `task_type`). Reusing it would require loosening that NOT NULL constraint and bolting on a new
enum to a table with an existing (if dormant) consumer contract. A fresh table keeps the two
outbox concerns — accounting-correction execution vs. Sell Machine operator execution — decoupled,
matching the existing "Critic name collision" lesson from Change E (don't reuse a table/module
whose existing shape encodes a different concern).

**2. `task_type` as a Postgres CHECK constraint, not a native enum type.**
Matches the established pattern in `crm_leads.stage` (Change B) rather than introducing a new
Postgres `CREATE TYPE`, which is harder to alter later and inconsistent with every prior migration
in this repo. Values: `post_content | run_ads_ab | research | metrics_pull |
external_integration | generate_doc`.

**3. Reuse the existing `SELL_MACHINE_CANONICAL` flag; no new flag.**
Unlike Change E (which needed a new flag because it introduced the first Sell Machine surface at
all), this change extends the same capability area. The flag is already `true` in production
(flipped during Change E's Stage 11). New routes register under the same flag check in
`router.py`. Risk: these new endpoints go live immediately on merge, not dark — accepted, because
(a) they are pull-only from Hermes's side (nothing calls them until Hermes is configured, which is
out of scope here), and (b) they carry the same no-request-auth posture already accepted for every
other Sell Machine/CRM endpoint (plan's R1, accepted risk). Confirmed via reading `config.py` and
`router.py` directly before deciding this, not assumed.

**4. The campaign→task conversion is a new explicit endpoint, not a hook inside `approve_draft`.**
`POST /api/v1/sell-machine/campaigns/{decision_id}/dispatch` reads the Approval Queue row directly
(via `ApprovalQueueService.list_drafts` / a direct Supabase read), verifies
`draft_type == "campaign_package"` and `status == "approved"`, and inserts a new `operator_tasks`
row (`task_type="post_content"`, `payload` = the campaign package's hooks/brief/segment/budget).
This keeps `approval_queue_service.py` completely unmodified (confirmed in proposal.md's Impact)
and keeps the HITL gate intact: dispatch is impossible before approval, since the endpoint checks
`status == "approved"` itself rather than trusting the caller.

**5. HITL split enforced server-side by task_type, not just by which endpoint is used.**
`post_content` and `run_ads_ab` (side-effecting) can ONLY be created via the dispatch endpoint
above (i.e., only from an already-approved Approval Queue draft) — a direct "create task" call
with one of these two types is rejected with 400. `research`, `metrics_pull`,
`external_integration`, `generate_doc` (read-only/no-spend) can be created directly via
`POST /api/v1/sell-machine/tasks` with no approval draft required, since they have no outbound
side effect. This makes the HITL boundary a validated invariant in the service layer, not a
frontend convention that could be bypassed by calling the API directly.

**6. Status lifecycle: `pending → dispatched → completed | failed`.**
`POST /tasks/{id}/status` (Hermes calls this once it picks up a task) only allows `pending →
dispatched`. `POST /tasks/{id}/result` (Hermes calls this after Manus finishes) allows
`dispatched → completed` or `dispatched → failed`, storing the `result` jsonb payload (shape
varies by `task_type` — a post URL + basic metrics for `post_content`/`run_ads_ab`, a report
payload for `research`/`metrics_pull`/`generate_doc`). Invalid transitions (e.g. resulting a
`pending` task) are rejected with 409, since a hung/never-dispatched task reaching `/result` would
indicate a Hermes-side bug worth surfacing rather than silently allowing.

**7. RLS and tenant scoping mirror Changes A/B/E exactly.**
`tenant_id` NOT NULL, admin-only RLS via the live `role` enum, `updated_at` trigger reusing
`update_crm_b2b_updated_at()` (already defined, generic despite the name — confirmed by reading
`0020_crm_b2b_retainers.sql`), idempotent migration (`IF NOT EXISTS`, `DROP POLICY IF EXISTS ...;
CREATE POLICY ...`).

## Risks / Trade-offs

- **[Risk] New endpoints reuse a flag that's already `true` in prod → they go live on merge, not
  dark.** → Mitigation: endpoints are pull/push-only and inert until something calls them (Hermes,
  not yet configured for this bridge); same accepted no-auth posture as every other Sell Machine
  endpoint (R1, already accepted). Stage 11 will still do a full dark-then-verify pass on the
  *table and service*, verifying via direct Supabase reads before any endpoint is exercised live,
  even though the flag itself isn't flipping.
- **[Risk] No timeout/retry for a task stuck in `dispatched`.** → Mitigation: explicitly a
  Non-Goal; Hermes-side retry policy is out of scope for this repo. Documented so Change G or a
  future Hermes-side change can address it.
- **[Risk] `operator_tasks` has no FK to `approval_queue`.** → Mitigation: intentional — a
  `post_content`/`run_ads_ab` task's `payload` carries a copy of the approved decision's data (the
  same pattern Change E used for `campaign_package`'s own payload), so the operator task remains
  self-contained and readable even if the Approval Queue row is later modified. The originating
  `decision_id` is still recorded in `payload.source_decision_id` for traceability, just not as a
  DB-level FK.

## Migration Plan

1. Migration `00XX_operator_tasks.sql` (new table + RLS + trigger), applied via Supabase MCP
   `apply_migration`, re-applied once to confirm idempotency.
2. Service (`operator_task_service.py`) + endpoints, TDD, registered in `router.py` under the
   existing `SELL_MACHINE_CANONICAL` check (same file, new routes).
3. Stage 11: commit, merge, verify Railway/Vercel green, live-verify by creating a `research` task
   via curl (no approval needed) and a `post_content` task via the dispatch endpoint against the
   real approved campaign package from Change E's own smoke test (`7b4439c3-...`), confirm both
   rows and their status transitions directly via Supabase SQL, deployment report, archive.
- **Rollback**: the table is additive and unused by any existing code path; dropping it (or simply
  leaving it unused) is a safe rollback with no cascading effect on `approval_queue` or
  `executor_outbox`.

## Open Questions

- Should a minimal read-only "Operator Tasks" Búnker view be added later for human visibility into
  what Hermes has picked up? Deferred — not needed for Hermes to function, and no user request for
  it yet.
- Exact Manus API request/response shape is still unconfirmed (per the plan's "Open decisions to
  lock later") — this change does not depend on it, since Hermes translates between this generic
  contract and whatever Manus's actual API expects.
