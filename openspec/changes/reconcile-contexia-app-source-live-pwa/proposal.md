## Why

The end-user PWA that is live at `contexia.online/app/overview` (full client UI: Pulso/Fiscal/Radar/Patrimonio nav, Auditoría Sombra CTA, Taty card, and the **live Caja Real** from `GET /api/v1/financials`) currently exists ONLY as a pre-built static export in `app/`. Its declared source, `contexia-app/`, renders placeholders for 4 of 5 screens and **cannot reproduce this UI**. The live-data behavior survives only as a hand-injected `<script>` in `app/overview.html` (commits `f91d9da` / `8559ca1`) — a documented exception to the "never hand-edit `app/`" rule (CLAUDE.md §9). This is fragile: any routine `npm run build` + sync from `contexia-app/` would silently overwrite the real UI and wipe the live Caja Real in production. This change removes that landmine so Cliente Cero can be developed safely.

## What Changes

- Reconcile `contexia-app/` source so `npm run build` reproduces the **exact** live client UI: full top-nav (Pulso/Fiscal/Radar/Patrimonio), Auditoría Sombra CTA, Taty "Tu Amiga Contadora" card, correct "Cerrar Sesión" label, and all screen bodies currently only present in the `app/` export.
- Move the Caja Real live-data fetch from the hand-injected `<script>` into the component tree as a first-class data-bound render (extend the existing `CashTodayCard` pattern) — `ventas_ayer` / `gastos_ayer` / `dinero_disponible` included, fail-safe to a graceful state (never the "No pudimos cargar" error).
- Re-establish `app/` as a true build artifact: regenerate `app/` from the reconciled source and remove the hand-edit exception once parity is proven.
- **BREAKING (build process only):** after this change, `app/` MUST be regenerated from `contexia-app/`; the hand-edited `app/overview.html` script is retired.

## Capabilities

### New Capabilities
- `client-pwa-live-data`: The end-user PWA renders the full client UI and the live Caja Real (Pulso/Overview) reproducibly from `contexia-app/` source — a `npm run build` + sync yields the exact production UI with live data, with explicit loading/error/empty/ready states and mock fallback that never shows an error banner.

### Modified Capabilities
<!-- None: no existing spec's requirements change. -->

## Non-Goals

- NOT wiring Fiscal / Radar / Patrimonio / Flujo-detalle to live data (they stay mock this increment).
- NOT building the manual-data-ingestion UX for training Hermes (separate, later increment).
- NOT touching the backend `/api/v1/financials` contract, CORS config, or Shadow GL.
- NOT redesigning any screen — visual parity with the current `app/` export is the acceptance bar.

## Impact

- **Source:** `contexia-app/` (components/layout TopBar+nav, overview page, `CashTodayCard`, mocks, `lib/config.ts`, `lib/api-client.ts`).
- **Build artifact:** `app/` regenerated; `app/overview.html` hand-edit removed; `sw.js` `CACHE_VERSION` bump.
- **Canon:** on success, retire the "hand-edit exception" note in CLAUDE.md §9 + ARCHITECTURE.md.
- **Deploy:** Vercel (auto from `main`). Stage 11 must verify live Caja Real ($ from `/api/v1/financials`) still renders post-rebuild and no screen regressed.
- **Risk:** production PWA is client-facing and was already broken once by a bad rebuild (CLAUDE.md §9 incident) — visual verification before deploy is mandatory.
