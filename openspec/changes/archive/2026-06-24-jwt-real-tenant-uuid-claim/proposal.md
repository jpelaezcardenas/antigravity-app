## Why

`unify-jwt-identity-resolution` (archived 2026-06-24) fixed identity resolution **inside the
backend** — `core/deps.py` and `core/tenant_middleware.py` now resolve the JWT's string
`tenant_id` to a real UUID via `IdentityResolver`, in-memory, per request. That change's design
(D4) explicitly flagged a gap it did **not** close: it doesn't change what the JWT itself
**signs**. `core/security.py:create_access_token` still defaults `tenant_id` to the literal
string `"contexia-org-1"` whenever the caller doesn't pass one — which is always, today, since
neither login path (`application/auth_service.py`) passes a `tenant_id`.

This blocks `hermes-multi-tenant-wrapper` T10 specifically: its RLS policies are written as
Postgres-native casts — `auth.jwt()->>'tenant_id'::uuid` — which only work if the JWT claim
itself is a real UUID. No amount of backend-side resolution fixes a cast Postgres runs directly
on the token; only the token's signed claim can fix that.

## What Changes

- `application/auth_service.py`'s `login()` resolves the caller's real tenant UUID (via the
  existing `IdentityResolver`, same lookup `unify-jwt-identity-resolution` already uses) **before**
  calling `create_access_token`, and passes it explicitly as `tenant_id` in the token data.
- `core/security.py:create_access_token` is **unchanged** — its existing fallback to
  `"contexia-org-1"` stays as the safety net for any caller (present or future) that doesn't
  resolve a real tenant, preserving current behavior for anyone who doesn't opt in.
- `sub` (the user identity claim) is **not** changed — stays whatever it is today (demo string or
  `usuarios.id`). Only the `tenant_id`/`workspace_id` claims become real UUIDs when resolvable.
- Fail-open: if the tenant can't be resolved at login (no membership, lookup error), the token
  falls back to today's literal default — login never fails because of this.

## Capabilities

### Modified Capabilities
- `agent-operations-governance`: no functional change (already resolves identity server-side),
  but now also benefits from receiving an already-correct `tenant_id` claim instead of relying
  solely on its own resolution step.

## Non-Goals

- **Not** changing `sub` to a UUID at issuance — kept out of scope to avoid touching any code
  that compares `sub` to a hardcoded demo string or `usuarios.id` elsewhere in the codebase.
- **Not** migrating login to Supabase Auth sessions (same decision already made in
  `unify-jwt-identity-resolution`).
- **Not** modifying `hermes-multi-tenant-wrapper`'s own tasks.md/RLS migrations from this change
  — this only makes the precondition for its T10 RLS cast true; that change's owner still
  verifies the cast itself works end-to-end.

## Impact

- Modified: `apps/backend/application/auth_service.py`.
- Reused, unmodified: `apps/backend/core/identity_resolver.py`, `apps/backend/core/security.py`.
- Risk surface: auth/login — every login call gains one extra Supabase round-trip
  (tenant membership lookup) before the token is issued. Fail-open mitigates availability risk;
  Stage 11 deploy gated.
