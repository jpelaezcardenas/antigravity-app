# Agent Endpoints Real Tenant Filtering

## Why

Per-tenant client access is settled (`ARCHITECTURE.md` Decision #13, archived
`per-tenant-client-access`), but only `GET /api/v1/financials` implements it. Every other
agent-facing HTTP surface is either anonymous or fake-multi-tenant:

- `presentation/agents_endpoints.py` has no auth at all on any of its 8 routes.
- `presentation/pulso_diario_endpoints.py` / `centinela_agents_endpoints.py` read
  `request.state.tenant_id` (the raw JWT claim, or the literal string `"default-tenant"`)
  and only interpolate it into response strings — no DB call exists to filter.
- `presentation/approval_queue_endpoints.py`'s `GET ""` returns **every tenant's drafts**;
  `POST /enqueue` reads `request.state.tenant_id` but never uses it (the service hardcodes
  Cliente Cero); `/approve` and `/reject` have no ownership check at all.
- `presentation/taty_endpoints.py` and `presentation/centinela_endpoints.py` trust a
  client-supplied `company_id` with no auth and no ownership verification.

This is the same class of bug `per-tenant-client-access` fixed for financials, now confirmed
live across the agent surface — and it matches the known governance gap in `AGENTES.md:324`
("Direct HTTP calls to agents: BYPASS governance").

## What Changes

- Auth-gate (`Depends(get_current_user)`) every route in the six in-scope presentation files.
- Tenant-scope the routes that touch the DB: approval queue list/enqueue/approve/reject,
  centinela evaluate/alerts, taty ask — reusing the shared tenant-resolution helper that
  `approval-queue-tenant-scoping` is introducing in `core/tenant_context.py` (see design.md;
  this change does not invent a second one).
- Stop trusting client-supplied `company_id`; derive it from the caller's resolved tenant. A
  cross-tenant or unknown `company_id` returns **404** (anti-enumeration).
- Convert the two response-string stubs (`pulso_diario /summary`, `centinela_agents
  /generate-draft`) to echo the resolved tenant, never the raw JWT claim or
  `"default-tenant"`.
- Keep `orchestrator/full-pipeline` as the demo it already honestly is
  (`"mode": "demo"`, `agents_endpoints.py:469-474`) — just auth-gate it.
- Unauthenticated callers newly receive 401 on these routes once `AUTH_ENFORCED=true`; the
  existing staging fallback (`AUTH_ENFORCED=False`, no token) is preserved unchanged.

## BLOCKED ON (prerequisites — implementation deferred)

This session ships **artifacts only**. As of 2026-07-23, four prerequisite changes are all
in active drafting in parallel worktrees on this checkout, none archived/merged:
`approval-queue-tenant-scoping` (also introduces the shared `core/tenant_context.py`
resolution helper this change reuses), `centinela-tenant-scoped-alerts`,
`taty-per-tenant-profiles`, and `hermes-task-queue-tenant-scoping` (sequencing only, no API
consumed here). Full seam contracts are in design.md.

Do not start implementation Stages 4-6 (tasks.md) until the hard prerequisites above are
archived. Stages 1-3 (auth-gate pure-LLM/demo routes; stub conversion) have no seam
dependency and may proceed independently — see design.md and tasks.md.

## Capabilities

- **NEW**: `agent-endpoint-tenant-scoping`
- **MODIFIED**: `approval-queue`, `centinela-alerts`

## Impact

- Code: `presentation/{agents,pulso_diario,centinela_agents,approval_queue,taty,centinela}_endpoints.py`
- New tests: one file per in-scope presentation file (see design.md testing strategy)
- Docs: `AGENTES.md:324` wording, `docs/API_REFERENCE.md` auth requirements

## Non-Goals

- `sell_machine_endpoints.py` Hermes bridge routes (no auth today; out of scope, covered by
  `hermes-task-queue-tenant-scoping`'s own sequencing, not this change's API).
- `services/operator_task_service.py` (sibling change's scope).
- Restoring cost-logging/gating for direct HTTP calls to agents (AGENTES.md:324's governance
  gap is only partially closed by this change — see design.md).
- Rate limiting, replacing the orchestrator demo with a real pipeline, any DB migration.
