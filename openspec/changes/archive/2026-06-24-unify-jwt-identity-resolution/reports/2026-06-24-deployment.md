# Deployment Report: unify-jwt-identity-resolution

**Date:** 2026-06-24
**Commits:** `882e0be` (artifacts), `50ba645` (implementation)

## What shipped

`core/identity_resolver.py`'s `IdentityResolver` — previously wired only into the WebSocket
connect flow — is now also called from:
- `core/deps.py:get_current_user()` — adds `resolved_user_id`/`resolved_tenant_id` to the
  returned dict, alongside the existing raw `id`/`email`.
- `core/tenant_middleware.py:TenantContextMiddleware.dispatch()` — adds
  `request.state.resolved_user_id`/`resolved_tenant_id`, alongside the existing raw
  `tenant_id`/`user_id`.

Both are additive and fail-open: existing consumers reading only the raw fields are unaffected;
an unresolved identity simply leaves the new fields `None` rather than raising.

## Verification

- **Tests:** 24 new/updated unit tests in `tests/test_auth_deps.py` and the new
  `tests/test_tenant_middleware.py`, all passing. Full backend suite: 230 passed, 65 skipped
  (2 pre-existing collection errors in `test_swarm_operators.py`/`test_t11_integration.py` —
  bad `sys.path` imports, unrelated to this change, not introduced by it).
- **Railway deploy branch:** confirmed pointed at `main` (the dashboard repoint from the
  `agent-operations-multitenant-security` Stage 11 findings holds) — push auto-deployed,
  deployment `567bebfb` went `SUCCESS` at `2026-06-24T23:20:23Z`, ~2 minutes after the push.
- **Runtime health (not just a green build):** `GET /api/v1/health` → `{"status":"healthy",...}`.
- **Real authenticated request:** logged in as `cliente@demo.co` via
  `POST /api/v1/auth/login`, called `GET /api/v1/pulso/usr_cliente_demo` with the resulting JWT
  → `404 {"detail":"Usuario no encontrado"}`. This is the endpoint's own business-logic response
  (not a 500/crash), proving `get_current_user()` — including the new `identity_resolver.resolve()`
  call against the real service-role Supabase client — executes cleanly in production.
- **No regressions:** existing endpoints reading only `id`/`email` (e.g.
  `verify_resource_ownership`) are unmodified in behavior; covered by unchanged pre-existing tests.

## Known gap (intentionally out of scope, see design D4)

This change does **not** make `hermes-multi-tenant-wrapper` T10's Postgres-native
`auth.jwt()->>'tenant_id'::uuid` RLS cast work — that requires the JWT itself to carry a real
UUID tenant claim (a separate, smaller change to `core/security.py`/`auth_service.py`), not
just backend-side resolution. Flagged for that change's owner to pick up if/when Postgres-native
RLS enforcement (rather than app-level checks via the resolved UUID) is required.

## Rollback

Revert commits `50ba645` and `882e0be`. No schema/migration changes; no data written; safe to
revert without any cleanup.
