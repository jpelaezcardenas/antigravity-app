## Context

Only `presentation/financials_endpoints.py` implements the real tenant contract
(`per-tenant-client-access`, archived 2026-07-22): `user = Depends(get_current_user)` →
`resolved_tenant_id = user.get("resolved_tenant_id")`; if present, use it; elif the caller is
`_STAGING_USER` (`AUTH_ENFORCED=False`, no token), fall back to Cliente Cero; else return an
empty snapshot — **never** Cliente Cero for an authenticated-but-unresolved caller. Its test
file, `apps/backend/tests/test_financials_endpoint_tenant_scoping.py`, is this change's
testing template.

Every other agent-facing HTTP surface today (file:line references from this session's
exploration):

- `agents_endpoints.py` — no `Depends` anywhere. 6 pure-LLM routes over client-supplied data,
  1 hardcoded demo (`/orchestrator/full-pipeline`, lines 373-375/469-474 already return
  `"mode": "demo"` + an explicit "no agents are actually executed" note — this is honest, not
  a bug), 1 metadata route.
- `pulso_diario_endpoints.py:40` / `centinela_agents_endpoints.py:41` — both do
  `tenant_id = getattr(request.state, "tenant_id", "default-tenant")` (the raw JWT claim from
  `TenantContextMiddleware`, **not** the resolved UUID from `core/deps.py::get_current_user`)
  and only interpolate it into a response string. No DB call exists in either handler.
- `approval_queue_endpoints.py` — `GET ""` calls `ApprovalQueueService.list_drafts(status,
  draft_type)` with no tenant argument even though the service **already accepts one and
  filters by it** (lines 104-122) — that parameter is simply never passed. `POST /enqueue`
  reads `request.state.tenant_id` (line 112) and never uses it; the service hardcodes
  Cliente Cero (line 77). `/approve` and `/reject` take only a `decision_id` — no tenant
  check at all.
- `taty_endpoints.py` / `centinela_endpoints.py` — no auth; `company_id` is a client-supplied
  field, trusted as-is. `CentinelaService.save_alerts` hardcodes Cliente Cero (line 407).

**Hard dependency on an emerging shared helper, not a new one.** `core/tenant_context.py`
exists on `main` today with a single function, `resolve_cliente_cero_tenant_id(client)`
(extracted from `operator_task_service.py` by `hermes-multi-tenant-wrapper`). The
`approval-queue-tenant-scoping` change (drafted in parallel this session, not yet merged)
proposes generalizing this file with `resolve_request_tenant_scope(user, client) ->
TenantScope(tenant_id, all_tenants)` — the same three-branch ladder as financials, plus a
fourth outcome (a Cliente-Cero-resolved caller is an *operator* who may see every tenant's
queue). **This change reuses that helper once it lands rather than building a second,
competing one.** If `approval-queue-tenant-scoping` ships a differently-shaped helper, this
change's implementer adapts to whatever actually merged — the seam contract below is the
negotiation point, not a frozen signature.

## Goals / Non-Goals

**Goals:**
- Every agent HTTP route requires an authenticated caller.
- Every DB-touching agent route is scoped to the caller's real tenant, using one shared
  resolution helper (not six copy-pasted ladders).
- Zero behavior change for a legitimate same-tenant caller.

**Non-Goals:**
- Building a second tenant-resolution helper — `core/tenant_context.py`'s emerging
  `resolve_request_tenant_scope` is the one this change depends on and reuses.
- Reopening the orchestrator-demo decision, the Hermes-bridge exclusion, or the 404-vs-403
  choice below — these were settled with the founder before this session's artifacts were
  written.
- Cost attribution / rate limiting for the now-auth-gated pure-LLM routes (enabled by, not
  part of, this change).

## Per-endpoint tenant contract

