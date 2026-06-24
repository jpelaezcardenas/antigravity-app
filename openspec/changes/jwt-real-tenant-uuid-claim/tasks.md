# Tasks: Sign a Real Tenant UUID Claim in the JWT

## 0. Feature branch
- [x] 0.1 Working directly on `main` (small, additive, fail-open; consistent with this session's workflow)

## 1. Extend `application/auth_service.py`
- [ ] 1.1 Import `identity_resolver` from `core/identity_resolver.py`
- [ ] 1.2 In the demo-user branch, after determining `sub`/`email`, resolve `user_uuid = identity_resolver.resolve_user_uuid(sub, email)`, then `tenant_uuid = identity_resolver.resolve_tenant_uuid(None, user_uuid)`; pass `tenant_id=tenant_uuid` into `create_access_token`'s data dict only when `tenant_uuid` is truthy
- [ ] 1.3 Same change in the DB-backed login branch (`user_data["id"]`/`user_data["email"]`)
- [ ] 1.4 Do not modify `core/security.py` — its existing default fallback stays as the safety net
- [ ] 1.5 Unit test: demo login (`cliente@demo.co`) → decoded token's `tenant_id` is the real seeded tenant UUID, not the literal `"contexia-org-1"`
- [ ] 1.6 Unit test: resolution failure (unknown user / no membership, mocked) → falls back to today's behavior, `create_access_token` called without `tenant_id`, login still succeeds (no exception, no 401 introduced by this change)
- [ ] 1.7 Unit test: `sub` claim is unchanged from current behavior in both tests above

## 2. Cross-check with `hermes-multi-tenant-wrapper`
- [ ] 2.1 Confirm (read-only, no edits to that change's files) that a freshly issued demo token's `tenant_id` now passes the `::uuid` cast used in that change's RLS migrations
- [ ] 2.2 Note in this change's report whether T10 is now actually unblocked end-to-end, or whether a separate verification step in `hermes-multi-tenant-wrapper` itself is still needed (that change's own task, not edited from here)

## 3. Stage 11. Deploy to Production (MANDATORY — CLAUDE.md §8)

- [ ] 3.1 git commit + push to main
- [ ] 3.2 Railway deploy active, build green
- [ ] 3.3 Runtime verification: real login (`cliente@demo.co`) against production, decode the returned JWT, confirm `tenant_id` is a real UUID
- [ ] 3.4 Confirm zero regressions: existing consumers of `sub`/`usuario_id` (frontend, other endpoints) unaffected
- [ ] 3.5 Create report: `openspec/changes/jwt-real-tenant-uuid-claim/reports/YYYY-MM-DD-deployment.md`

## 4. Archive
- [ ] 4.1 Move to `openspec/changes/archive/YYYY-MM-DD-jwt-real-tenant-uuid-claim/`
