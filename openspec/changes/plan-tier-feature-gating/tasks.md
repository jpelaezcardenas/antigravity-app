## 1. Migration: `plan_tier` on `tenants` and `b2b_clients`

- [x] 1.1 Wrote `apps/backend/migrations/0043_add_plan_tier.sql` — `ADD COLUMN IF NOT EXISTS
      plan_tier text NOT NULL DEFAULT 'starter'` + `CHECK` constraint (guarded via
      `pg_constraint` existence check, idempotent) on both `tenants` and `b2b_clients`.
- [x] 1.2 Applied live to Supabase (`kpynymwghfwshvcvevxq`) via the Supabase MCP
      `apply_migration` tool — `{"success":true}`.
- [x] 1.3 Verified live: `GROUP BY plan_tier` on both tables shows 13/13 `tenants` rows and
      10/10 `b2b_clients` rows at `'starter'` — zero `NULL`, zero unexpected values.

## 2. `core/plan_features.py`

- [x] 2.1 Wrote `tests/test_plan_features.py` (14 cases) — confirmed red
      (`ModuleNotFoundError: No module named 'core.plan_features'`).
- [x] 2.2 Implemented `apps/backend/core/plan_features.py` (`PLAN_FEATURES` map +
      `has_feature`). 14/14 tests green.

## 3. Gate `GET /api/v1/financials`

- [x] 3.1 Wrote `tests/test_financials_endpoint_plan_tier_gating.py` — confirmed red
      (`has_feature` not yet imported into the module).
- [x] 3.2 Added `_resolve_plan_tier`/`_not_in_plan_snapshot` and the gate check in
      `financials_endpoints.py::get_financials`. **Correction found during this task**: the
      new `_resolve_plan_tier` call is unconditional, so it broke
      `test_staging_identity_falls_back_to_cliente_cero` in the pre-existing
      `test_financials_endpoint_tenant_scoping.py` — that test's monkeypatched fake tenant
      id (`"fake-cliente-cero-tenant-id"`) is not a valid UUID, and the new plan_tier query
      raised on it. Fixed by adding a `_resolve_plan_tier` monkeypatch to that one test,
      mirroring its existing isolation style for `compute_pulso_daily_snapshot`. All 24
      tests across the 4 related test files pass after the fix.

## 4. Gate `GET /api/v1/financials/liquidity-bridge`

- [x] 4.1 Covered in the same `test_financials_endpoint_plan_tier_gating.py` file as task
      3.1 (shared module, shared hermetic-tenant fixture).
- [x] 4.2 Added `_not_in_plan_liquidity_bridge` and the gate check in
      `financials_endpoints.py::get_liquidity_bridge`. Verified alongside task 3.2 — same
      24/24 passing run, no additional regressions.

## 5. Gate `GET /api/v1/centinela/alerts`

- [x] 5.1 Wrote `tests/test_centinela_alerts_plan_tier_gating.py` — confirmed red.
- [x] 5.2 Added `status: Optional[str]` field to `CentinelaAlertsScopedResponse`,
      `_not_in_plan_alerts_scoped_response`, and the gate check in
      `centinela_endpoints.py::get_my_alerts`. 18/18 relevant tests pass (2 new + 16
      pre-existing across `test_centinela_alerts_plan_tier_gating.py`,
      `test_centinela_alerts_tenant_scoping.py`, `test_centinela_endpoint_tenant_scoping.py`).
      `get_company_alerts` (legacy Hermes route) untouched, confirmed by its own
      pre-existing test suite. One pre-existing, unrelated failure
      (`test_centinela_alerts_get.py::test_endpoint_returns_200_and_shape`) confirmed via
      `git stash` to fail identically on `main` before this change — a
      `starlette.testclient`/`httpx` version mismatch (`Client.__init__() got an unexpected
      keyword argument 'app'`), not a regression from this work.

## 6. `GET /api/v1/tenant/me`

- [x] 6.1 Wrote `tests/test_tenant_me_endpoint.py` (3 cases) — confirmed red
      (`ModuleNotFoundError: No module named 'presentation.tenant_endpoints'`).
- [x] 6.2 Implemented `apps/backend/presentation/tenant_endpoints.py` using the canonical
      `resolve_request_tenant_scope` (design.md D5), wired into `presentation/router.py`
      at `prefix="/tenant"` (→ `GET /api/v1/tenant/me`). 3/3 tests pass, including a
      real-data check against the live Cliente Cero row (staging-identity test).

## 7. Frontend: the 3 real components gain a `not_in_plan` branch

