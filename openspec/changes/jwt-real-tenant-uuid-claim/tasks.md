# Tasks: Sign a Real Tenant UUID Claim in the JWT

## 0. Feature branch
- [x] 0.1 Working directly on `main` (small, additive, fail-open; consistent with this session's workflow)

## 1. Extend `application/auth_service.py`
- [x] 1.1 Import `identity_resolver` from `core/identity_resolver.py`
- [x] 1.2 In the demo-user branch, after determining `sub`/`email`, resolve `user_uuid = identity_resolver.resolve_user_uuid(sub, email)`, then `tenant_uuid = identity_resolver.resolve_tenant_uuid(None, user_uuid)`; pass `tenant_id=tenant_uuid` into `create_access_token`'s data dict only when `tenant_uuid` is truthy
- [x] 1.3 Same change in the DB-backed login branch (`user_data["id"]`/`user_data["email"]`)
- [x] 1.4 Did not modify `core/security.py` — its existing default fallback stays as the safety net
- [x] 1.5 Unit test: demo login (`cliente@demo.co`) → decoded token's `tenant_id` is the real seeded tenant UUID, not the literal `"contexia-org-1"` (`test_demo_login_signs_real_tenant_uuid`)
- [x] 1.6 Unit test: resolution failure (unknown user / no membership, mocked) → falls back to today's behavior, login still succeeds (`test_demo_login_falls_back_when_unresolved`)
- [x] 1.7 Unit test: `sub` claim unchanged in both tests above; invalid-password 401 path still works (`test_demo_login_invalid_password_still_raises_401`)

## 2. Cross-check with `hermes-multi-tenant-wrapper`
- [x] 2.1 Confirmed via unit test: a freshly issued demo token's `tenant_id` is now a real UUID string, which passes a `::uuid` Postgres cast (literal `"contexia-org-1"` would not)
- [x] 2.2 Noted in report: T10's RLS cast precondition is now true for any session whose tenant resolves; end-to-end RLS behavior (cross-tenant block, etc.) is still `hermes-multi-tenant-wrapper`'s own task to verify, not edited from here

## 3. Stage 11. Deploy to Production (MANDATORY — CLAUDE.md §8)

- [ ] 3.1 git commit + push to main
- [ ] 3.2 Railway deploy active, build green
- [ ] 3.3 Runtime verification: real login (`cliente@demo.co`) against production, decode the returned JWT, confirm `tenant_id` is a real UUID
- [ ] 3.4 Confirm zero regressions: existing consumers of `sub`/`usuario_id` (frontend, other endpoints) unaffected
- [ ] 3.5 Create report: `openspec/changes/jwt-real-tenant-uuid-claim/reports/YYYY-MM-DD-deployment.md`

## 4. Archive
- [ ] 4.1 Move to `openspec/changes/archive/YYYY-MM-DD-jwt-real-tenant-uuid-claim/`
