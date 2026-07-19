## Why

The Búnker (`/app/bunker`) is currently a single flat page showing only a client list. Juan David needs a persistent admin sidebar with dedicated sections — starting with an Infrastructure Consumption Dashboard (cloud spend across Vercel/Railway/Supabase/GLM/Groq/OpenRouter/Claude/GCP/Hermes) — as the foundation for the Búnker's future role as an internal AI OS surface (per `ARCHITECTURE.md`: "Búnker … panel interno-futuro (AI OS)"). Today there is no way to see infra cost/consumption without manually checking each provider dashboard.

## What Changes

- Add a persistent left sidebar to `/app/bunker`: logo + "Admin CONTEXIA" header, 6 nav items (Dashboard, CRM/Ventas, Onboarding, Social Content Ops, Agentic OS, Configuración), active-item highlight, "POWERED BY CONTEXIA" footer.
- Add client-side tab state so switching sidebar items swaps the main content area without a route change (single page, `useState`-driven section).
- New `InfrastructureDashboard` component under **Dashboard**: static/hardcoded snapshot (summary cards, per-service cards, cost breakdown, stack table, alerts) built with this project's existing `@theme` Tailwind tokens — no new hardcoded color palette.
- Existing client list + stats (today the entire `BunkerPage` body) move under **CRM/Ventas**, unchanged in content.
- **Onboarding**, **Social Content Ops**, **Agentic OS**, **Configuración** render a shared "coming soon" placeholder — no functionality yet.
- No backend calls, no persistence, no auth changes — pure static/mock content, consistent with `contexia-app/CLAUDE.md`'s mock-first rules.

## Capabilities

### New Capabilities
- `bunker-admin-shell`: sidebar navigation shell for `/app/bunker` with section switching and placeholder states for not-yet-built sections.
- `bunker-infrastructure-dashboard`: static infrastructure/cost consumption dashboard rendered under the Búnker's Dashboard section.

### Modified Capabilities
(none — no existing `openspec/specs/` capability governs `/app/bunker` today)

## Impact

- `contexia-app/app/app/bunker/page.tsx` — restructured into a sidebar shell; existing client-list JSX relocated into a CRM/Ventas section component, not deleted.
- `contexia-app/app/app/fiscal/`, `flujo-detalle/`, `overview/`, `patrimonio/`, `radar/`, `layout.tsx` — moved into new route group `contexia-app/app/app/(shell)/` to stop the Búnker from inheriting the PWA's TopBar/BottomNav shell (pre-existing bug found during implementation, see `design.md` decision 6). No URL changes for any of these routes.
- New: `contexia-app/components/bunker/BunkerSidebar.tsx`, `contexia-app/components/bunker/InfrastructureDashboard.tsx`, `contexia-app/components/bunker/ComingSoon.tsx`, `contexia-app/components/bunker/CrmVentasSection.tsx` (exact filenames TBD in design).
- Build/deploy: `contexia-app/` → `npm run build` → sync to `app/` (repo root) → commit → push `main` → Vercel auto-deploy → verify `https://contexia.online/app/bunker`.
- No backend, database, or API impact.
