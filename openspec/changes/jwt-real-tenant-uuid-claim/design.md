## Context

`unify-jwt-identity-resolution` (archived 2026-06-24, design D4) explicitly deferred this:
"if `hermes-multi-tenant-wrapper`'s RLS policies must keep checking
`auth.jwt()->>'tenant_id'::uuid` directly in Postgres ... then `create_access_token` itself needs
to start signing a real UUID tenant claim." `hermes-multi-tenant-wrapper`'s tasks.md (T10) already
confirmed this is exactly the mechanism its RLS migrations rely on — so this follow-up is now in
scope.

Both login paths in `application/auth_service.py` call `create_access_token(data={"sub": ..., "email": ...})`
without a `tenant_id`, so `core/security.py`'s fallback (`"contexia-org-1"`, a literal string) is
always what gets signed today. `IdentityResolver.resolve_tenant_uuid(workspace_id, user_uuid)`
already does the exact lookup needed (UUID passthrough → `tenants.company_id` →
single active `user_tenants` membership) — it's only ever been called from the WebSocket connect
flow and, as of `unify-jwt-identity-resolution`, from `deps.py`/`tenant_middleware.py` — never at
token-issuance time.

## Decisions

### D1 — Resolve tenant UUID at login, before signing, using the existing resolver
**Decision:** In `AuthService.login()`, after determining `sub`/`email` (demo or DB path), call
`identity_resolver.resolve_user_uuid(sub, email)` to get the real `usuarios.id`, then
`identity_resolver.resolve_tenant_uuid(workspace_id=None, user_uuid=that_uuid)` to fall through
directly to the membership-based lookup (there's no `workspace_id` input at login — it doesn't
exist yet, that's what we're creating). Pass the result as `tenant_id` in `create_access_token`'s
`data` dict only if resolved; omit it otherwise (lets the existing default apply unchanged).
**Why:** Reuses the exact, already-tested resolution logic with zero new lookup code. Demo users'
emails (`cliente@demo.co`, `contexia.marketing@gmail.com`) already map to real seeded `usuarios`
rows with `user_tenants` memberships — confirmed live in `agent-operations-multitenant-security`'s
verification — so this resolves correctly for the existing demo flow without any seed-data changes.

### D2 — `sub` stays unchanged
**Decision:** Do not touch the `sub` claim. Only `tenant_id` (and therefore `workspace_id`, which
`create_access_token` mirrors from `tenant_id`) changes.
**Why:** `sub` is read in many places as a raw string identity (e.g. `usuario_id` returned to the
frontend, ownership checks). Changing it is a strictly bigger, riskier change with no benefit for
T10's specific need — T10 only needs `tenant_id` to be a real UUID for its Postgres cast. Keeps
this change minimal and contained, consistent with `unify-jwt-identity-resolution`'s same
incremental philosophy.

### D3 — Fail-open at login: never block authentication because of this
**Decision:** If `resolve_user_uuid`/`resolve_tenant_uuid` return `None` (lookup error, no
membership, demo user not yet seeded), `create_access_token` is called exactly as today — no
`tenant_id` passed, default literal applies. Login never raises because of a resolution failure.
**Why:** Mirrors the fail-open precedent from `unify-jwt-identity-resolution` D2. Availability of
login must never regress; T10's RLS cast simply continues to fail-closed (as it already does
today) for any session whose tenant couldn't be resolved at login — no worse than the current
state, and self-healing once the membership data is correct.

### D4 — One extra Supabase round-trip per login (not per request)
**Decision:** Accept the added latency at login time (two service-role lookups: user-by-email,
tenant-by-membership).
**Why:** Login is infrequent compared to per-request middleware; unlike D3 in
`unify-jwt-identity-resolution` (which pays a cost on every HTTP request), this only happens once
per session. No caching needed.

## Risks / Trade-offs

- Demo/staging users with no seeded `usuarios`/`user_tenants` row will simply keep getting the
  literal default `tenant_id` — same as today, not a regression.
- Does not fix `sub` for any RLS policy that might (incorrectly) cast `auth.jwt()->>'sub'::uuid`
  — out of scope per D2; if discovered, needs its own follow-up.
- Slightly slower login (two extra DB round-trips) — acceptable, login is not a hot path.
