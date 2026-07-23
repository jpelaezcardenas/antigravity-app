# Tasks — PWA Tenant-Aware Screens (next wave)

## Stage 0. Setup
- [x] 0.1 Isolated worktree + branch `feature/pwa-tenant-aware-screens` created from `main`
  (`../antigravity-app-pwa-tenant-aware-screens`) — a parallel session held uncommitted WIP on the
  shared checkout, so this change runs in its own worktree per `using-git-worktrees`.
- [x] 0.2 `./init.sh` green in the new worktree.

## Stage 1. Backend: shared tenant resolver (TDD)
- [x] 1.1 Extracted `resolve_caller_tenant_id(user, cliente_cero_resolver=None) -> str | None`
  into `core/tenant_context.py` (optional injectable resolver, needed to preserve the existing
  regression test's monkeypatch seam — see `progress/impl_stage1.md`). Existing
  `tests/test_financials_endpoint_tenant_scoping.py` stayed green, unmodified (39/39 targeted
  tests passing). Commit `7403968`.
- [x] 1.2 Refactored `get_financials` to call the extracted helper. No behavior change, verified
  by the unmodified regression suite.

## Stage 2. Backend: tenant-scoped alerts route (TDD)
- [x] 2.1 Failing tests first — `tests/test_centinela_alerts_tenant_scoping.py`: own-tenant
  alerts; two-tenant isolation; staging → Cliente Cero; authenticated-unresolved → empty (Cliente
  Cero resolver never invoked); no-rows → honest empty list. Commit `95945f0`.
- [x] 2.2 Implemented `GET /api/v1/centinela/alerts` in `presentation/centinela_endpoints.py`
  using the Stage 1 resolver — no demo fallback (spec `centinela-alerts`).
- [x] 2.3 Green: 5/5 new tests + `test_centinela_alerts_get.py` unchanged (3/4 pass; the 4th,
  `test_endpoint_returns_200_and_shape`, fails on a pre-existing `starlette`/`httpx`
  `TestClient` version mismatch in this environment, confirmed via `git stash` to predate this
  change — not caused by or fixable within this task).

## Stage 3. Backend: liquidity bridge endpoint (TDD)
- [x] 3.1 Failing tests first — `tests/test_financials_liquidity_bridge.py`: bridge math on
  hermetic throwaway tenants (reused `insert_test_entry` from `test_financials_aggregation.py`);
  `final_balance` equals the equivalent `caja_real`; empty tenant; tenant isolation; month
  boundary. Commit `3c809fb`.
- [x] 3.2 `compute_liquidity_bridge(tenant_id, year, month)` in `services/financials_service.py`,
  reusing `_compute_caja_real_balance`.
- [x] 3.3 `GET /api/v1/financials/liquidity-bridge` in `presentation/financials_endpoints.py`,
  same resolver as Stage 1.
- [x] 3.4 Green: 5/5 new tests + `test_financials_aggregation.py` +
  `test_financials_endpoint_tenant_scoping.py` unchanged).

## Stage 4. Backend: rolling reseed of synthetic Shadow GL
- [x] 4.1 Verified `pg_cron` extension on project `kpynymwghfwshvcvevxq` via Supabase MCP
  `list_extensions`: already installed (`installed_version: "1.6.4"`, schema `pg_catalog`). No
  `create extension` step needed; migration can call `cron.schedule` directly (design.md D4
  primary path confirmed — fallback not needed).
- [x] 4.2 Wrote `migrations/0033_rolling_reseed_synthetic_shadow_gl.sql`: one-shot UPDATE
  re-dating `SYNTH-*-SALE`/`SYNTH-*-EXPENSE` rows to `CURRENT_DATE - 1` (idempotent, excludes
  `-OPEN`), plus an idempotent daily `cron.schedule` doing the same. Commit `fa61548`.
