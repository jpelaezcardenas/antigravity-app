## Context

This change's original goal (2026-07-23 draft): one shared tenant-resolution helper and one
anti-enumeration policy across all 6 agent-facing HTTP files. All 4 originally-blocking sibling
changes have since archived directly into `main`
(`openspec/changes/archive/2026-07-23-{approval-queue-tenant-scoping,
centinela-tenant-scoped-alerts, taty-per-tenant-profiles, hermes-task-queue-tenant-scoping}`).
Three of them added real, tested tenant scoping to their own files — but independently, so the
repo now has **three different resolution paths** for the same problem:

1. `approval_queue_endpoints.py` (4 call sites) — `core/tenant_context.py::
   resolve_request_tenant_scope(user, client) -> Optional[TenantScope(tenant_id, all_tenants)]`.
   Unresolved → `HTTPException(403, "No tenant resolved for caller")` at 3 of the 4 sites
   (enqueue, approve, reject — `list_drafts`'s `GET ""` just returns an empty list, no
   exception).
2. `centinela_endpoints.py` (2 call sites) — `core/tenant_context.py::resolve_caller_tenant(user,
   client) -> Optional[str]`, a simpler 3-branch ladder with no operator/`all_tenants` outcome.
   Unresolved → empty result (`source="none"` / `save_skipped_reason="tenant_unresolved"`).
