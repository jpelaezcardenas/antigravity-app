## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/retention-loop` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Backend: retention_service.py — Failing Tests First (TDD)

- [x] 1.1 Create `apps/backend/tests/test_retention_service.py` with failing tests:
      `MissedPaymentRule.evaluate()` fires for an `activo` client with no payment in the most
      recent complete month, doesn't fire for the current in-progress month, doesn't fire for an
      `inactivo` client; `PaymentDropRule.evaluate()` fires on a material drop vs. trailing 3-month
      average, doesn't fire with fewer than 3 prior payments; `RetentionService.evaluate_roster()`
      aggregates alerts across multiple clients; `save_alerts()`/`get_alerts()` persist and read
      back scoped to `tenant_id` (mock Supabase client, no real credentials)
- [x] 1.2 Run and confirm they fail (module doesn't exist yet)

## 2. Backend: retention_service.py — Implementation

- [x] 2.1 Implement `MissedPaymentRule` and `PaymentDropRule` (small `evaluate()`-per-rule classes,
      modeled on `centinela_service.py`'s `CentinelaRule` pattern)
- [x] 2.2 Implement `RetentionService.evaluate_roster()`, `save_alerts()`, `get_alerts()` (tenant
      scoping via `core.tenant_context.require_tenant_id`, same as `CentinelaService`)
- [x] 2.3 Run and confirm all tests pass

## 3. Database: retention_alerts Migration

- [x] 3.1 Write `apps/backend/migrations/0039_retention_alerts.sql`: `retention_alerts` table
      (`id`, `tenant_id`, `client_id`, `rule_id`, `severity`, `message`, `created_at`), FK to
      `b2b_clients`, RLS admin-only (same policy shape as `centinela_alerts`)
- [x] 3.2 Apply the migration to production Supabase via Supabase MCP, verify the table exists with
      correct columns and RLS policy

## 4. Backend: Endpoint

- [x] 4.1 Add `GET /b2b/retention-alerts` to `crm_endpoints.py`, following the existing route
      conventions in that file (same auth dependency, same service-getter pattern)
- [x] 4.2 Add/update tests in `apps/backend/tests/test_crm_endpoints.py` (or equivalent) for the
      new route

## 5. Frontend: crm-api.ts + B2bRetainersTab.tsx

- [x] 5.1 Add `RetentionAlert` type and a fetch function to `contexia-app/lib/crm-api.ts`,
      following the existing `B2bPaymentsResponse`-style pattern
- [x] 5.2 Add an alerts panel to `B2bRetainersTab.tsx` with explicit loading/error/empty states (no
      mock fallback in the UI layer — matches this tab's existing data-bound convention)
- [x] 5.3 `npm run build` from `contexia-app/` and sync `out/` → `app/` (CLAUDE.md §9 — `app/` is a
      build artifact, never hand-edited)

## 6. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 6.1 Confirm no other module needs to change to support this (Approval Queue, Centinela,
      poller — all untouched by this change)
- [x] 6.2 Confirm `b2b_payments_grid()`/`create_b2b_client()`/`set_b2b_client_status()` are
      unmodified and their existing tests still pass

## 7. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [x] 7.1 Capture pre-migration baseline: confirm `retention_alerts` does not exist yet
- [x] 7.2 Run targeted tests: `test_retention_service.py`, updated `test_crm_endpoints.py`
- [x] 7.3 Run the full `apps/backend` test suite (excluding the 3 known pre-existing
      collection-broken files) and confirm no new regressions vs. the most recent baseline (797
      passed / 39 failed / 115 skipped from `copywriter-rewrite-shape-guard`)
- [x] 7.4 Verify post-migration database state: `retention_alerts` table exists with correct
      schema and RLS; no unintended mutation to `b2b_clients`/`b2b_payments`
- [x] 7.5 Create report
      `openspec/changes/retention-loop/reports/YYYY-MM-DD-step-7-unit-test-and-db-verification.md`
- [x] 7.6 Mark this section complete only after the report exists and tests are green

## 8. Manual Endpoint Testing with curl (MANDATORY — AGENT MUST EXECUTE)

- [ ] 8.1 Test `GET /api/v1/crm/b2b/retention-alerts` against the live Railway URL post-deploy;
      document status code and response shape (auth-boundary note if `get_current_user` blocks an
      unauthenticated curl, same substitution pattern as prior changes this session)
- [ ] 8.2 Document the curl command and response in the Step 7 report or a dedicated section

## 9. E2E Testing with Playwright MCP (MANDATORY — AGENT MUST EXECUTE, frontend change)

- [ ] 9.1 Navigate to `/app/bunker` → "CRM / Ventas" → "B2B / Retainers" post-deploy
- [ ] 9.2 Verify the retention-alerts panel renders (either real alerts or the explicit empty
      state) without throwing, alongside the existing payments grid
- [ ] 9.3 Verify an unreachable-backend scenario (if feasible) shows the explicit error state, not
      a blank panel
- [ ] 9.4 Document screenshots/outcomes in the Step 7 report

## 10. OpenSpec: Sync Spec + Documentation

- [x] 10.1 Confirm both delta specs (`retention-loop` new, `crm-b2b-retainers` modified) match the
      implemented behavior
- [x] 10.2 Grep `AGENTES.md`/`ARCHITECTURE.md` for CRM/retention references — update only if found

## 11. Deploy to Production (MANDATORY — CLOSES THE LOOP, Stage 11)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 11.1 Commit + merge `feature/retention-loop` into `main` + push
- [ ] 11.2 Vercel build complete (green) — frontend change
- [ ] 11.3 Railway deploy active — confirm `SUCCESS` via Railway MCP
- [ ] 11.4 Production URL: retention-alerts panel visible and working (screenshot)
- [ ] 11.5 Create deployment report:
      `openspec/changes/retention-loop/reports/YYYY-MM-DD-deployment.md`

## 12. Archive

- [ ] 12.1 Run `openspec-sync-specs` to merge both delta specs into main specs
- [ ] 12.2 Archive this change once Stage 11 is verified and all tasks above are checked
