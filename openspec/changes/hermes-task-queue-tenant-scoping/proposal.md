# Proposal: hermes-task-queue-tenant-scoping

## Why

Since `per-tenant-client-access` (ARCHITECTURE.md Decision #13), every B2B client has its own
tenant — but the `operator_tasks` queue that bridges the backend to Hermes (local, on-prem
orchestrator of the 9 agents; Hermes always pulls, ARCHITECTURE.md Decision #1) is still
tenant-blind: `create_task()` stamps Cliente Cero unconditionally, `list_pending_tasks()` returns
every pending row with no tenant contract, and the 5 HTTP routes Hermes polls bypass the
`AgentAccessControl` governance that guards the WebSocket chokepoint (documented limitation,
AGENTES.md:324; archived change `agent-operations-multitenant-security` Decision D1). As Contexia
onboards real B2B clients whose tasks flow through this queue, an agent that can't tell which
tenant it's working for is a correctness bug waiting to happen, and the unauthenticated write path
into a service-role table is a governance gap the repo has already flagged but never closed.

This change makes three changes: (a) `create_task()`/`dispatch_campaign_package()` accept and
stamp the real client tenant, falling back to Cliente Cero only explicitly and with a logged
warning — never a silent default; (b) the Hermes poll payload contractually includes `tenant_id`
(explicit column projection, not an accident of `select *`); (c) the HTTP bridge gets a concrete,
backward-compatible mitigation: an env-gated bearer token (fail-open until configured), audit
parity via the existing `agent_operations` log, and write-time tenant validation. Full
`AgentAccessControl` reuse was evaluated and rejected — its check is "is this user a member of
this tenant," which is vacuous for Hermes, a machine that legitimately serves every tenant with no
user identity of its own.

## What Changes

- `operator_task_service.create_task()` gains an optional `tenant_id` param; omitting it falls
  back to Cliente Cero with a logged warning instead of a silent default.
- `operator_task_service.list_pending_tasks()` gains an optional `tenant_id` filter and switches
  from `select("*")` to an explicit column projection that always includes `tenant_id`.
- `operator_task_service.dispatch_campaign_package()` derives the tenant from the approval
  decision's `tenant_id` field (added by the concurrent `hermes-multi-tenant-wrapper` change),
  falling back to Cliente Cero only for legacy decisions that lack it.
- New `tenant_exists()` helper in `core/tenant_context.py` (additive only).
- New env-gated `HERMES_BRIDGE_TOKEN` bearer-auth dependency on the 5 operator-task HTTP routes
  (fail-open when unset).
- The 4 mutating operator-task endpoints record to `agent_operations` for audit parity with the
  WebSocket governance path.

## Non-Goals

- No changes to the Hermes-side poller (lives in the separate `hermes-workspace` repo) — activating
  the bearer token is a founder follow-up task, out of this change's Stage 11.
- No schema migration — `operator_tasks.tenant_id` is already `NOT NULL` with RLS
  (migration `0024_operator_tasks.sql`).
- No changes to `list_completed_tasks()`, `mark_dispatched()`, or `report_result()` — out of scope.
- Not replacing the accepted-risk posture (archived `hermes-manus-execution-bridge` design.md R1)
  with full user authentication — Hermes remains a machine peer, not a browser session.
- Not reusing `AgentAccessControl` — evaluated and rejected (see design.md D5).