- [x] 4.3 Read-only dry-run (PostgREST, since Supabase MCP wasn't available in that subagent's
  tool list) confirmed 19 matching rows against real production — 9 `-SALE` + 10 `-EXPENSE`
  (Nia Cano's 2 rows correctly absent per migration 0030; CÓDIGO 520 correctly has no `-SALE`,
  only `-EXPENSE`, per 0028's own conditional). Migration file exists on disk only — not applied
  to production; that happens in Stage 13 (deploy).

## Stage 5. Backend: review and full unit-test + DB verification (MANDATORY)
- [ ] 5.1 Capture pre-test baseline: row counts for `centinela_alerts` and `erp_journal_lines` per
  scratch/throwaway tenant used by new tests.
- [ ] 5.2 Run targeted tests (Stages 1–3 new files) then the full backend suite
  (`pytest apps/backend/tests/`).
- [ ] 5.3 Verify no unintended mutation of production-adjacent data (throwaway tenants only;
  cleanup asserted in test teardown, matching the existing `test_financials_aggregation.py`
  pattern).
- [ ] 5.4 Report:
  `openspec/changes/pwa-tenant-aware-screens/reports/2026-07-XX-step-5-unit-test-and-db-verification.md`.

## Stage 6. Backend: manual endpoint testing with curl (MANDATORY — AGENT MUST EXECUTE)
- [ ] 6.1 Start backend locally (or use Railway prod once Stage 11 deploys); test
  `GET /api/v1/centinela/alerts` with a valid client token (200, own-tenant data), without a token
  (staging fallback or 401 per `AUTH_ENFORCED`), and with an unresolved-tenant token (empty list).
- [ ] 6.2 Test `GET /api/v1/financials/liquidity-bridge` the same three ways.
- [ ] 6.3 Confirm `GET /centinela/alerts/{company_id}` (legacy) still returns its existing shape,
  unaffected.
- [ ] 6.4 Report:
  `openspec/changes/pwa-tenant-aware-screens/reports/2026-07-XX-step-6-curl-verification.md`.

## Stage 7. Frontend: data clients
- [x] 7.1 `lib/config.ts`: added `API_ENDPOINTS.centinelaAlerts`, `API_ENDPOINTS.liquidityBridge`.
  Commit `db4cdc6`, reviewed/approved.
- [x] 7.2 `lib/api-client.ts`: `CentinelaAlertsResponse`/`LiquidityBridgeSnapshot` types +
  `fetchCentinelaAlerts()`/`fetchLiquidityBridge()`, same `ApiError` handling as
  `fetchFinancials`. Shapes verified field-for-field against real backend responses.

## Stage 8. Frontend: ActiveAlerts becomes data-bound
- [x] 8.1 `components/pulso/ActiveAlerts.tsx`: `"use client"`, drop `alerts` prop, `useEffect` +
  `fetchCentinelaAlerts()`, loading skeleton / ready / (empty-or-error → render `null`, per spec).
  Commit `d8d6747`.
- [x] 8.2 `app/app/(shell)/overview/page.tsx`: renders `<ActiveAlerts />` with no props.
- [x] 8.3 `npx tsc --noEmit` clean.

## Stage 9. Frontend: MonthlyLiquidityBridgeCard becomes data-bound
- [x] 9.1 `components/flujo-detalle/MonthlyLiquidityBridgeCard.tsx`: `"use client"`, drop `bridge`
  prop, `useEffect` + `fetchLiquidityBridge()`, loading / ready (÷100 → `formatCop`) / unavailable
  states. Commit `095a771`.
- [x] 9.2 `app/flujo-detalle/page.tsx`: renders `<MonthlyLiquidityBridgeCard />` with no props
  (page itself stays a Server Component — only the card is client).
- [x] 9.3 `npx tsc --noEmit` clean.

## Stage 10. Frontend: CashTodayCard honesty fix
- [x] 10.1 `components/pulso/CashTodayCard.tsx`: replaced the `.catch` → `pulsoMock.cash` + `ready`
  fallback with an explicit `"error"` status branch and its own discrete render (spec
  `pulso-overview-live-data`, scenario "Error state renders honestly"). Commit `014b740`.
- [x] 10.2 `npx tsc --noEmit && npm run build` clean (full `contexia-app` build) — run by the
  leader after Stages 7-10 landed together, confirming the three concurrent changes compose
  cleanly (12 routes generated, no errors).

## Stage 11. Frontend: E2E with a real client (MANDATORY where applicable)
- [ ] 11.1 Local `npm run dev` against the deployed backend (post Stage-11-deploy) or a temporary
  staging pointer: verify all three states (loading/ready/empty-or-error) render for ActiveAlerts
  and the Liquidity Bridge without crashing the screen.
- [ ] 11.2 Confirm `CashTodayCard` no longer shows `$42.850.000` under any simulated error
  condition.

## Stage 12. Docs
- [ ] 12.1 `contexia-app/CLAUDE.md`: add `ActiveAlerts` and `MonthlyLiquidityBridgeCard` to
  "Pantallas data-bound"; add the hard rule "data-bound cards never fall back to mock data for
  authenticated users — error states must be honest" (citing the `CashTodayCard` fix as the
  precedent this closes).
- [ ] 12.2 `ARCHITECTURE.md` flujo-estrella section: note the two new endpoints if the diagram
  needs it (only if reviewer flags it as materially incomplete without them).

## Stage 13. Deploy to Production (MANDATORY — CLOSES THE LOOP)
See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`
Project-specific: deploy branch `main`; Frontend `https://contexia.online/app/overview` (+
`/app/flujo-detalle`); Backend `https://antigravity-app-production-175a.up.railway.app`.

- [ ] 13.1 `git branch --show-current` check, then merge `feature/pwa-tenant-aware-screens` → main
  (or open a PR per repo convention), push.
- [ ] 13.2 Apply migration `0033_*.sql` to Supabase (`kpynymwghfwshvcvevxq`) via Supabase MCP
  `apply_migration`; verify with a `SELECT` that SYNTH sale/expense rows are dated yesterday and
  the cron job (`cron.job` table) exists and is scheduled.
- [ ] 13.3 Bump `contexia-app/public/sw.js` `CACHE_VERSION` (`v14-2026-07-22` → next), then
  `cd contexia-app && npm run build`, sync `out/` → repo-root build artifact per the reconciliation
  procedure in `CLAUDE.md` §9 / the `2026-07-22-per-tenant-client-access` deployment report. Never
  hand-edit the artifact.
- [ ] 13.4 Vercel build green; Railway deploy active (confirm via `/api/v1/health` + deployment
  logs).
- [ ] 13.5 Production endpoint check: `GET /api/v1/centinela/alerts` and
  `GET /api/v1/financials/liquidity-bridge` return 200 with correct tenant/empty semantics.
- [ ] 13.6 **Real visual verification with a provisioned client login**: the founder logs in
  himself (Bitwarden credentials — Claude never types passwords into forms) and confirms: real
  Caja Real + real-or-honestly-empty alerts + real liquidity bridge, hard refresh Ctrl+F5;
  `ventas_ayer`/`gastos_ayer` non-zero again (reseed working).
- [ ] 13.7 Report: `openspec/changes/pwa-tenant-aware-screens/reports/2026-07-XX-deployment.md`.

## Stage 14. Close
- [ ] 14.1 `opsx:sync` the four delta specs into main `openspec/specs/`.
- [ ] 14.2 `opsx:archive` this change.
- [ ] 14.3 Update `feature_list.json`: mark `pwa-tenant-aware-screens` `done`, reconcile `active`
  with whatever the shared checkout's other parallel sessions have landed by then (check
  `git log main` for what merged first).
