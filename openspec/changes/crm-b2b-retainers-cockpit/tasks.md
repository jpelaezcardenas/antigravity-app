## 1. Setup + schema verification

- [x] 1.1 Create branch `feature/crm-b2b-retainers-cockpit`; capture `git status` baseline.
- [x] 1.2 Read-only SQL: confirmed live `user_roles.role` is enum `role_type` with values
      `admin | finance | marketing | growth | operator | viewer` (NOT `admin|superadmin|
      contexia_admin` — that's the separate JWT `app_metadata.role` used by the Vercel edge
      middleware). Cliente Cero tenant id confirmed: `e2d30d09-6b96-4ebe-a79a-c6aff7a5df34`
      (Contexia SAS). Confirmed `b2b_clients`/`b2b_payments` names are free (`clients` already
      exists — not colliding). Confirmed `ingestion_batches` (0019) has zero live RLS policies,
      i.e. `CREATE POLICY IF NOT EXISTS` silently no-oped — must use `DROP POLICY IF EXISTS ...;
      CREATE POLICY ...` instead.

## 2. Migration (DDL) — TDD

- [x] 2.1 Wrote `apps/backend/tests/test_crm_b2b_schema.py` (gated `RUN_CRM_B2B=1`, mirrors
      `test_shadow_gl_schema.py`): asserts both tables queryable, 10 clients + 60 payment rows
      seeded, the Don Álvaro March typo is corrected, and the grand total matches a computed
      fixture. Confirmed failing now (tables don't exist).
- [x] 2.2 Authored `apps/backend/migrations/0020_crm_b2b_retainers.sql`: `b2b_clients`,
      `b2b_payments` tables, indexes, `UNIQUE` constraints, RLS policy using the live `role_type`
      enum (`role = 'admin'`), `updated_at` trigger, idempotent (`IF NOT EXISTS`;
      `DROP POLICY IF EXISTS ... ; CREATE POLICY ...`).
- [x] 2.3 Applied via Supabase MCP `apply_migration` (project `kpynymwghfwshvcvevxq`). Confirmed live:
      both tables exist with `relrowsecurity = true`, and both `*_admin_only` policies are present
      (unlike `0019`'s policy, which silently never landed).

## 3. Seed (idempotent) — TDD

- [x] 3.1 (covered by `test_crm_b2b_schema.py`, written in 2.1) — asserts 10 clients, 60 payment
      rows, grand total, and the Don Álvaro March correction.
- [x] 3.2 Authored `apps/backend/migrations/0021_seed_b2b_retainers.sql`: inserts the 10 clients and
      their Jan–Jun 2026 `b2b_payments` rows (all 6 months per client, including 0-amount months),
      using `ON CONFLICT (client_id, period) DO UPDATE SET amount_cents = EXCLUDED.amount_cents`.
- [x] 3.3 Applied via Supabase MCP; verified live: 10 clients, 60 payment rows, grand total
      `3,732,000,000` cents (37,320,000 COP). Re-applied the full seed a second time — counts and
      total unchanged, confirming idempotency.

## 4. Backend service — TDD

- [x] 4.1 Wrote `apps/backend/tests/test_crm_service.py` (RUN_CRM_B2B=1-gated, hits live Supabase —
      asserts `source`, all 10 clients, grid shape, grand total, per-client total) and
      `apps/backend/tests/test_crm_service_grid_logic.py` (credential-free, mocks the Supabase
      client — verifies `_month_periods()` and the pivot/aggregation logic deterministically,
      independent of local env credentials).
- [x] 4.2 Implemented `apps/backend/services/crm_service.py` (`get_crm_service()` singleton,
      Supabase-preferred/demo-fallback per `social_ops_service.py`'s pattern; reads via
      `get_service_supabase()` per design.md Decision 8; resolves Cliente Cero tenant server-side
      via `is_cliente_cero = true`).
- [x] 4.3 `test_crm_service_grid_logic.py`: 6/6 passed locally (no credentials needed).
      `test_crm_service.py` (RUN_CRM_B2B=1) could not be run in this shell — the local
      `apps/backend/.env` has `SUPABASE_URL`/`SUPABASE_KEY` but **no `SUPABASE_SERVICE_ROLE_KEY`**,
      so `get_service_supabase()` fails fast with "supabase_key is required" locally. This test
      will run in CI/Railway where that key is configured (same gating convention as
      `test_shadow_gl_schema.py`); flagged as a local-environment gap, not a code defect — the
      underlying data path was independently verified correct via direct SQL through the Supabase
      MCP in Section 2/3.

## 5. Backend endpoints + feature flag — TDD

- [x] 5.1 Wrote `apps/backend/tests/test_crm_endpoints.py`: feature-flag existence/gating checks
      plus `200` + shape assertions for both routes (isolated FastAPI app,
      `httpx.AsyncClient(transport=ASGITransport(...))` + `pytest.mark.asyncio`, service layer
      mocked — the sync `fastapi.testclient.TestClient` is broken in this environment by a
      pre-existing `httpx>=0.28`/`starlette 0.27` incompatibility unrelated to this change).
      Confirmed failing before 5.2 (module didn't exist / flag not registered).
- [x] 5.2 Added `CRM_CANONICAL: bool = False` to `apps/backend/config.py`. Created
      `apps/backend/presentation/crm_endpoints.py` (`APIRouter(tags=["crm"])`) with both routes.
      Registered in `apps/backend/presentation/router.py` behind
      `if settings.CRM_CANONICAL: api_router.include_router(crm_router, prefix="/crm", ...)`.
- [x] 5.3 All 5 endpoint tests green. Manual `curl` against the live Railway backend deferred to
      Stage 11 (Section 10) since `CRM_CANONICAL` defaults `false` and flips only at deploy time;
      the mocked endpoint tests already prove the route wiring end-to-end.

## 6. Frontend client + tab shell

- [x] 6.1 Created `contexia-app/lib/crm-api.ts`: a private `api<T>(path, init?)` wrapper cloned from
      `social-ops-api.ts`'s pattern over `${API_BASE_URL}/api/v1`; exports `getB2bClients()`,
      `getB2bPaymentsGrid()`, and their TypeScript response types.
- [x] 6.2 Rewrote `contexia-app/components/bunker/CrmVentasSection.tsx` as a tab shell (modeled on
      `SocialContentOpsSection.tsx`'s `useState<CrmTab>` pattern) with two tabs: "B2B / Retainers"
      (live) and "B2C / Renta Natural" (placeholder only — no functionality yet). Deleted the
      hardcoded `clients` mock array entirely. Kept the file at its existing path (no import-path
      change needed in `app/app/bunker/page.tsx`); new sub-components live under the new
      `components/bunker/crm/` folder.
- [x] 6.3 Created `contexia-app/components/bunker/crm/B2bRetainersTab.tsx`: `load()` in
      `useEffect(...,[])` with explicit `loading`/`error`/`empty`/`source` states, a `<table>` grid
      (clients × Jan–Jun periods) with per-period and grand-total rows using the existing
      `formatCop` helper (÷100), and active/inactive status chips. Uses only existing `@theme`
      tokens — no new colors, no new libraries.

Verification: `tsc --noEmit` clean, `npm run build` green (including `/app/bunker` static export).
Visually confirmed in-browser: the tab shell renders both tabs, the old mock clients (e.g.
"Contexia Marketing", "Studio 4") are completely gone, and — critically — when the backend/flag is
unreachable the B2B tab shows an explicit "Failed to fetch" error state rather than blank/crashing,
satisfying the spec's error-state scenario. A full live-data screenshot (real 10-client grid,
`source: "supabase"`) was attempted locally but blocked by local environment constraints shared with
a concurrent session on this machine (see Section 8 notes) — deferred to the Stage 11 prod
smoke-test, where `CRM_CANONICAL` will be flipped against the real deployed backend.

## 7. Docs

- [x] 7.1 Added the "third data-bound screen" entry (Búnker → CRM/Ventas B2B, read-only) to the
      *Pantallas data-bound* section of `contexia-app/CLAUDE.md`, following the existing Social
      Content Ops entry's structure; updated the top-level "Reglas duras" bullet accordingly.
- [x] 7.2 Confirmed the delta spec file is in place at
      `specs/crm-b2b-retainers/spec.md` — ready for `openspec-sync-specs`/archive to sync into
      `openspec/specs/`.

## 8. Verify + DB state (MANDATORY before Stage 11)

- [x] 8.1 Ran the full targeted backend + frontend test suites: 11/11 backend tests green
      (credential-free); `tsc --noEmit` clean; `npm run build` green. The two RUN_CRM_B2B=1
      Supabase-hitting suites couldn't run locally (missing `SUPABASE_SERVICE_ROLE_KEY` in local
      `.env`) — deferred to CI/Railway, same convention as `test_shadow_gl_schema.py`.
- [x] 8.2 Verified live DB state directly via Supabase MCP (no local backend curl possible — see
      9.1 note): 10 clients, 60 payments, grand total `3,732,000,000` cents matching the fixture
      exactly, Don Álvaro March corrected, RLS + policies present. No rows were mutated by manual
      testing this session — re-verified counts/total unchanged after all exploratory work.
- [x] 8.3 Wrote `openspec/changes/crm-b2b-retainers-cockpit/reports/2026-07-19-step8-verification.md`.

## 9. E2E (browser)

- [x] 9.1 Opened the Búnker locally, navigated CRM/Ventas → confirmed the tab shell renders both
      tabs and no trace of the old mock clients ("Contexia Marketing", "Studio 4", etc.) remains
      anywhere. Confirmed the B2B tab shows an explicit "Failed to fetch" error state (not blank)
      when the backend/flag is unreachable — satisfies the spec's error-state scenario. A full
      live-data render (real grid, `source: supabase`) was blocked by local port contention with a
      concurrent session on this machine (port 8080 already in use) — deferred to the Stage 11 prod
      smoke-test (Section 10.5-10.6), where the flag is flipped against the real deployed backend.
      See the verification report for full detail.

## 10. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 10.1 Committed the migrations, backend, and frontend changes across 7 scoped commits on
      `feature/crm-b2b-retainers-cockpit` (600a11d, 963f0df, 1df3c59, 62acefb, 9cbc520 + the merge).
- [x] 10.2 Merged into `main` (resolved one real conflict in `CLAUDE.md`'s data-bound section against
      a concurrent session's Onboarding work — both entries kept, CRM/Ventas renumbered "cuarta") and
      pushed (`1783df7`).
- [x] 10.3 Confirmed Railway backend deploy green (dark deploy, `CRM_CANONICAL` unset/false).
- [x] 10.4 Bumped `contexia-app/public/sw.js` `CACHE_VERSION` (v9→v10; committed separately as
      `b8dd433` after a concurrent-session collision reverted the first attempt), rebuilt
      (`npm run build`), and synced `contexia-app/out/` → `app/` additively (`f26dfa4`): new buildId's
      static chunks, `app/bunker.html`/`.txt`, the previously-uncommitted `app/bunker/` RSC subfolder
      (force-added to match sibling pages), and root `sw.js`. Confirmed Vercel deploy green.
      **Caught in production verification**: one chunk (`188-e0~0ya.2n.js`, filename containing `~`)
      was missed by the initial grep-based reference check and 404'd live — root-caused to the
      check's regex not handling `~` in filenames, fixed with a proper parser, hotfixed (`9658b68`),
      redeployed, re-verified 0 missing references across all 11 real chunk refs.
- [x] 10.5 Verified live at `https://contexia.online/app/bunker`: sidebar and existing sections
      unaffected; CRM/Ventas shows the new tab shell (B2C placeholder; B2B showed the expected
      "Failed to fetch" state pre-flag-flip).
- [x] 10.6 Flipped `CRM_CANONICAL=true` on Railway `-175a`. Re-verified in production:
      `GET /api/v1/crm/b2b/clients` → `source: "supabase"`, all 10 real clients;
      `GET /api/v1/crm/b2b/payments` → `source: "supabase"`, grand total `3,732,000,000` cents; and
      the actual `/app/bunker` → CRM/Ventas → B2B UI renders the full live grid with every client,
      every month's amount, and the grand total (`$37.320.000`) matching exactly — including
      **Repuestos Don Álvaro's March = $1.200.000** (typo correctly fixed, not $12.000.000).
      **Accepted risk noted**: these endpoints have no request-level auth beyond the Búnker's
      edge-middleware gate and the feature flag (same posture as Social Ops) — documented in the
      deployment report.
- [x] 10.7 Created deployment report at
      `openspec/changes/crm-b2b-retainers-cockpit/reports/2026-07-19-deployment.md`.

## 11. Archive

- [ ] 11.1 Run `openspec-archive-change` (or `/opsx:archive`) once Stage 11 is confirmed complete and
      verified live.