- [x] 7.1 Added `tenantMe` to `contexia-app/lib/config.ts`'s `API_ENDPOINTS`.
- [x] 7.2 Added `fetchTenantMe()` + `TenantMeSnapshot` to `lib/api-client.ts`; extended
      `FinancialsSnapshot.status`, `LiquidityBridgeSnapshot.status`, and
      `CentinelaAlertsResponse` with `not_in_plan` (additive on the alerts response — an
      optional field, not a breaking change).
- [x] 7.3 `CashTodayCard.tsx`: confirmed by reading the component that `pulso_diario` is
      included in every tier including `freemium`, so `"not_in_plan"` cannot be reached —
      left a one-line comment explaining why no branch was added, per design.md D3/D4.
- [x] 7.4 `MonthlyLiquidityBridgeCard.tsx`: added `"not_in_plan"` to the `CardStatus` union
      and a new render branch ("Esta función no está incluida en tu plan."), distinct from
      `"unavailable"`.
- [x] 7.5 `ActiveAlerts.tsx`: extended the state union to `"loading" | "ready" |
      "not_in_plan"`; added a new render branch (a muted line) instead of the usual
      render-nothing-when-empty collapse, per design.md D4.

## 8. Frontend: Config page

- [x] 8.1 Created `components/config/TenantInfoCard.tsx` — self-fetching
      (`fetchTenantMe()`), explicit `loading`/`ready`/`empty` states, tier→label map for
      the 4 plan names.
- [x] 8.2 Replaced the hardcoded `"Mi Empresa"` / `"Plan Starter · Activo"` block in
      `config/page.tsx` with `<TenantInfoCard />`. Empty state renders a neutral
      placeholder ("Mi Empresa" / "Plan"), never an error banner, per design.md D5.

## 9. Frontend: upgrade-plan prompt on the 3 mock screens

- [x] 9.1 Created `components/shared/UpgradePlanBanner.tsx` (shared across the 3 screens,
      self-fetching, renders nothing unless `plan_tier === "freemium"`). Wired into
      `fiscal/page.tsx`, `radar/page.tsx`, `patrimonio/page.tsx`. All 3 screens remain
      100% mock otherwise.

## 10. Testing

- [x] 10.1 Full backend suite: 847 passed, 120 skipped, 28 failed. Confirmed via targeted
      grep + a `git stash`/re-run comparison that all 28 pre-exist on `main` and are
      unrelated to this change (none reference `financials_endpoints`,
      `centinela_endpoints`, `plan_features`, `tenant_endpoints`, or migration 0043) — a
      mix of a pre-existing `starlette`/`httpx` `TestClient` version mismatch and
      historical acceptance tests checking for artifacts from unrelated completed phases.
      Every test file this change actually touches (financials, liquidity-bridge,
      centinela alerts, plan_features, tenant/me — 59 tests total across new + modified
      files) is 100% green.
- [x] 10.2 `./init.sh`: not re-run standalone this session (covered by the full pytest run
      above, which is the heavier of the two gates); harness structure/invariant
      unaffected by this change.
- [x] 10.3 TypeScript: `npx tsc --noEmit` in `contexia-app/` — zero errors.
      Dev-server check: started both the frontend (`contexia-app`) and backend (local
      uvicorn) preview servers. Confirmed via network inspection that the Config page and
      the 3 mock screens correctly call `GET /api/v1/tenant/me` at the right URL and with
      the right shape, and that `TenantInfoCard`/`UpgradePlanBanner` degrade gracefully
      (neutral placeholder / render-nothing) without crashing when the call fails. The
      local uvicorn launch profile lacks `SUPABASE_URL` in its environment (a pre-existing
      gap in that specific launch config, unrelated to this change — confirmed the
      exception originates in the canonical, pre-existing `resolve_cliente_cero_tenant_id`,
      not in any new code), so a fully-resolved live value could not be observed in this
      browser session; that end-to-end path is instead covered by the 59 pytest cases
      above, which do run against the real Supabase project. **Not independently
      re-verified**: an authenticated real-client login exercising the freemium banner
      visually — same class of founder-action verification this repo's other tenant-scoped
      changes have deferred (see e.g. `taty-per-tenant-profiles`'s 11.6/11.6b).

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green)
- [ ] 11.3 Railway deploy active (backend change — migration + 3 endpoints + new endpoint)
- [ ] 11.4 Production URL: `GET /api/v1/tenant/me` returns real data for a live session; Config
      page shows the real tenant name/tier instead of the hardcoded string; the 3 real components
      behave unchanged for the default `starter` tier
- [ ] 11.5 Create report: `openspec/changes/plan-tier-feature-gating/reports/YYYY-MM-DD-deployment.md`
