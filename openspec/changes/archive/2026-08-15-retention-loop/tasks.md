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

- [x] 8.1 Tested `GET /api/v1/crm/b2b/retention-alerts` against the live Railway URL — clean `401`
      (auth boundary, same substitution pattern as prior changes this session — agent never
      obtains/holds a login token)
- [x] 8.2 Documented in `reports/2026-08-15-deployment.md`

## 9. E2E Testing with Playwright MCP (MANDATORY — AGENT MUST EXECUTE, frontend change)

- [x] 9.1 Attempted: a leftover browser session from earlier in this session was authenticated,
      but as a **client-tier** login (3-section sidebar per `ARCHITECTURE.md` Decision #18) —
      CRM/Ventas is admin-only and not reachable from that session
- [x] 9.2 **Not visually confirmed live** — requires the founder's own admin session. Substitute
      evidence: zero console errors on the shared app bundle from the reachable client-tier page,
      `npm run build` passed cleanly with no TypeScript errors, and the referenced-asset check
      (9.1-equivalent orphan-chunk check) passed before staging
- [x] 9.3 Not tested (blocked by 9.1) — noted as a gap, not silently skipped
- [x] 9.4 Documented in `reports/2026-08-15-deployment.md`, including the recommended founder
      follow-up to open the tab with their own admin login

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

- [x] 11.1 Committed (`e86472a`) + fast-forward merged into `main` + pushed
      (`3e3515a..e86472a`)
- [x] 11.2 Vercel deploy `dpl_9gd4dB15nKW46RNUZ4omz5wXhUGp` confirmed `READY` via Vercel MCP
- [x] 11.3 Railway deploy `347b3e6e-3c74-469c-a6cc-b2920d56f3d9` confirmed `SUCCESS` via Railway MCP
- [x] 11.4 Production URL verified to the extent possible without an admin session — see
      `reports/2026-08-15-deployment.md` for the honest account (backend clean 401, frontend
      bundle error-free, CRM/Ventas panel itself not visually confirmed live)
- [x] 11.5 Deployment report created: `openspec/changes/retention-loop/reports/2026-08-15-deployment.md`

## 12. Archive

- [x] 12.1 Run `openspec-sync-specs` to merge both delta specs into main specs
- [x] 12.2 Archive this change once Stage 11 is verified and all tasks above are checked
