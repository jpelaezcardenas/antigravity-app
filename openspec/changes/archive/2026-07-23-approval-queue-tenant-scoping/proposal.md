# Approval Queue Tenant Scoping

## Why
Per-tenant client access is settled (`ARCHITECTURE.md` Decision #13, archived
`per-tenant-client-access`), but the Approval Queue ignores it:

- `services/approval_queue_service.py::enqueue_draft` stamps Cliente Cero's tenant_id on
  **every** draft regardless of caller — no tenant can be passed in at all.
- `presentation/approval_queue_endpoints.py` reads `request.state.tenant_id` but never uses
  it (dead variable); the GET endpoint never filters by tenant; approve/reject have no
  tenant checks at all.
- None of the 4 approval-queue endpoints resolve the caller via `Depends(get_current_user)` —
  they are effectively unauthenticated today (`TenantContextMiddleware` is fail-open).

Net effect: anything any client enqueues silently lands under Contexia's own tenant, and any
caller can list, approve, or reject any other tenant's drafts. This is the same class of bug
`per-tenant-client-access` fixed for `GET /api/v1/financials`, applied here to the approval
queue.

## What Changes
- **Service layer** (`approval_queue_service.py`): `enqueue_draft` requires an explicit
  `tenant_id` keyword argument (no default, no internal Cliente Cero resolution).
  `approve_draft`/`reject_draft` require an explicit `tenant_id: Optional[str]` keyword
  (`None` = unrestricted, only for the admin path) and scope both the existence check and the
  update by `.eq("tenant_id", ...)` when provided.
- **New shared helper** `core/tenant_context.py::resolve_request_tenant_scope(user, client)` →
  `TenantScope(tenant_id, all_tenants)`, generalizing the `financials_endpoints.py` three-way
  resolution ladder (own tenant / Cliente Cero admin+staging / empty-never-Cliente-Cero) to
  add a fourth outcome: a caller resolved to Cliente Cero is an **operator** who sees every
  tenant's queue.
- **Endpoints** (`approval_queue_endpoints.py`): all 4 routes gain
  `user: dict = Depends(get_current_user)`; GET supports an optional `?tenant_id=` filter for
  admins only; `DraftListItem` gains a `tenant_id` field.
- **Internal callers** (`resolution_agent_service.py`, `social_ops_service.py`,
  `sell_machine_service.py`) pass tenant_id explicitly at the call site — Cliente Cero is used
  by Contexia-internal agents only when resolved explicitly, never as a silent service-layer
  default.
- **Migration `0033`**: drop the bogus zeros default on `approval_queue.tenant_id` and set
  `NOT NULL` (all live rows are already backfilled to the real Cliente Cero UUID by
  `hermes-multi-tenant-wrapper`'s Ground Truth Correction #2 — verified, not repeated here).

## Impact
- **Specs:** NEW `approval-queue` capability spec (tenant scoping requirements).
- **Code:** `services/approval_queue_service.py`, `presentation/approval_queue_endpoints.py`,
  `core/tenant_context.py`, `models/approval_decisions.py` (no change needed — already has
  `tenant_id`), the 3 internal caller services above.
- **Data:** one idempotent migration (`0033`), no data backfill (already done).
- **Depends on:** `hermes-multi-tenant-wrapper` (created `core/tenant_context.py` and did the
  live backfill this change relies on — read, do not duplicate). Does **not** touch that
  change's still-open item (dropping the permissive `approval_queue_anon_all` RLS policy) —
  explicitly out of scope, application-layer scoping is the defense here.
- **Non-goals:** RLS policy cleanup; refactoring `financials_endpoints.py` to reuse the new
  helper (noted as a follow-up, its tests monkeypatch module-level names); an admin
  body-level tenant override on enqueue (no current caller needs it).
