# Deployment Report: jwt-real-tenant-uuid-claim

**Date:** 2026-06-24
**Commits:** `fa9c650` (artifacts), `72d9de4` (implementation)

## What shipped

`application/auth_service.py:login()` now resolves the caller's real tenant UUID (via the
existing `IdentityResolver`) before signing the JWT, and passes it explicitly as `tenant_id`.
`core/security.py` is unchanged — its literal `"contexia-org-1"` default remains the fail-open
fallback for any session that can't resolve. `sub` is untouched.

## Verification

- **Tests:** 3 new tests in `tests/test_auth_service.py`, all passing. Full backend suite:
  233 passed, 65 skipped (same 2 pre-existing unrelated collection errors as before, untouched
  by this change).
- **Railway deploy:** push auto-deployed via the `main`-pointed service; deployment `1f9149c2`
  went `SUCCESS` at `2026-06-24T23:38:07Z`.
- **Runtime health:** `GET /api/v1/health` → `{"status":"healthy",...}`.
- **Real login against production:** `POST /api/v1/auth/login` as `cliente@demo.co` → decoded
  the returned JWT payload:
  ```json
  {
    "sub": "usr_cliente_demo",
    "email": "cliente@demo.co",
    "tenant_id": "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34",
    "workspace_id": "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34",
    "exp": 1782346219
  }
  ```
  `tenant_id`/`workspace_id` are now the real Cliente Cero tenant UUID (`e2d30d09-...`), not the
  literal string `"contexia-org-1"`. `sub` is unchanged, confirming design D2.
- **No regressions:** `usuario_id`/`email`/`nombre_empresa` in the login response are unchanged;
  invalid-password path still returns 401 (covered by `test_demo_login_invalid_password_still_raises_401`).

## Cross-check with `hermes-multi-tenant-wrapper` (read-only, no edits to that change)

T10's precondition — a real UUID in the JWT's `tenant_id` claim, castable via
`auth.jwt()->>'tenant_id'::uuid` — is now true for any session whose tenant resolves (confirmed
for the Cliente Cero demo session above). Whether the RLS policies themselves behave correctly
end-to-end (cross-tenant block, etc.) remains that change's own verification task — not run from
here.

## Rollback

Revert commits `72d9de4` and `fa9c650`. No schema/migration changes; no data written; safe to
revert without cleanup — logins simply go back to signing the literal default `tenant_id`.
