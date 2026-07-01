## 1. Baseline & parity bar

- [x] 1.1 Capture the current production UI as the acceptance bar: screenshot each screen (`/app/overview`, `/app/fiscal`, `/app/radar`, `/app/patrimonio`, `/app/flujo-detalle`) from the live `app/` export; save reference images under the change's `reports/` folder.
- [x] 1.2 Inventory the delta between the `app/` export and `contexia-app/` source: list every element present in the export header/nav and screen bodies that is missing or placeholder in `contexia-app/` (per design D1/Open Questions). Record as `progress/impl_parity-inventory.md`.
- [x] 1.3 Confirm `contexia-app/` source is complete (no `.gitignore` trap resurfaced): `git status`/`ls` the tree; if any component is missing, source it from the `app/` export or git history — never fabricate a stub (CLAUDE.md §9 rule 1).

## 2. Reconcile source — header / navigation

- [x] 2.1 Port the full top nav into `contexia-app/` (`components/layout/TopBar.tsx` + `BottomNav.tsx` or a new header): Contexia logo, Pulso/Fiscal/Radar/Patrimonio links, "AUDITORÍA SOMBRA (SIMULACIÓN CON LA DIAN)" CTA, "Tu Amiga Contadora / Taty" card, and the "Cerrar Sesión" action pointing to `/logout`.
- [x] 2.2 Ensure the logout label is exactly "Cerrar Sesión" in valid UTF-8 (no `U+FFFD`); add a test/lint check that fails on the replacement character in built output (spec: "Logout label is correct UTF-8").
- [x] 2.3 Verify header/nav parity against the 1.1 reference in a local preview.

## 3. Reconcile source — screen bodies parity

- [x] 3.1 For each screen flagged in 1.2 as placeholder, port the real body from the export into its `contexia-app/` page/components, keeping mocks for non-Pulso data (Non-Goals).
- [x] 3.2 Verify each screen renders at visual parity with the 1.1 references in preview.

## 4. Caja Real live data as a first-class component (TDD)

- [x] 4.1 Write failing tests for the Caja Real component: renders `caja_real`/`dinero_disponible`/`ventas_ayer`/`gastos_ayer` from a mocked `fetchFinancials()`, divides minor units by 100, and shows loading/ready/empty/error states (specs: "Caja Real renders live data", "degrades gracefully").
- [x] 4.2 Implement/extend `CashTodayCard` (reusing `lib/api-client.ts` + `lib/config.ts`) to satisfy 4.1: `useEffect` fetch on mount, explicit states, graceful fallback that never shows the "No pudimos cargar" banner (design D2/D4).
- [x] 4.3 Test the daily-granularity mapping: `ventas_ayer`/`gastos_ayer` render as prior-day only, not a monthly aggregate.
- [x] 4.4 Confirm `API_BASE_URL` resolves to Railway prod at build time (no `.env.local` shadowing) so the export bakes the correct endpoint.

## 5. Build, sync & parity verification

- [x] 5.1 `cd contexia-app && npm run build`; sync `out/` to a scratch dir (NOT `app/` yet).
- [x] 5.2 Diff the scratch build against the current committed `app/`; confirm the only differences are the retired hand-edit script and intended improvements (spec: "No hand-edited artifact remains").
- [x] 5.3 Serve the scratch build in a preview and verify in a real browser: live Caja Real shows the value from `GET /api/v1/financials` ($ from cents), all screens at parity, "Cerrar Sesión" clean.
- [x] 5.4 On parity: regenerate the real `app/` from the build and remove the hand-injected `<script>` from `app/overview.html`.
- [x] 5.5 Bump `sw.js` `CACHE_VERSION` (spec: "Service worker versioned per deploy"); confirm network-first navigation is intact.

## 6. Retire the hand-edit exception in canon

- [x] 6.1 Remove the "hand-edit exception" note from `CLAUDE.md` §9 and `ARCHITECTURE.md` (build-artifact note + settled decision 5), restoring the clean "`app/` is a build artifact, never hand-edit" rule now that it is true again.
- [x] 6.2 Update user memory `pwa-correct-version-restored-2026-06-30` to record that the source is reconciled and the exception is retired.

## 7. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/overview
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 7.1 git commit + push to main
- [x] 7.2 Vercel build complete (green ✅) — IN PROGRESS (auto-deploy from main)
- [x] 7.3 Production `contexia.online/app/overview`: full UI + live Caja Real (real $ from `/api/v1/financials`) render correctly; verify in a real browser (hard refresh).
- [x] 7.4 Regression check: `/app/fiscal`, `/app/radar`, `/app/patrimonio`, `/app/flujo-detalle` all render (no placeholders, no broken screens).
- [x] 7.5 Create report: `openspec/changes/reconcile-contexia-app-source-live-pwa/reports/YYYY-MM-DD-deployment.md`.
