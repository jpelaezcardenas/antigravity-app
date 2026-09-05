## 1. Database

- [x] 1.1 Write `apps/backend/migrations/0047_radar_module_opens.sql`: table with `tenant_id`, nullable `user_id`, `opened_on DATE`, `created_at`; a unique index making (tenant, user, day) one row including when `user_id IS NULL`; an index for the weekly rollup; RLS enabled with a tenant-scoped policy via `user_tenants` plus a `service_role` policy — copying migration `0045`'s pattern, never `USING (true)`.

## 2. Backend — recording

- [x] 2.1 Write failing tests in `apps/backend/tests/test_radar_adoption_tracking.py`: `record_module_open` inserts one row scoped to the given tenant/user/day, and swallows (logs, does not raise) when the client raises.
- [x] 2.2 Implement `record_module_open(tenant_id, user_id, supabase_client=None)` in `services/radar_service.py` — upsert with `ON CONFLICT DO NOTHING` semantics, wrapped so no exception escapes. Make 2.1 pass.

## 3. Backend — endpoint wiring

- [x] 3.1 Write a failing test asserting `get_cash_projection` calls `record_module_open` with the resolved tenant when the tenant resolves, and does **not** call it when the tenant is unresolved.
- [x] 3.2 Write a failing test asserting the endpoint still returns its normal 200 projection body when `record_module_open` raises.
- [x] 3.3 Wire the call into `presentation/radar_endpoints.py::get_cash_projection`, documenting in the docstring that this read endpoint has a deliberate telemetry side effect (design.md Decision #1). Make 3.1 and 3.2 pass.

## 4. Verification

- [x] 4.1 Full radar test suite green; confirm no regression against the archived change's 16 tests.
- [x] 4.2 Run the recording against the real Supabase — **PASS**: 1 call = 1 row, 3 calls = still 1 row, cleanup 0. This run also surfaced the two silent-no-op bugs recorded in design.md (anon client hitting the `user_roles` policy recursion; `ON CONFLICT` unable to infer a partial index).

## 5. Documentation

- [x] 5.1 Add the endpoint's telemetry side effect to `ARCHITECTURE.md`'s Radar de Caja bullet, so the living doc does not describe it as purely read-only.

## 6. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app
- Frontend: no change in this delta

Tasks:
- [ ] 6.1 git commit + push to main
- [ ] 6.2 Railway deploy active, health check green
- [ ] 6.3 Apply migration `0047` to production — **requires explicit founder approval**, per this repo's practice for schema changes. The code is fail-soft, so it is safe to deploy before this lands.
- [ ] 6.4 Confirm a real open is recorded in production after the migration is applied
- [ ] 6.5 Create report: `openspec/changes/radar-adoption-tracking/reports/YYYY-MM-DD-deployment.md`

## 7. Archive

- [ ] 7.1 Archive once Stage 11 is verified.
