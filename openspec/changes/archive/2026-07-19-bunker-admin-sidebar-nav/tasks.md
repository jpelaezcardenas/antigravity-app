## 1. Shared shell components

- [x] 1.1 Create `contexia-app/components/bunker/BunkerSidebar.tsx`: logo mark, "Admin CONTEXIA" header, 6 nav items (Dashboard, CRM/Ventas, Onboarding, Social Content Ops, Agentic OS, Configuración), active-item pill highlight, "POWERED BY CONTEXIA" footer — props: `activeSection`, `onSelect`, using existing `@theme` tokens only.
- [x] 1.2 Create `contexia-app/components/bunker/ComingSoonSection.tsx`: shared placeholder taking a `label` prop, rendered for Onboarding/Social Content Ops/Agentic OS/Configuración.

## 2. CRM/Ventas section (relocate existing content)

- [x] 2.1 Create `contexia-app/components/bunker/CrmVentasSection.tsx` and move the existing `clients` array + client-card grid + "Estadísticas del Bunker" block from `page.tsx` into it, unchanged in content.
- [x] 2.2 Verify CRM/Ventas renders all 5 existing clients and the stats block identically to the pre-change `/app/bunker` page.

## 3. Infrastructure Dashboard section

- [x] 3.1 Create `contexia-app/components/bunker/InfrastructureDashboard.tsx` with the 4 summary cards (monthly cloud spend, production services count, active AI layers, local agents) using existing tokens.
- [x] 3.2 Add per-service cards grouped by category (Cloud: Vercel/Railway/Supabase; AI: GLM/Groq/OpenRouter; Tools: Claude/GCP/Hermes) with status badge, metrics, and cost, per `specs/bunker-infrastructure-dashboard/spec.md`.
- [x] 3.3 Add cost breakdown visualization using native elements + tokens (no Chart.js, no CDN script, no new dependency).
- [x] 3.4 Add technical stack summary table (layer/technology/function/cost/status).
- [x] 3.5 Add alerts/pending-actions panel with danger/warning/ok severity styling.
- [x] 3.6 Confirm no network requests fire on Dashboard section render (all data inline/hardcoded).

## 4. Page composition

- [x] 4.1 Refactor `contexia-app/app/app/bunker/page.tsx` into a client component holding `activeSection` state, rendering `BunkerSidebar` + the section matching `activeSection` (Dashboard → `InfrastructureDashboard`, CRM/Ventas → `CrmVentasSection`, others → `ComingSoonSection`).
- [x] 4.2 Verify section switching updates content without full page reload/URL change, and the correct nav item shows the active-pill state, per `specs/bunker-admin-shell/spec.md`.
- [x] 4.3 (Discovered during implementation) Fix pre-existing double-shell bug: `/app/bunker` was nested inside `app/app/layout.tsx`, which wraps all pages under it in the PWA's `ClientTopBar`+`BottomNav`. Moved PWA-tab pages into a new `app/app/(shell)/` route group so `/app/bunker` no longer inherits that shell, with no change to any URL. See `design.md` decision 6.

## 5. Build and local verification

- [x] 5.1 `cd contexia-app && npm run build` — confirm the build is green with no type errors and no `ignoreBuildErrors` shortcuts used.
- [x] 5.2 Run the app locally (or via static preview of `contexia-app/out/`) and manually click through all 6 sidebar sections, confirming Dashboard, CRM/Ventas, and the 4 placeholders all render correctly with no console errors. Also re-verified `/app/overview` (PWA) still renders its shell correctly after the route-group restructure.
- [x] 5.3 Sync `contexia-app/out/` → `app/` (repo root) per the established build-artifact rule (`CLAUDE.md` §9) — do not hand-edit `app/bunker.html`. Bumped `sw.js` `CACHE_VERSION` (v5→v6) first since `_next/static/<buildId>/` changes per build. Synced additively (`git checkout` + copy) to avoid clobbering `app/config.html`'s unrelated chunk references — verified with a `grep`-based resolver that every `/_next/static/*` reference in every changed HTML file exists on disk, and restored an unrelated `.claude/launch.json` that was accidentally overwritten mid-sync.

## 6. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 6.1 `git add` the changed/new files under `contexia-app/` and the synced `app/` artifact; commit with a descriptive message. (commits `33a7cfa`, `3c59ee2`)
- [x] 6.2 Push to `main`. (`1a3b0a0..3c59ee2`)
- [x] 6.3 Confirm Vercel build completes green. (current production deployment, descendant of commits `33a7cfa`/`3c59ee2`/`ccbd64e`, is `READY`, aliased to `contexia.online`)
- [x] 6.4 Verify live at `https://contexia.online/app/bunker`: sidebar renders, all 6 sections navigable, Dashboard shows the infrastructure content, CRM/Ventas shows the existing client list unchanged. Hard refresh (Ctrl+F5) to bypass cache. (`curl` confirms 200, all 6 sidebar labels present, correct title — not `app-admin`'s)
- [x] 6.5 Create deployment report at `openspec/changes/bunker-admin-sidebar-nav/reports/YYYY-MM-DD-deployment.md`. (`reports/2026-07-19-deployment.md`, retroactive closure)

## 7. Archive

- [ ] 7.1 Run `openspec-archive-change` once Stage 11 is confirmed complete and verified live.
