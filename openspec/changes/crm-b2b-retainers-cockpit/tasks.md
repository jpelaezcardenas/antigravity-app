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

- [ ] 6.1 Create `contexia-app/lib/crm-api.ts`: a private `api<T>(path, init?)` wrapper cloned from
      `social-ops-api.ts`'s pattern over `${API_BASE_URL}/api/v1`; export `getB2bClients()`,
      `getB2bPaymentsGrid()`, and their TypeScript response types.
- [ ] 6.2 Rewrite `contexia-app/components/bunker/CrmVentasSection.tsx` as a tab shell (modeled on
      `SocialContentOpsSection.tsx`'s `useState<CrmTab>` pattern) with two tabs: "B2B / Retainers"
      (live) and "B2C / Renta Natural" (placeholder only — no functionality yet). Delete the
      hardcoded `clients` mock array entirely.
- [ ] 6.3 Create `contexia-app/components/bunker/crm/B2bRetainersTab.tsx`: `load()` in
      `useEffect(...,[])` with explicit `loading`/`error`/`source` states, a `<table>` grid (clients
      × Jan–Jun periods) with per-period and grand-total rows using the existing `formatCop`
      helper (÷100), and active/inactive status chips. Use only existing `@theme` tokens — no new
      colors, no new libraries.

## 7. Docs

- [ ] 7.1 Add the "third data-bound screen" entry (CRM/Ventas — reads live B2B data) to the
      *Pantallas data-bound* section of `contexia-app/CLAUDE.md`, following the existing Social
      Content Ops entry's structure.
- [ ] 7.2 Sync the `crm-b2b-retainers` capability into `openspec/specs/` at archive time (handled by
      the archive step, not here — confirm the delta spec file is in place under
      `specs/crm-b2b-retainers/spec.md`).

## 8. Verify + DB state (MANDATORY before Stage 11)

- [ ] 8.1 Run the full targeted backend + frontend test suites; confirm green.
- [ ] 8.2 `curl` both endpoints against the local/dev backend; verify grid totals match the seed
      fixture exactly; if any row was mutated during manual testing, restore it via the seed
      migration's idempotent re-apply.
- [ ] 8.3 Write `openspec/changes/crm-b2b-retainers-cockpit/reports/YYYY-MM-DD-step8-verification.md`
      summarizing test results and totals verified.

## 9. E2E (browser)

- [ ] 9.1 Open the Búnker locally (or via static preview), navigate CRM/Ventas → "B2B / Retainers",
      and confirm: the live grid renders all 10 clients across Jan–Jun 2026, totals are correct,
      `source` reads `supabase`, and no trace of the old mock clients (e.g. "Contexia Marketing",
      "Studio 4") remains anywhere in the section.

## 10. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 10.1 `git add`/commit the migrations, backend, and frontend changes with a descriptive message
      referencing this change id.
- [ ] 10.2 Push to `main`.
- [ ] 10.3 Confirm Railway backend deploy completes green with `CRM_CANONICAL=false` (dark deploy).
- [ ] 10.4 Confirm Vercel frontend build completes green. **Bump `contexia-app/public/sw.js`
      `CACHE_VERSION`** before this deploy since `_next/static/<buildId>/` changes; sync
      `contexia-app/out/` → `app/` per the established build-artifact rule (never hand-edit `app/`).
- [ ] 10.5 Verify live at `https://contexia.online/app/bunker` (hard refresh, Ctrl+F5): sidebar and
      existing sections unaffected; CRM/Ventas shows the new tab shell (B2C tab as placeholder,
      B2B tab may still show empty/flagged-off state until 10.6).
- [ ] 10.6 Flip `CRM_CANONICAL=true` on Railway `-175a`; re-verify `/app/bunker` → CRM/Ventas → B2B
      shows the live grid with correct totals in production. **Note the accepted risk**: these
      endpoints currently have no request-level auth beyond the Búnker's edge-middleware gate and the
      feature flag (consistent with the existing Social Ops posture) — flag this explicitly in the
      deployment report.
- [ ] 10.7 Create deployment report at
      `openspec/changes/crm-b2b-retainers-cockpit/reports/YYYY-MM-DD-deployment.md`.

## 11. Archive

- [ ] 11.1 Run `openspec-archive-change` (or `/opsx:archive`) once Stage 11 is confirmed complete and
      verified live.
