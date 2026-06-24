## Why

`agent-operations-multitenant-security` (design D7, archived path verified live 2026-06-24) discovered that the backend's HS256 JWT carries **string** identities — `sub` is a hardcoded demo string or a custom `usuarios.id`, and `create_access_token` defaults `workspace_id`/`tenant_id` to the literal `"contexia-org-1"` — while the governance tables (`user_tenants`, `user_roles`, `agent_operations`) key on real UUIDs. D7 built `core/identity_resolver.py` (`IdentityResolver`) to bridge this, but **only wired it into the WebSocket connect flow** (`api/websocket_handler.py`). D7 itself flagged the gap: "replacing that default with a real signed tenant claim is a follow-up that belongs to the auth layer, not this change."

That follow-up is now blocking three separate changes, all discovered independently while resolving OpenSpec backlog on 2026-06-24:

- `agent-operations-multitenant-security` §11.7: identity bridge decision still open for non-WebSocket call sites.
- `hermes-multi-tenant-wrapper` T10: JWT `tenant_id` is a string, so the RLS policies' `auth.jwt()->>'tenant_id'::uuid` cast fails for HTTP-authenticated requests.
- `hermes-user-sync-and-onboarding` T11.1: user authentication can't reliably resolve to a UUID-keyed `user_tenants`/`user_roles` row outside the WebSocket path.

Fixing it once, in the two HTTP-facing chokepoints (`core/deps.py`, `core/tenant_middleware.py`), unblocks all three without duplicating the work three times.

**Decision (confirmed by Juan David, 2026-06-24):** extend `IdentityResolver` into the HTTP paths rather than migrating login to real Supabase Auth sessions. Smaller blast radius — keeps the existing JWT shape and `auth_service.py` untouched; Supabase Auth migration stays a future option if ever needed.

## What Changes

- `core/deps.py`'s `get_current_user()` additionally returns `resolved_user_id` / `resolved_tenant_id` (canonical UUIDs via `IdentityResolver`), **alongside** the existing raw `id`/`email` — existing consumers that read `id` are untouched.
- `core/tenant_middleware.py`'s `TenantContextMiddleware` additionally sets `request.state.resolved_tenant_id` / `request.state.resolved_user_id`, alongside the existing raw `request.state.tenant_id` / `user_id`.
- Resolution failure is **fail-open at the dependency/middleware level** (resolved fields stay `None`; raw fields and existing behavior unchanged) — mirrors the non-invasive precedent already documented in `tenant_middleware.py`'s own docstring. Fail-**closed** enforcement stays at each specific governance call site that actually needs a UUID (e.g. an RLS-backed query), the same pattern D7 already established for the WebSocket chokepoint.
- No change to `auth_service.py`, `core/security.py`'s token shape, or the frontend.

## Capabilities

### Modified Capabilities
- `agent-operations-governance` (from `agent-operations-multitenant-security`): unblocks §11.7 by giving HTTP request handlers the same resolved-UUID identity the WebSocket path already has.

## Non-Goals

- **Not** migrating login to real Supabase Auth sessions (the larger alternative considered and explicitly deferred).
- **Not** changing the `agent_operations.user_id` column type (stays `VARCHAR`, per D8 — unaffected).
- **Not** re-running or modifying `hermes-multi-tenant-wrapper`'s or `hermes-user-sync-and-onboarding`'s own tasks.md — those changes consume this fix but are tracked separately; this change only unblocks them.

## Impact

- Modified: `apps/backend/core/deps.py`, `apps/backend/core/tenant_middleware.py`.
- Reused, unmodified: `apps/backend/core/identity_resolver.py`.
- Risk surface: auth/identity, but additive and fail-open at this layer — existing endpoints keep working unchanged even if resolution fails. Stage 11 deploy gated.
