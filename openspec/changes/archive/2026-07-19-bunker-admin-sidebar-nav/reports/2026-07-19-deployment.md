# Deployment Report — bunker-admin-sidebar-nav

**Date:** 2026-07-19 (retroactive closure — code has been live in production since 2026-07-15)

## What shipped

1. **Sidebar shell** for `/app/bunker`: logo + "Admin CONTEXIA" header, 6 nav items (Dashboard, CRM/Ventas, Onboarding, Social Content Ops, Agentic OS, Configuración), active-item pill highlight, "POWERED BY CONTEXIA" footer. Client-side section switching (`useState`, no route change).
2. **Infrastructure Dashboard** (Dashboard section): static cloud-consumption snapshot — summary cards, per-service cards (Vercel/Railway/Supabase/GLM/Groq/OpenRouter/Claude/GCP/Hermes), cost breakdown, stack table, alerts. Later enhanced with native SVG bar + donut charts (commit `7175044`, its own follow-up work, not re-reported here).
3. **CRM/Ventas**: existing client list relocated unchanged.
4. **Route-group fix** (discovered mid-implementation): `/app/bunker` was nested inside `app/app/layout.tsx`, which wraps every page in the PWA's `ClientTopBar`/`BottomNav` shell. Moved the PWA-tab pages into a new `app/app/(shell)/` route group so `/app/bunker` no longer inherits that shell — no URL changes.
5. **Routing bug fix** (discovered during verification): `vercel.json` rewrote `/app/bunker` to `/app/bunker/index.html`, a file format this Next.js version's static export no longer produces. That destination never resolved, so `/app/bunker` was silently falling through to the catch-all `/app/:path*` rule and serving `app-admin/index.html` (a separate, unrelated, auth-gated admin console) instead of the intended page. Fixed the rewrite to `/app/bunker.html`, matching the pattern already used for `/app/fiscal` etc.

## Commits

- `33a7cfa` — feat(bunker): add admin sidebar with Infrastructure Dashboard
- `3c59ee2` — chore(bunker): remove stale pre-route-group page copies
- `ccbd64e` — fix(bunker): repair stale rewrite so /app/bunker serves the real page

## Verification performed

- `npm run build` green, no type errors, no `ignoreBuildErrors` shortcuts.
- Local click-through of all 6 sidebar sections (Dashboard, CRM/Ventas, 4 placeholders) — correct content, no console errors. Re-verified `/app/overview` (PWA) still renders its own shell correctly after the route-group restructure (no regression).
- Production: `curl https://contexia.online/app/bunker` → 200, all 6 sidebar labels present (`Dashboard`, `CRM / Ventas`, `Onboarding`, `Social Content Ops`, `Agentic OS`, `Configuración`), title `Contexia — GPS Financiero` (confirms the Next.js page, not `app-admin`'s `Contexia · Bunker Admin`).
- Vercel: current production deployment (commit `4992da4`, descendant of all commits above) is `READY`, aliased to `contexia.online`.

## Known follow-ups (not in this change's scope)

- `login.html` (demo-credential login screen) and `middleware.ts`'s `ADMIN_ONLY` gate on `/app/bunker`/`/app-admin` remain untouched — explicitly paused by the user, tracked as a deferred item, not part of this change.
- Onboarding and Agentic OS sidebar sections were "coming soon" placeholders at the time of this change; Social Content Ops was ported to real data in the follow-up change `bunker-social-content-ops-port` (archived separately).
