# Agent Endpoints Real Tenant Filtering

## Why

Per-tenant client access is settled (`ARCHITECTURE.md` Decision #13). This change's original
goal (drafted 2026-07-23) was **one consistent tenant contract across every agent-facing HTTP
surface**: a single shared resolver, and a uniform anti-enumeration policy (404, not 403) for
unresolved-tenant callers, across all 6 presentation files.

Since the original draft, three parallel sessions on this checkout archived their own changes
directly into `main` (`openspec/changes/archive/2026-07-23-{approval-queue-tenant-scoping,
centinela-tenant-scoped-alerts, taty-per-tenant-profiles}`) and each independently added tenant
scoping to its own file — genuinely, with real disjoint-tenant test coverage. But they did so
**without a shared contract**, because none of them could see the others' work in progress:

- `approval_queue_endpoints.py` calls `core/tenant_context.py::resolve_request_tenant_scope`
  (a 4-outcome ladder with an operator/`all_tenants` concept) and returns **403** for an
  unresolved tenant.
- `centinela_endpoints.py` calls a second, simpler helper, `resolve_caller_tenant` (3-outcome,
  no operator concept), and returns an empty result for an unresolved tenant.
- `taty_endpoints.py` resolves tenant inline (its own copy of the 3-branch ladder, predating
  either shared helper) and returns a structured error, not an HTTP status.

This is exactly the drift `ARCHITECTURE.md` Decision #15 already flagged: *"reconciliar ambos
helpers en un único contrato queda como follow-up."* Two files
(`pulso_diario_endpoints.py::/summary`, `centinela_agents_endpoints.py::/generate-draft`) and
one file's worth of routes (`agents_endpoints.py`'s remaining 7) were untouched by any sibling
and still have **no auth at all**.

Keeping this change's original scope means finishing what it set out to do: **one canonical
resolver, one anti-enumeration policy, applied consistently across all 6 files** — not treating
the siblings' partial, inconsistent coverage as "close enough."

## What Changes

- **Unify the tenant-resolution helpers.** `core/tenant_context.py::resolve_request_tenant_scope`
  becomes the single canonical resolver (it is the superset — its 4th outcome, operator/
  `all_tenants`, simply doesn't apply to callers that don't need it). Remove
  `resolve_caller_tenant`; migrate its two call sites in `centinela_endpoints.py` to
  `resolve_request_tenant_scope(...).tenant_id`. Migrate `taty_endpoints.py`'s inline
  3-branch resolution to the same shared call.
- **Align anti-enumeration policy to 404.** `approval_queue_endpoints.py`'s 3 call sites that
  currently raise `HTTPException(403, "No tenant resolved for caller")` (enqueue, approve,
  reject) change to 404 — consistent with the original design's anti-enumeration rationale
  (a 403 confirms "you're missing permission for something that exists"; a 404 doesn't).
- Auth-gate (`Depends(get_current_user)`) all 7 remaining routes in `agents_endpoints.py`. No
  tenant parameter is threaded through — none of these routes touch the database.
- Auth-gate `pulso_diario_endpoints.py::/summary` and
  `centinela_agents_endpoints.py::/generate-draft`, and switch both from the raw
  `request.state.tenant_id` to the now-canonical `resolve_request_tenant_scope`. Responses
  never contain the literal string `"default-tenant"`.
- Keep `orchestrator/full-pipeline` as the demo it already honestly is (`"mode": "demo"`,
  `agents_endpoints.py:469-474`) — just auth-gate it.
- Update every existing test that asserts the old 403 status code or mocks the removed
  `resolve_caller_tenant` helper (`test_approval_queue_endpoint_tenant_scoping.py`,
  `test_centinela_endpoint_tenant_scoping.py`, `test_tenant_context_helpers.py`) to match the
  unified contract — these are production-deployed, already-passing tests; this change edits
  already-shipped, tenant-security-critical code, so every touched assertion gets re-verified,
  not just re-written to pass.
- Unauthenticated callers newly receive 401 on the 9 previously-anonymous routes once
  `AUTH_ENFORCED=true`; the existing staging fallback (`AUTH_ENFORCED=False`, no token) is
  preserved unchanged everywhere.

## Capabilities

- **NEW**: `agent-endpoint-tenant-scoping`
- **MODIFIED**: `approval-queue` (403→404 policy change), `centinela-alerts` (helper migration,
  no behavior change)

## Impact

- Code: `core/tenant_context.py` (remove `resolve_caller_tenant`),
  `presentation/{agents,pulso_diario,centinela_agents,approval_queue,taty,centinela}_endpoints.py`
- Existing tests updated (not just added):
  `test_approval_queue_endpoint_tenant_scoping.py`, `test_centinela_endpoint_tenant_scoping.py`,
  `test_taty_endpoints_tenant_scoping.py`, `test_tenant_context_helpers.py` (helper tests for
  `resolve_caller_tenant` removed; superseded by `test_tenant_scope_resolution.py`, which
  already covers `resolve_request_tenant_scope`)
- New tests: `test_agents_endpoints_auth.py`, `test_agent_stub_endpoints_tenant.py`
- Docs: `AGENTES.md:324` wording, `ARCHITECTURE.md` Decision #15 (mark the helper reconciliation
  done), `docs/API_REFERENCE.md` auth requirements

## Non-Goals

- Introducing a *third* resolution mechanism — `resolve_request_tenant_scope` is reused as-is,
  not redesigned.
- `sell_machine_endpoints.py` Hermes bridge routes and `services/operator_task_service.py` —
  covered by the already-archived `hermes-task-queue-tenant-scoping`; that change's own helper
  usage (`tenant_exists`, `resolve_cliente_cero_tenant_id`) is untouched here.
- Restoring cost-logging/gating for direct HTTP calls to agents (`AGENTES.md:324`'s governance
  gap is only partially closed by this change — see design.md).
- Rate limiting, replacing the orchestrator demo with a real pipeline, any DB migration.
