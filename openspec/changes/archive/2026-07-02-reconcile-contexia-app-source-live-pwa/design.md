## Context

The live client PWA UI exists only as a pre-built static export in `app/`. Its declared source, `contexia-app/`, renders placeholders for 4 of 5 screens (see CLAUDE.md §9 incident, 2026-06-29) and cannot reproduce the production UI. The live Caja Real is a hand-injected `<script>` in `app/overview.html` (`f91d9da`) plus a UTF-8 logout fix (`8559ca1`) — a documented, temporary exception to "never hand-edit `app/`". This is fragile: a routine rebuild+sync from `contexia-app/` overwrites the real UI and wipes live production data.

Two possible sources of the real UI must be reconciled: (a) the static `app/` export (git state `4433c5b^`), which HAS the full UI; and (b) the `contexia-app/` React source, which has the layout components and `CashTodayCard` but placeholder pages / a minimal `TopBar`+`BottomNav`. The goal is to make (b) produce (a) — with live data as a first-class component, not an injected script.

## Goals / Non-Goals

**Goals:**
- `npm run build` in `contexia-app/` + sync to `app/` reproduces the exact production UI (visual parity with the `app/` export at current `main`).
- Caja Real live data (`caja_real`, `dinero_disponible`, `ventas_ayer`, `gastos_ayer`) rendered by a data-bound component with loading/ready/empty/error states and graceful fallback (never the "No pudimos cargar" banner).
- Retire the hand-edit exception (remove the injected `<script>`; regenerate `app/`; update canon).

**Non-Goals:**
- Wiring Fiscal/Radar/Patrimonio/Flujo-detalle to live data (stay mock).
- Manual-data-ingestion UX for Hermes training (separate increment).
- Any backend / `/api/v1/financials` / CORS / Shadow GL change.
- Visual redesign — parity with the existing export is the bar.

## Decisions

**D1 — Port the real UI into `contexia-app/` source, don't keep hand-editing `app/`.**
The `app/` export is the visual source of truth for parity, but the React source becomes the buildable source of truth. Extract the header/nav (full Pulso/Fiscal/Radar/Patrimonio + Auditoría Sombra CTA + Taty card + Cerrar Sesión) and the real screen bodies from the `app/` export into `contexia-app/` components/pages. *Alternative rejected:* keep hand-editing `app/` forever — perpetuates the landmine and blocks any future frontend work.

**D2 — Caja Real via the existing `CashTodayCard` data-bound pattern, not an injected script.**
Reuse `lib/api-client.ts` `fetchFinancials()` + `lib/config.ts` (already point at Railway prod) and the `useEffect`-on-mount `"use client"` component with explicit states. Extend it to also populate `dinero_disponible`, `ventas_ayer`, `gastos_ayer`. *Alternative rejected:* keep the vanilla `<script>` — not typed, not testable, lost on rebuild.

**D3 — Parity is verified before the exception is removed.**
Do NOT delete the hand-edited `app/overview.html` script until a rebuilt `app/` is proven visually equivalent AND live-data-equivalent in a preview. Sequence: reconcile source → build → diff/inspect vs current `app/` → verify live fetch in preview → only then regenerate `app/` and drop the exception. *Alternative rejected:* remove the script first — would regress production if parity is imperfect.

**D4 — Graceful fallback semantics.**
On fetch failure the component shows a neutral state (skeleton or last-known/placeholder), never a red error. This matches the current script's fail-safe behavior and the `CashTodayCard` contract in `contexia-app/CLAUDE.md`.

## Risks / Trade-offs

- [Rebuild regresses the live client UI, as in the 2026-06-29 incident] → Mandatory visual verification (preview_* / browser) of every screen before deploy; parity diff against the current `app/`; Stage 11 gate.
- [`contexia-app/` source is missing pieces / `.gitignore` trap resurfaces] → Confirm full source is present (the `.gitignore` bug was fixed); if a component is missing, extract it from the `app/` export or git history — never fabricate a stub (CLAUDE.md §9 rule 1).
- [Live Caja Real breaks post-rebuild (CORS/hydration)] → Keep `API_BASE_URL` = Railway prod (no `.env.local`); verify `access-control-allow-origin` for `contexia.online`; verify the value renders in a real browser, not just a build.
- [Service worker serves stale shell] → Bump `CACHE_VERSION`; network-first navigation (already in `sw.js`).
- [Visual drift from the export] → Screenshot/inspect parity against the current production page as the acceptance bar; no redesign.

## Migration Plan

1. Reconcile `contexia-app/` source (header/nav + real screen bodies + data-bound Caja Real).
2. Build + sync to a scratch dir; diff/inspect vs current `app/`; verify live fetch in preview.
3. On parity: regenerate `app/`, remove the hand-edited script, bump `CACHE_VERSION`.
4. Update canon: retire the "hand-edit exception" note in CLAUDE.md §9 + ARCHITECTURE.md.
5. Stage 11: commit + push `main` → Vercel deploy → verify live Caja Real + all screens in production → deployment report.

**Rollback:** revert the merge commit; the current hand-edited `app/` (commit `cd5c095`) remains the known-good production state and is restorable via `git checkout <sha> -- app/`.

## Open Questions

- Does `contexia-app/`'s current `TopBar`/`BottomNav` get replaced wholesale by the export's landing-style header, or adapted? (Resolve by comparing both during implementation; parity with the export wins.)
- Are the non-Pulso screen bodies (Fiscal/Radar/Patrimonio) already faithfully in `contexia-app/`, or must they also be ported from the export to reach parity? (Audit per-screen at task time.)