3. `taty_endpoints.py`::`/ask` — its own inline copy of the same 3-branch ladder (predates both
   shared helpers), using an async, file-local `_resolve_cliente_cero_tenant_id()` instead of
   `core/tenant_context.py`'s sync one. Unresolved → a structured `error_code:
   "tenant_not_resolved"` response, not an HTTP error.

`ARCHITECTURE.md` Decision #15 already names this exact drift as a known, unresolved follow-up.
Two files (`pulso_diario_endpoints.py::/summary`, `centinela_agents_endpoints.py::
/generate-draft`) and `agents_endpoints.py`'s remaining 7 routes were untouched by any sibling
and still have no auth.

This design closes both gaps: the 2 untouched files/route-group get auth-gated (as originally
planned), and the 3 already-scoped files get migrated onto one canonical helper with one
anti-enumeration policy — completing the original single-contract goal instead of leaving it
half-done across parallel sessions.

## Goals / Non-Goals

**Goals:**
- Every agent HTTP route requires an authenticated caller.
- Every DB-touching agent route resolves tenant via **one** helper:
  `core/tenant_context.py::resolve_request_tenant_scope`.
- One anti-enumeration policy: unresolved-tenant callers on a write/ownership-checked route get
  404, never 403 (confirms nothing about what exists) and never Cliente Cero's data.
- Zero behavior change for a legitimate same-tenant caller on any of the 6 files.

**Non-Goals:**
- Designing a *different* shared helper — `resolve_request_tenant_scope` already exists, is
  tested (`test_tenant_scope_resolution.py`), and is a strict superset of what
  `resolve_caller_tenant` and Taty's inline logic do.
- Changing `resolve_request_tenant_scope`'s own 4-branch semantics (operator/`all_tenants`) —
  reused as-is.
- Cost attribution / rate limiting for the now-auth-gated pure-LLM routes.

## Per-endpoint tenant contract

| File / Route | Today | Target contract | Unresolved-tenant behavior |
|---|---|---|---|
| `agents_endpoints.py` `/social/generate-content`, `/pulso/analyze`, `/centinela/monitor`, `/centinela/decide`, `/compliance/audit`, `/task-info/{t}` | no auth, pure LLM/no DB | auth gate only | n/a — no tenant used |
| `agents_endpoints.py` `/orchestrator/full-pipeline` | no auth, demo | auth gate only, `"mode":"demo"` unchanged | n/a |
| `pulso_diario_endpoints.py` `/summary`, `centinela_agents_endpoints.py` `/generate-draft` | echo raw `request.state.tenant_id` | auth + `resolve_request_tenant_scope`; echo `scope.tenant_id` | placeholder payload, never `"default-tenant"` |
| `approval_queue_endpoints.py` `GET ""` | already scoped via `resolve_request_tenant_scope` | **unchanged** | empty list (unchanged) |
| `approval_queue_endpoints.py` `POST /enqueue`, `/approve`, `/reject` | already scoped, 403 on unresolved | **same helper, 403 → 404** | 404 (was 403) |
| `centinela_endpoints.py` `POST /evaluate`, `GET /alerts/{company_id}` | already scoped via `resolve_caller_tenant` | migrate to `resolve_request_tenant_scope(...).tenant_id` | unchanged (empty/`source="none"`) |
| `taty_endpoints.py` `/ask` (POST+GET) | already scoped via inline 3-branch logic | migrate to `resolve_request_tenant_scope(...).tenant_id` | unchanged (`error_code="tenant_not_resolved"`) |

Note: only approval-queue's *response code* changes (403→404). Centinela's and Taty's
observable behavior is unchanged — only their internal resolution call site moves to the
canonical helper. This is a refactor for them, not a contract change; the proof of "no
behavior change" is that their existing tests pass unmodified except for the mock target
(`resolve_caller_tenant` → `resolve_request_tenant_scope`) and any inline resolution mock in
Taty's test file.

## Decisions

1. **`resolve_request_tenant_scope` is the canonical helper, not a new one.** It is already the
   superset: its 4th outcome (operator/`all_tenants`) is simply unused by centinela, taty, and
   the two stubs — they only ever read `.tenant_id`. Building a fourth helper, or trying to
   strip `TenantScope` down to a bare `Optional[str]`, would be more code for less clarity.
2. **`resolve_caller_tenant` is removed, not deprecated-and-kept.** It has exactly one caller
   file (`centinela_endpoints.py`, 2 call sites) and its own dedicated test file
   (`test_tenant_context_helpers.py`) that duplicates coverage `test_tenant_scope_resolution.py`
   already has for `resolve_request_tenant_scope`. Keeping both invites the next session to
   pick either one at random — the exact failure mode this change exists to close.
3. **Approval-queue's 403 becomes 404.** A 403 on an unresolved-tenant caller confirms "there is
   something here you're not allowed to see"; 404 doesn't. This was decided for the *original*
   design of this change and simply wasn't in scope for the session that shipped
   `approval-queue-tenant-scoping` (it didn't touch this decision at all). Fixing it now is
   completing this change's original scope, not re-litigating someone else's decision.
4. **Taty's async, file-local `_resolve_cliente_cero_tenant_id()` is retired in favor of the
   sync `core/tenant_context.py::resolve_cliente_cero_tenant_id`** (already called internally by
   `resolve_request_tenant_scope`). Taty's route stays `async def`; calling a sync helper from
   an async route is the same pattern `approval_queue_endpoints.py` and `centinela_endpoints.py`
   already use.
5. **Pure-LLM routes and the demo pipeline get auth-gate only, no tenant resolution.** They
   touch no database; wiring a tenant parameter through would be dead code.
6. **Existing tests for already-shipped code are edited, not left alone, and re-run before and
   after.** This change touches tenant-security-critical, deployed code
   (`approval_queue_endpoints.py`, `centinela_endpoints.py`, `taty_endpoints.py`) — every
   touched test's assertion is re-verified against the new call path, not just updated to make
   the suite green.

## Migration mechanics (the 3 already-shipped files)

- **`centinela_endpoints.py`** (2 sites, `presentation/centinela_endpoints.py:120,195`): replace
  `tenant_id = resolve_caller_tenant(user, get_service_supabase())` with
  `scope = resolve_request_tenant_scope(user, get_service_supabase()); tenant_id = scope.tenant_id
  if scope else None`. Import swap only; no behavior change (centinela never reads
  `scope.all_tenants`).
- **`taty_endpoints.py`** (both `/ask` handlers, `presentation/taty_endpoints.py:176-189`):
  replace the inline `if/elif/else` (currently returning the `tenant_not_resolved` structured
  response in the `else` branch) with the same `scope = resolve_request_tenant_scope(...)`
  pattern; keep the existing `tenant_not_resolved` structured response for `scope is None` so
  the observable API contract for Taty callers is unchanged. Delete the now-unused
  `_resolve_cliente_cero_tenant_id()` local helper.
- **`approval_queue_endpoints.py`** (3 sites, lines ~139/191/230): change
  `HTTPException(status_code=403, ...)` to `status_code=404`; update the inline comments at
  lines 131/185 describing the 403 policy.
- **Tests to update** (not delete, not leave stale):
  - `test_tenant_context_helpers.py`: remove the 3 `resolve_caller_tenant`-specific tests
    (lines ~68-84); `test_tenant_scope_resolution.py` already covers the same 3 branches for
    `resolve_request_tenant_scope`.
  - `test_centinela_endpoint_tenant_scoping.py`: swap the monkeypatch target from
    `resolve_caller_tenant` to `resolve_request_tenant_scope`, returning a `TenantScope` instead
    of a bare string.
  - `test_taty_endpoints_tenant_scoping.py`: swap whatever mocks the inline
    `_resolve_cliente_cero_tenant_id`/`resolved_tenant_id` branch to mock
    `resolve_request_tenant_scope` instead; assertions on `tenant_id` values and `error_code`
    stay the same.
  - `test_approval_queue_endpoint_tenant_scoping.py`: rename and update
    `test_authenticated_unresolved_enqueue_returns_403_never_cliente_cero`,
    `test_approve_unresolved_returns_403`, `test_reject_unresolved_returns_403` → assert 404;
    update the docstring table at the top of the file (lines 14-16) that documents the 403
    policy.

## Governance limitation (AGENTES.md:324)

Today: *"Direct HTTP calls to agents: BYPASS governance (known limitation; future: middleware
wrapper)"*.

**What the archived siblings already fixed:** approval-queue, taty, and centinela HTTP routes
require identity and are tenant-scoped (with the drift this change now reconciles).

**What this change fixes on top:** the remaining `agents_endpoints.py` routes and the two stub
endpoints also require identity — closing anonymous direct-HTTP access repo-wide — and every
DB-touching route now shares one resolution contract.

**What nothing has fixed yet:** cost logging and execution gating are still bypassed on direct
HTTP entirely. `AGENTES.md:324` should be updated (Stage 9) from "BYPASS governance" to
"authenticated and tenant-scoped, but not cost-governed (middleware wrapper still future
work)". `ARCHITECTURE.md` Decision #15 should be updated to mark the two-helper reconciliation
done, citing this change.

## Testing strategy

For the 2 previously-untouched files: mirror `test_financials_endpoint_tenant_scoping.py`'s
approach (call endpoint functions directly with fake `user` dicts). No DB fixtures needed —
neither file touches the database.

For the 3 already-shipped files: **run their existing test suites red-then-green** around the
migration — after swapping the mock target/status code, every existing assertion must still
pass with the same observable meaning (same tenant_id resolved, same empty/error shape),
proving the migration is a pure refactor plus the one intentional 403→404 change.

New test files: `test_agents_endpoints_auth.py`, `test_agent_stub_endpoints_tenant.py`.
Updated test files: `test_tenant_context_helpers.py`, `test_centinela_endpoint_tenant_scoping.py`,
`test_taty_endpoints_tenant_scoping.py`, `test_approval_queue_endpoint_tenant_scoping.py`.

## Risks / Trade-offs

- **[Risk] This change edits already-deployed, tenant-security-critical production code**
  (approval-queue, centinela, taty), not just previously-anonymous routes. Mitigation: each
  migrated file's full existing test suite must pass unmodified in observable outcome (Decision
  6); Stage 8's curl verification re-checks all three files' tenant isolation in addition to the
  2 new files, before merge.
- **[Risk] 401-ing previously open `agents_endpoints.py`/stub routes breaks an unauthenticated
  caller that exists today** (frontend fetch, internal script, or the MCP server per
  `mcp-agents-invocation`'s own JWT-bearer requirement). Mitigation: staging fallback preserves
  local/dev behavior; curl verification checks each route with and without a token.
- **[Trade-off] Removing `resolve_caller_tenant` is a breaking change for any future caller that
  might have been about to use it.** Accepted — it has exactly one current caller file, fully
  migrated in this same change; a repo-wide grep in Stage 1 re-confirms no other caller exists
  before deletion.

## Open Questions

- Timing of the cost-governance middleware wrapper referenced in `AGENTES.md:324` — a separate
  future change, not scoped by this one.
