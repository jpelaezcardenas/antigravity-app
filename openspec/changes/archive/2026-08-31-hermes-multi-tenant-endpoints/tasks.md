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
- [x] 5.4 Fix production 500: `centinela_alerts` has no `resolved` boolean column — `.eq("resolved", False)` caused postgrest error. Fix: remove the filter; use `.order("created_at", desc=True)` instead (matches `centinela_endpoints.py` pattern). Commit `0b38927`.

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

- [x] 9.1 Run all `/internal/` endpoints against the local dev server with the founder's company active in `b2b_clients`; confirm founder's company appears in `clientes` of all 5 endpoints
- [x] 9.2 Confirm `GET /api/v1/financials`, `/centinela/alerts`, (existing endpoints) still return 401 in production (AUTH_ENFORCED=true, no regression) ✅ 2026-08-31

## 10. Hermes Script Updates (WSL)

- [x] 10.1 Install `pulso.sh` at `~/.hermes/profiles/contexia/scripts/pulso.sh` — calls `/internal/pulso/all-active`, iterates 11 clients ✅
- [x] 10.2 Install `centinela.sh`, `radar.sh`, `auditoria-sombra.sh`, `social-ops.sh` — all 4 installed and verified ✅
- [x] 10.3 Manual run confirmed multi-client output: 11 clients per script, all endpoints returning data ✅ 2026-08-31

## 11. Stage 11: Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 11.1 `git commit + git push` to `main` — commit 4ec10ab
- [x] 11.2 Railway deploy active for `antigravity-app-production-175a` (green ✅) — commit a00089c
- [x] 11.3 Smoke test production: `GET /internal/health` → 200 ✅
- [x] 11.4 Smoke test production: `GET /internal/pulso/all-active` → 200 ✅, 11 active clients returned
- [x] 11.5 Confirm existing `/api/v1/*` endpoints unaffected in production — health 200, financials 401, centinela 401 (AUTH_ENFORCED=true, correct) ✅
- [x] 11.6 Trigger Hermes cron jobs manually on WSL — all 5 scripts: 11 clients each, no errors ✅ 2026-08-31
- [x] 11.7 Create deployment report: `openspec/changes/hermes-multi-tenant-endpoints/reports/2026-08-31-deployment.md` ✅
