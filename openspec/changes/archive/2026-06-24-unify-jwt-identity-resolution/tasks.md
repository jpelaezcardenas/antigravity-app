# Tasks: Unify JWT Identity Resolution (HTTP paths)

## 0. Feature branch
- [x] 0.1 Worked directly on `main` (small, additive, fail-open change; consistent with this session's established workflow of pushing directly to main)

## 1. Extend `core/deps.py`
- [x] 1.1 Import `identity_resolver` from `core/identity_resolver.py`
- [x] 1.2 In `get_current_user()`, after resolving `payload`/`id`/`email`, call `identity_resolver.resolve(sub=id, email=email, workspace_id=payload.get("tenant_id") or payload.get("workspace_id"))` and add `resolved_user_id`, `resolved_tenant_id` to the returned dict
- [x] 1.3 When falling back to `_STAGING_USER` (auth not enforced, no/invalid token), set `resolved_user_id`/`resolved_tenant_id` to `None` (no resolution call — there's no real JWT to resolve)
- [x] 1.4 Unit test: valid demo JWT → `resolved_user_id`/`resolved_tenant_id` populated for a known seeded user (`test_valid_token_adds_resolved_identity`)
- [x] 1.5 Unit test: invalid/missing token, `AUTH_ENFORCED=False` → falls back to `_STAGING_USER`, `resolved_*` are `None`, no exception (`test_not_enforced_falls_back_to_staging`)
- [x] 1.6 Unit test: existing callers reading only `id`/`email` are unaffected — no behavior change (all pre-existing `test_auth_deps.py` tests still pass unmodified)

## 2. Extend `core/tenant_middleware.py`
- [x] 2.1 Import `identity_resolver`
- [x] 2.2 In `dispatch()`, after extracting raw `tenant_id`/`user_id` from the payload, call `identity_resolver.resolve(...)` and set `request.state.resolved_tenant_id` / `request.state.resolved_user_id`
- [x] 2.3 If no JWT / invalid JWT, set both resolved fields to `None` (keep existing `"default-tenant"` raw fallback behavior unchanged) — verified the resolver is not even called in this path (`test_no_token_does_not_call_resolver_and_request_proceeds`)
- [x] 2.4 Unit test: valid JWT → resolved fields populated; raw `tenant_id`/`user_id` unchanged (`test_valid_token_sets_resolved_fields`, new file `tests/test_tenant_middleware.py`)
- [x] 2.5 Unit test: missing/invalid JWT → raw fields keep `"default-tenant"`/`None`, resolved fields are `None`, request still proceeds (no 401 introduced by this middleware)

## 3. Cross-check with the three blocked changes (read-only verification, no code changes to those folders)
- [x] 3.1 Confirmed: `agent-operations-multitenant-security`'s §11.7 governance check (`invoke_agent`) is exclusively invoked over the WebSocket path — there is no separate HTTP-invoked agent governance call site today, so §11.7 stays resolved by the existing D7 WebSocket wiring; this change's HTTP-path resolution is available to any *future* HTTP governance endpoint, not a currently-blocked one.
- [ ] 3.2 Confirm `hermes-user-sync-and-onboarding` T11.1's blocker note is updated to reflect that HTTP-path resolution now exists (separate change owns updating that file's checkbox/status — do not edit it from here without revisiting that change explicitly)
- [x] 3.3 Documented (design D4): `hermes-multi-tenant-wrapper` T10 (Postgres-native `auth.jwt()::uuid` RLS cast) is **not** fixed by this change — that needs a separate JWT-claim change to `core/security.py`/`auth_service.py` if Postgres-native enforcement is required

## 4. Stage 11. Deploy to Production (MANDATORY — CLAUDE.md §8)

Project-specific details:
- Deploy branch: `main` (confirm Railway service is actually pointed at `main`, not a feature branch — known footgun per `agent-operations-multitenant-security`'s Stage 11 findings)
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 4.1 git commit + push to main (`50ba645`)
- [x] 4.2 Railway deploy active, build green (deployment `567bebfb`, SUCCESS, 2026-06-24T23:20:23Z)
- [x] 4.3 Runtime verification: real authenticated request (`cliente@demo.co` login → `GET /api/v1/pulso/usr_cliente_demo`) returns a normal business-logic 404, not a 500/crash — proves `get_current_user()`'s new `identity_resolver.resolve()` call executes cleanly against the live service-role client
- [x] 4.4 Confirm zero regressions: pre-existing tests for `verify_resource_ownership` and raw `id`/`email` consumers pass unmodified; full suite 230 passed
- [x] 4.5 Create report: `openspec/changes/unify-jwt-identity-resolution/reports/2026-06-24-deployment.md`

## 5. Archive
- [x] 5.1 Move to `openspec/changes/archive/2026-06-24-unify-jwt-identity-resolution/`
