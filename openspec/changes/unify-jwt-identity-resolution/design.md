## Context

Verified live 2026-06-24 (see `agent-operations-multitenant-security/design.md` D6/D7 for the original discovery):

- Login (`apps/backend/application/auth_service.py`) issues a custom HS256 JWT via `core/security.py:create_access_token`. `sub` is either a hardcoded demo string (`usr_cliente_demo`, `usr_admin_demo`) or `usuarios.id` from a custom table lookup — **never** a Supabase Auth `auth.uid()`. `tenant_id`/`workspace_id` defaults to the literal string `"contexia-org-1"` when not explicitly passed (always, today).
- `user_tenants`, `user_roles`, `agent_operations` key on real UUIDs (`usuarios.id`, `tenants.id`).
- `core/identity_resolver.py` (`IdentityResolver`, service-role client) already resolves `sub`/`email` → `usuarios.id` and `workspace_id` → `tenants.id`, fail-closed (`None` on any ambiguity/error). It is wired into exactly one place: `api/websocket_handler.py`'s connect flow.
- Two more call sites read the same raw JWT claims and pass them downstream unresolved: `core/deps.py:get_current_user` (returns raw `payload["sub"]` as `id`) and `core/tenant_middleware.py:TenantContextMiddleware` (sets `request.state.tenant_id`/`user_id` from raw claims, defaulting to the string `"default-tenant"`).

## Decisions

### D1 — Additive fields, not a replacement of existing behavior
**Decision:** `get_current_user()` keeps returning `{"id": ..., "email": ...}` exactly as today, and adds two new keys: `resolved_user_id`, `resolved_tenant_id` (each `Optional[str]`, populated via `identity_resolver.resolve(...)`). Same pattern for `TenantContextMiddleware`: keep `request.state.tenant_id`/`user_id` (raw) and add `request.state.resolved_tenant_id`/`resolved_user_id`.
**Why:** `core/deps.py` and `tenant_middleware.py` are used across the whole HTTP surface (`tenant_middleware.py`'s own docstring already states "Non-invasive: existing endpoints unaware of this middleware"). Any endpoint currently comparing `payload["sub"]` to something else (e.g. `verify_resource_ownership`) must keep working unchanged. Adding fields rather than replacing them means zero behavior change for every existing consumer — only call sites that explicitly read the new `resolved_*` fields opt in.

### D2 — Fail-open at the dependency/middleware level; fail-closed only at the governance call site
**Decision:** If `IdentityResolver` can't resolve an identity, `resolved_user_id`/`resolved_tenant_id` are simply `None`. `get_current_user()` and `TenantContextMiddleware` never raise or 401 because of a resolution failure — only because of an actually invalid/missing token, exactly as today.
**Why:** This mirrors the already-shipped WebSocket precedent (D7: "resolution failure does not crash the socket, but invocations are blocked and audited" — the *blocking* happens at the agent-invocation chokepoint, not at context creation). The right place to fail closed is wherever a real RLS-backed or UUID-keyed query is about to run, not at the generic auth dependency that hundreds of unrelated endpoints depend on. Endpoints that need a resolved UUID (e.g. a new `user_tenants` RLS query) check `resolved_user_id is None` themselves and reject/403 at that point.

### D3 — Reuse `IdentityResolver` unchanged
**Decision:** No changes to `core/identity_resolver.py`. Both new call sites construct/reuse the existing module-level `identity_resolver` singleton and call `.resolve(sub, email, workspace_id)`.
**Why:** It already does exactly the right lookup (email-first for user, company_id/membership fallback for tenant), is fail-closed internally, and uses the service-role client (necessary since `user_tenants`/`user_roles` have RLS enabled with zero policies for the anon client — D6). No new behavior to design here, just reuse.
**Trade-off:** one extra Supabase round-trip per HTTP request (uncached) on top of the one the WebSocket path already pays per connection. Acceptable for now — request volume is low (internal/demo stage); a request-scoped or short-TTL cache is a future optimization, not required to unblock the three pending changes.

### D4 — Where this plugs into the three blocked changes
**Decision:** This change does not modify `hermes-multi-tenant-wrapper` or `hermes-user-sync-and-onboarding`'s own code/tasks. It only makes `resolved_user_id`/`resolved_tenant_id` available to them. Each of those changes still needs its own follow-up task to actually consume the resolved fields where it matters (e.g. `hermes-multi-tenant-wrapper`'s RLS policies still need the **JWT itself** to carry a real UUID `tenant_id` claim if they're meant to be enforced by Postgres directly via `auth.jwt()` — this change does not make that true, since it does not alter the JWT's signed claims, only what the backend resolves them to in-memory per request).
**Open follow-up (explicitly out of scope here):** if `hermes-multi-tenant-wrapper`'s RLS policies must keep checking `auth.jwt()->>'tenant_id'::uuid` directly in Postgres (rather than the backend doing an app-level check with the resolved UUID and querying via the service-role client, as D6/D2 already do for `agent_operations`), then `create_access_token` itself needs to start signing a real UUID tenant claim — a different, smaller change to `core/security.py` + `auth_service.py`, deferred until that change's owner confirms which enforcement point it actually relies on.

## Risks / Trade-offs

- Extra DB round-trip per request when resolution is invoked — mitigated by being additive/opt-in (only paid by endpoints that actually call `get_current_user`/read `request.state.resolved_*`, which today is most but not all routes; no change for routes that don't use these deps at all).
- Demo/staging fallback identity (`_STAGING_USER`, `id: "test-user-staging"`) will resolve to `None` (not a real `usuarios` row) — expected and harmless under D2's fail-open behavior.
- Does not fix Postgres-native `auth.jwt()`-based RLS (D4's open follow-up) — must be communicated clearly so `hermes-multi-tenant-wrapper` isn't assumed "unblocked" for that specific mechanism.