| File / Route | Today | Target contract | Unresolved-tenant behavior | Gated by |
|---|---|---|---|---|
| `agents_endpoints.py` `/social/generate-content`, `/pulso/analyze`, `/centinela/monitor`, `/centinela/decide`, `/compliance/audit`, `/task-info/{t}` | no auth, pure LLM/no DB | auth gate only | n/a — no tenant used | — |
| `agents_endpoints.py` `/orchestrator/full-pipeline` | no auth, demo | auth gate only, `"mode":"demo"` unchanged | n/a | — |
| `agents_endpoints.py` `/taty/ask` (deprecated) | client `company_id` | auth + tenant-derived company | 404 | taty-per-tenant-profiles |
| `pulso_diario_endpoints.py` `/summary`, `centinela_agents_endpoints.py` `/generate-draft` | echo raw `request.state.tenant_id` | auth + `resolve_request_tenant_scope`; echo resolved tenant | placeholder payload, never `"default-tenant"`, never Cliente Cero for an unresolved authenticated caller | — |
| `approval_queue_endpoints.py` `GET ""` | all tenants' drafts | pass resolved `tenant_id` into the already-tenant-aware `list_drafts` | empty list | approval-queue-tenant-scoping |
| `approval_queue_endpoints.py` `POST /enqueue` | hardcoded Cliente Cero | caller's resolved tenant | 404 (cannot enqueue without a tenant) | approval-queue-tenant-scoping |
| `approval_queue_endpoints.py` `/approve`, `/reject` | no ownership check | fetch draft → compare tenant → act | 404 on mismatch/unresolved | approval-queue-tenant-scoping |
| `taty_endpoints.py` `POST`/`GET /ask` | client `company_id` | auth + tenant-derived company | 404 | taty-per-tenant-profiles |
| `centinela_endpoints.py` `POST /evaluate` | Cliente Cero hardcode in `save_alerts` | `save_alerts(..., tenant_id=resolved)` | 404 | centinela-tenant-scoped-alerts |
| `centinela_endpoints.py` `GET /alerts/{company_id}` | any company readable | verify company belongs to caller's tenant, else 404 | 404 | centinela-tenant-scoped-alerts |

## Decisions

1. **Reuse `core/tenant_context.py`'s emerging helper instead of introducing a second
   resolution mechanism.** Alternative considered: a new `core/tenant_resolution.py` with its
   own dataclass, drafted independently. Rejected mid-authoring, once this session confirmed
   `approval-queue-tenant-scoping` is already building the generalized version in the same
   file `hermes-multi-tenant-wrapper` created — two competing helpers for the same problem is
   exactly the drift `taty-lead-router-tenant-scoping` just cured elsewhere in this repo.
2. **Cross-tenant resource access returns 404, not 403.** A 403 confirms the resource exists
   under someone else's tenant — an enumeration primitive. 404 is indistinguishable from
   "never existed."
3. **Pure-LLM routes get auth-gate only, no tenant resolution.** They read no DB and write no
   DB; wiring a tenant parameter through would be dead code. Cost attribution is a natural
   follow-up once auth exists, not a requirement of this change.
4. **Stub endpoints (`pulso_diario /summary`, `centinela_agents /generate-draft`) convert now,
   ungated.** This is a contract-only change (auth + correct tenant source), has no service
   dependency, and immediately removes the `"default-tenant"` string leak — no reason to wait
   for the four prerequisites.
5. **The orchestrator demo is kept, only auth-gated** — already decided with the founder; not
   reopened here. It is honestly labeled (`"mode": "demo"`) today, so the risk it poses is
   "someone calls a documented no-op," not a data leak.

## Seam contracts expected from prerequisite changes

Written as acceptance criteria for each sibling's implementer — this change's Stage 4-6
endpoints adapt to whatever actually merges, but these are the interfaces assumed when writing
the tasks below:

