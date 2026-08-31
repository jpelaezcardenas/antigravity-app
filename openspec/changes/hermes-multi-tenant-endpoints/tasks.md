## 1. Token Auth Dependency

- [x] 1.1 Write failing tests for `verify_hermes_token` FastAPI dependency: valid token → pass, missing header → 403, wrong token → 403, missing env var → startup error
- [x] 1.2 Implement `apps/backend/core/hermes_auth.py::verify_hermes_token` using `secrets.compare_digest` against `HERMES_BRIDGE_TOKEN` env var; raise `RuntimeError` at import time if env var is unset
- [x] 1.3 Confirm all 4 test scenarios pass

## 2. Active PWA Client Resolver

- [x] 2.1 Write failing tests for `get_active_pwa_clients()`: returns only rows with `status='activo'` AND `provision_status='provisioned'`; excludes inactive; excludes unprovisioned; returns empty list when no matches
- [x] 2.2 Implement `apps/backend/core/pwa_clients.py::ActiveClient` (typed dataclass: `company_id`, `tenant_id`, `nombre`) and `get_active_pwa_clients(supabase_client) -> list[ActiveClient]`
- [x] 2.3 Confirm all tests pass

## 3. Internal Router Scaffold

- [x] 3.1 Create `apps/backend/routers/internal.py` with an `APIRouter(prefix="/internal")` and a health endpoint `GET /internal/health` protected by `verify_hermes_token`
- [x] 3.2 Register the internal router in `apps/backend/main.py`
- [x] 3.3 Smoke test: covered by 19 unit tests (TestClient broken in this env; httpx ASGITransport used instead)

## 4. Pulso Aggregator Endpoint

- [x] 4.1 Write failing test for `GET /internal/pulso/all-active`: valid token + 2 mocked active clients → response contains 2 entries with `company_id`, `nombre`, `pulso`; `total=2`; `timestamp` is ISO UTC
- [x] 4.2 Implement `GET /internal/pulso/all-active` in `routers/internal.py` calling `PulsoDiarioService` per client with explicit `tenant_id` filter
- [x] 4.3 Confirm test passes
- [x] 4.4 Fix production 500: `get_daily_summary` hard-coded `get_supabase()` (anon/RLS client); add optional `supabase_client` param defaulting to `get_supabase()` so internal router can inject `get_service_supabase()` — prevents `.single()` on `tenants` table throwing when RLS blocks the anon call

## 5. Centinela Aggregator Endpoint

- [x] 5.1 Write failing test for `GET /internal/centinela/all-active`
- [x] 5.2 Implement `GET /internal/centinela/all-active` calling `CentinelaService` per client
- [x] 5.3 Confirm test passes

## 6. Radar Aggregator Endpoint

- [x] 6.1 Write failing test for `GET /internal/radar/all-active`
- [x] 6.2 Implement `GET /internal/radar/all-active` calling `RadarService` per client
- [x] 6.3 Confirm test passes

## 7. Auditoría Sombra Aggregator Endpoint

- [x] 7.1 Write failing test for `POST /internal/auditoria-sombra/all-active` (mode=nightly, direct service call — no self HTTP)
- [x] 7.2 Implement `POST /internal/auditoria-sombra/all-active` calling `AuditoriaSombraService` directly per client
- [x] 7.3 Confirm test passes

## 8. Social Ops Aggregator Endpoint

- [x] 8.1 Write failing test for `GET /internal/social-ops/all-active` including error-resilience scenario (one client throws → null payload + error field, others unaffected)
- [x] 8.2 Implement `GET /internal/social-ops/all-active` calling `SocialOpsService.get_briefing()` per client wrapped in try/except
- [x] 8.3 Confirm test passes

## 9. Integration Test (E2E with Cliente Cero)

- [ ] 9.1 Run all `/internal/` endpoints against the local dev server with the founder's company active in `b2b_clients`; confirm founder's company appears in `clientes` of all 5 endpoints
- [ ] 9.2 Confirm `GET /api/v1/pulso`, `/centinela/alerts`, `/radar` (existing endpoints) still return the same responses as before (no regression)

## 10. Hermes Script Updates (WSL)

- [ ] 10.1 Update `~/.hermes/profiles/contexia/scripts/pulso.sh`: change URL from `/api/v1/pulso?company_id=<hardcoded>` to `/internal/pulso/all-active`; remove `COMPANY_ID` variable; add iteration over `clientes` array
- [ ] 10.2 Update remaining 6 Hermes scripts (centinela, radar, auditoria-sombra, social-ops, and any fallback scripts) with the same URL pattern change
- [ ] 10.3 Run each updated cron script manually (dry-run) and confirm multi-client JSON output is received and iterated correctly

## 11. Stage 11: Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 11.1 `git commit + git push` to `main` — commit 4ec10ab
- [ ] 11.2 Railway deploy active for `antigravity-app-production-175a` (green ✅)
- [ ] 11.3 Smoke test production: `curl https://antigravity-app-production-175a.up.railway.app/internal/health -H "Authorization: Bearer <HERMES_BRIDGE_TOKEN>"` → 200
- [ ] 11.4 Smoke test production: `GET /internal/pulso/all-active` → founder's company in `clientes`
- [ ] 11.5 Confirm existing `/api/v1/*` endpoints unaffected in production
- [ ] 11.6 Trigger Hermes cron jobs manually on WSL; confirm multi-client output
- [ ] 11.7 Create deployment report: `openspec/changes/hermes-multi-tenant-endpoints/reports/YYYY-MM-DD-deployment.md`
