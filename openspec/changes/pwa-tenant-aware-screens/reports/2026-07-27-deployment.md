# Deployment Report — pwa-tenant-aware-screens

- Date: 2026-07-27 / 2026-07-28 (UTC crossover during deploy)
- Deploy branch: `main`
- Commits merged: `db81263`..`e1472a8` (feature branch `feature/pwa-tenant-aware-screens`,
  fast-forward merged into `main`)

## Summary

Next wave of tenant-aware data-bound PWA screens: Pulso `ActiveAlerts` + Flujo-detalle
`MonthlyLiquidityBridgeCard`, two new tenant-scoped backend endpoints, a rolling reseed of
synthetic Shadow GL "yesterday" dates, and a fix for `CashTodayCard` silently masking fetch
errors with mock data.

## Mid-implementation reconciliation (worth flagging explicitly)

`origin/main` moved substantially while this change was implemented on an isolated git worktree
— 5 sibling tenant-scoping changes landed, including `agent-endpoints-real-tenant-filtering`,
which established `core/tenant_context.py::resolve_request_tenant_scope()` as the single
canonical tenant resolver and explicitly deprecated a second-resolver pattern. Before merging,
this branch was reconciled onto that canonical resolver (`centinela_endpoints.py`'s new route),
kept a private local resolver in `financials_endpoints.py` (never in scope for that
consolidation), and renumbered its migration `0033` → `0035` (collision with two sibling
changes' own `0033`/`0034`). Full detail: `tasks.md` Stage 13.0, `design.md` D1,
`progress/review_stage13_reconciliation.md` (APPROVED).

## Stage 11.1-11.2 — Live E2E verification (before merge)

Ran the real `contexia-app` frontend against a real local backend in the isolated worktree.
Confirmed all three cards render correct live data (Caja Real, 20 real Centinela alerts,
Liquidity Bridge), and confirmed honest degradation (no crash, no mock fallback) when the
backend was stopped: `CashTodayCard` → "No pudimos actualizar tu Caja Real...", `ActiveAlerts` →
section disappears, `MonthlyLiquidityBridgeCard` → "Datos no disponibles por el momento." Found
and fixed a real React duplicate-key bug (`ActiveAlerts`, commit `89c7774`) — many live alerts
share one `rule_id`.

## Stage 13.2 — Migration 0035 applied

Applied `apps/backend/migrations/0035_rolling_reseed_synthetic_shadow_gl.sql` to Supabase
project `kpynymwghfwshvcvevxq` via Supabase MCP `apply_migration`. Verified:
- All 19 `SYNTH-*-SALE`/`SYNTH-*-EXPENSE` rows re-dated from `2026-07-20` (stale) to
  `2026-07-27` (= `CURRENT_DATE - 1`).
- `cron.job` table shows `reseed-synth-shadow-gl` active, schedule `10 5 * * *` (UTC, ~00:10
  Bogotá).

## Stage 13.3 — Build artifact synced

Investigated the repo-root build-artifact mapping carefully before syncing (past incident
precedent, `CLAUDE.md` §9): `vercel.json`'s `outputDirectory: "."` + rewrites confirmed
`_next/`, `sw.js`, `manifest.webmanifest`, `icons/`, `flujo-detalle*`, `crear-empresa-wizard*`
live at the **repo root** (not under `app/`) — only the route pages (`app/overview.html` etc.)
go under `app/`. Bumped `CACHE_VERSION` `v14-2026-07-22` → `v15-2026-07-27` in
`contexia-app/public/sw.js`, ran `npm run build`, synced `out/` → repo root with a
copy-overwrite-only operation (no deletion) — confirmed `app-admin/`, `.antigravity/`, the
wizard, and `assets/`'s non-contexia-app content (`css/theme.css`, wizard bundle) were left
untouched. Grepped the new `_next/static/chunks/*.js` for `fetchCentinelaAlerts`/
`fetchLiquidityBridge` before committing to confirm the right code actually landed. Commit
`270a859`.

## Stage 13.1 — Merged and pushed to main

`git push origin feature/pwa-tenant-aware-screens:main` — fast-forward, `9c180b7..db81263`, then
a second push after Stage 13.2/13.3's commits — `db81263..e1472a8`.

## Stage 13.4-13.5 — Deploy verification

**Railway** (`elegant-success` / `antigravity-app`, the sole canonical backend per
ARCHITECTURE.md Decision #9): deployment `58228003-65d2-4722-bdd9-3c66111e23d3` — `SUCCESS`.
`GET /api/v1/health` on `antigravity-app-production-175a.up.railway.app` — `200 healthy`.

**Vercel** (`contexia-web-app`): deployment `dpl_FYm4vdg7C34x7UsGTpq6V9jJryf1` — `READY`,
`target: production`, `githubCommitSha` matches `e1472a8` (this change's final commit).

**Production endpoint check** (Railway direct + through the `contexia.online` Vercel proxy):
- `GET /api/v1/centinela/alerts`, `GET /api/v1/financials/liquidity-bridge`, and the legacy
  `GET /centinela/alerts/{company_id}` all return `401 {"detail":"Invalid or missing
  authentication token"}` with no token — correct (`AUTH_ENFORCED=True` in production, unlike
  local dev's permissive staging fallback). A clean `401` (not `404`/`500`) confirms the routes
  are correctly mounted and reachable, not crashed or missing.
- `contexia.online/sw.js` — confirmed serving `CACHE_VERSION = "v15-2026-07-27"`.
- `contexia.online/app/overview.html` — `200`, references the new `_next/static/chunks/*.js`
  bundle; sampled one such chunk directly — `200`, reachable.
- `contexia.online/api/v1/health` (through the Vercel → Railway proxy rewrite) — `200 healthy`.

## Stage 13.6 — FOUNDER ACTION REQUIRED (not yet executed)

Following the established precedent from every prior tenant-scoping change this session
(`taty-per-tenant-profiles`, `approval-queue-tenant-scoping`, `centinela-tenant-scoped-alerts`,
`agent-endpoints-real-tenant-filtering`): this agent does not handle plaintext credentials and
did not attempt to log in as a real client. **Founder action needed:**

1. Log in at `contexia.online` as a real provisioned B2B client (Bitwarden credentials).
2. Hard refresh (Ctrl+F5) `/app/overview` and confirm: real Caja Real (not `$42.850.000`), real
   Alertas Activas (or the section correctly absent if the tenant has none), `ventas_ayer`/
   `gastos_ayer` non-zero (confirms the migration 0035 reseed is visible end-to-end).
3. Navigate to `/app/flujo-detalle` and confirm the Puente de Liquidez card shows real, non-mock
   figures.
4. Confirm no fetch errors/console errors during normal navigation.

## Outcome

- Stage 13 status: backend + frontend deployed and verified at the infrastructure/endpoint
  level. Founder's real-client visual confirmation (13.6) is the only remaining item before
  Stage 14 (close/archive).
- Blocking issues: none identified. No regressions found in the 5 sibling changes' code (full
  backend suite: 694 passed / 40 pre-existing-unrelated failures, unchanged before and after
  reconciliation).