- **`approval-queue-tenant-scoping`**: `core/tenant_context.py::resolve_request_tenant_scope(user, client) -> TenantScope(tenant_id, all_tenants)`; `ApprovalQueueService.enqueue_draft(..., tenant_id: str)` (no default); `approve_draft`/`reject_draft(..., tenant_id: Optional[str])` scoping the existence check and the update. **Frozen, do not re-litigate**: `list_drafts(status, draft_type, tenant_id=None)` already exists and filters correctly (lines 104-122 on `main`) — this change only needs to start passing the argument.
- **`centinela-tenant-scoped-alerts`**: `CentinelaService.save_alerts(alerts, tenant_id: str)` (no silent Cliente Cero default); a tenant-scoped read path or an equivalent `company_belongs_to_tenant(tenant_id, company_id) -> bool` for `GET /alerts/{company_id}`'s ownership check.
- **`taty-per-tenant-profiles`**: `TatyService.ask(question: str, tenant_id: str, ...)` with internal tenant→company resolution, replacing the client-supplied `company_id` parameter.
- **`hermes-task-queue-tenant-scoping`**: no API consumed by this change — sequencing dependency only (shares the harness's one-active-change invariant; this change's implementation stages must not start while it or the other three are `in_progress`, per `feature_list.json`).

## Governance limitation (AGENTES.md:324)

Today: *"Direct HTTP calls to agents: BYPASS governance (known limitation; future: middleware
wrapper)"* — the WebSocket chokepoint's Gate → Execute → Log+Cost sequence is skipped
entirely by direct HTTP.

**What this change fixes:** anonymous direct HTTP to agents is closed. Every route requires a
known identity; in production (`AUTH_ENFORCED=true`) a request with no valid token gets 401.

**What it does not fix:** cost logging and execution gating are still bypassed on direct HTTP
— this change adds *identity and tenant scoping*, not the chokepoint's cost/gate semantics.
`AGENTES.md:324` should be updated (Stage 10) from "BYPASS governance" to "authenticated and
tenant-scoped, but not cost-governed (middleware wrapper still future work)".

## Testing strategy

Mirror `test_financials_endpoint_tenant_scoping.py`: call endpoint functions directly with
fake `user` dicts (not `TestClient`/real HTTP) covering the three branches (resolved tenant,
`_STAGING_USER` → Cliente Cero, authenticated-unresolved → empty/404); hermetic two-tenant
Supabase fixtures for DB-touching routes (assert disjoint visibility, 404 on cross-tenant
access); integration tests gated by `SUPABASE_SERVICE_ROLE_KEY` (absent from local `.env`,
per this repo's known gap).

New test files: `test_agents_endpoints_auth.py`, `test_agent_stub_endpoints_tenant.py`,
`test_approval_queue_tenant_scoping.py`, `test_taty_endpoints_tenant_scoping.py`,
`test_centinela_endpoints_tenant_scoping.py`.

## Risks / Trade-offs

- **[Risk] 401-ing previously open routes breaks an unauthenticated caller that exists today**
  (frontend fetch, an internal script, or the MCP server per `mcp-agents-invocation`'s own
  JWT-bearer requirement — it should already send tokens, but verify at implementation time).
  Mitigation: the staging fallback preserves local/dev behavior unchanged; Stage 9's curl
  verification checks each route with and without a token before merge.
- **[Risk] The prerequisite seams may land shaped differently than assumed above.** Mitigation:
  the seam-contracts section is written as negotiable acceptance criteria, not a frozen
  signature; each gated stage re-verifies the actual merged interface before starting.
- **[Trade-off] 404-over-403 hides authorization failures from a legitimate but
  misconfigured caller.** Accepted — logged server-side for debugging, and consistent with
  the anti-enumeration posture already chosen for `per-tenant-client-access`.

## Open Questions

- Whether the deprecated `agents_endpoints.py::/taty/ask` should be deleted outright instead
  of scoped — deferred to `taty-per-tenant-profiles`'s own design, not decided here.
- Timing of the cost-governance middleware wrapper referenced in `AGENTES.md:324` — a
  separate future change, not scoped by this one.
