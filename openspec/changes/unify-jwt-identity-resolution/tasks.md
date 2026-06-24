# Tasks: Unify JWT Identity Resolution (HTTP paths)

## 0. Feature branch
- [ ] 0.1 Create feature branch for this change

## 1. Extend `core/deps.py`
- [ ] 1.1 Import `identity_resolver` from `core/identity_resolver.py`
- [ ] 1.2 In `get_current_user()`, after resolving `payload`/`id`/`email`, call `identity_resolver.resolve(sub=id, email=email, workspace_id=payload.get("tenant_id") or payload.get("workspace_id"))` and add `resolved_user_id`, `resolved_tenant_id` to the returned dict
- [ ] 1.3 When falling back to `_STAGING_USER` (auth not enforced, no/invalid token), set `resolved_user_id`/`resolved_tenant_id` to `None` (no resolution call — there's no real JWT to resolve)
- [ ] 1.4 Unit test: valid demo JWT → `resolved_user_id`/`resolved_tenant_id` populated for a known seeded user (e.g. `cliente@demo.co`)
- [ ] 1.5 Unit test: invalid/missing token, `AUTH_ENFORCED=False` → falls back to `_STAGING_USER`, `resolved_*` are `None`, no exception
- [ ] 1.6 Unit test: existing callers reading only `id`/`email` (e.g. `verify_resource_ownership`) are unaffected — no behavior change

## 2. Extend `core/tenant_middleware.py`
- [ ] 2.1 Import `identity_resolver`
- [ ] 2.2 In `dispatch()`, after extracting raw `tenant_id`/`user_id` from the payload, call `identity_resolver.resolve(...)` and set `request.state.resolved_tenant_id` / `request.state.resolved_user_id`
- [ ] 2.3 If no JWT / invalid JWT, set both resolved fields to `None` (keep existing `"default-tenant"` raw fallback behavior unchanged)
- [ ] 2.4 Unit test: valid JWT → resolved fields populated; raw `tenant_id`/`user_id` unchanged
- [ ] 2.5 Unit test: missing/invalid JWT → raw fields keep `"default-tenant"`/`None`, resolved fields are `None`, request still proceeds (no 401 introduced by this middleware)

## 3. Cross-check with the three blocked changes (read-only verification, no code changes to those folders)
- [ ] 3.1 Confirm `agent-operations-multitenant-security` §11.7 can now resolve identity for an HTTP-invoked (non-WebSocket) governance check, if any exists; otherwise note it stays WebSocket-only by design
- [ ] 3.2 Confirm `hermes-user-sync-and-onboarding` T11.1's blocker note is updated to reflect that HTTP-path resolution now exists (separate change owns updating that file's checkbox/status — do not edit it from here without revisiting that change explicitly)
- [ ] 3.3 Document in this change's reports that `hermes-multi-tenant-wrapper` T10 (Postgres-native `auth.jwt()::uuid` RLS cast) is **not** fixed by this change (per design D4) — that needs a separate JWT-claim change if Postgres-native enforcement is required

## 4. Stage 11. Deploy to Production (MANDATORY — CLAUDE.md §8)

Project-specific details:
- Deploy branch: `main` (confirm Railway service is actually pointed at `main`, not a feature branch — known footgun per `agent-operations-multitenant-security`'s Stage 11 findings)
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 4.1 git commit + push to main
- [ ] 4.2 Railway deploy active, build green
- [ ] 4.3 Runtime verification: a real authenticated HTTP request (not just a green build) hits an endpoint using `get_current_user`, confirm no exception, `resolved_user_id` non-null for a known seeded user (check via temporary log line or a debug endpoint, then remove)
- [ ] 4.4 Confirm zero regressions: existing endpoints relying on raw `id`/`tenant_id` behave identically (spot-check 2-3 endpoints pre/post deploy)
- [ ] 4.5 Create report: `openspec/changes/unify-jwt-identity-resolution/reports/YYYY-MM-DD-deployment.md`

## 5. Archive
- [ ] 5.1 Move to `openspec/changes/archive/YYYY-MM-DD-unify-jwt-identity-resolution/`
