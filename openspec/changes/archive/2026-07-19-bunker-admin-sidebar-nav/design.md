## Context

`/app/bunker` (`contexia-app/app/app/bunker/page.tsx`) is today a single client component: header + a hardcoded `clients` array rendered as cards + a small stats block. No routing, no nav, no state beyond what's in the JSX. This is the internal admin surface, separate from the end-user PWA (`/app/overview` etc.) and outside the route group that has the PWA's TopBar/BottomNav shell (see `ARCHITECTURE.md`: "Búnker … panel interno-futuro (AI OS), no es el MVP").

The user supplied a reference screenshot of a sidebar (logo, "Admin CONTEXIA", 6 nav items, active-pill highlight, footer caption) from an unrelated project ("Social Media OPs Systems") as the visual target, and a separately-drafted static "Infrastructure Dashboard" mockup (raw HTML/inline-styled) as the content for the Dashboard section. Neither artifact is native to this codebase — the sidebar visual needs to be rebuilt with this project's own components/tokens, and the dashboard mockup's inline dark-theme styles must be re-expressed using `contexia-app`'s `@theme` Tailwind tokens (`bg-surface-elevated`, `text-primary-container`, etc.) per `contexia-app/CLAUDE.md`.

## Goals / Non-Goals

**Goals:**
- Give `/app/bunker` a persistent sidebar shell with 6 sections, client-side section switching (no new routes — single page, `useState`).
- Ship a static Infrastructure Dashboard under "Dashboard" reusing this project's existing design tokens only.
- Preserve the existing client-list content unchanged in substance, relocated under "CRM/Ventas".
- Give the 4 not-yet-built sections a real (not broken) placeholder state.

**Non-Goals:**
- No backend integration for infra metrics — all values in `InfrastructureDashboard` are hardcoded, matching the mock-first rule already governing every other `contexia-app` screen except `CashTodayCard`.
- No real functionality for Onboarding, Social Content Ops, Agentic OS, Configuración — placeholder only.
- No auth/access-control changes to `/app/bunker`.
- No charting library addition (the source mockup used Chart.js from a CDN, which `contexia-app/CLAUDE.md` explicitly forbids — "Sin CDN"). Cost breakdown is rendered as a token-styled bar/table, not a canvas chart.

## Decisions

1. **Single page + local state, not sub-routes.** `BunkerPage` becomes a client component holding `activeSection` state; each section is a sibling component conditionally rendered. Alternative considered: `/app/bunker/[section]` sub-routes — rejected because the reference UI behaves as an SPA-style shell (instant switch, no reload), and this repo's route groups are reserved for the PWA shell pattern.
2. **No Chart.js.** `contexia-app/CLAUDE.md` bans CDN scripts and new dependencies without strong reason. The cost breakdown becomes a simple horizontal bar list built from `<div>` widths + token colors — visually equivalent, zero new dependency.
3. **Tokens only, no inline hex styles.** The mockup's inline `style={{ background: '#161a24', ... }}` is translated to this project's existing `@theme` classes (`bg-surface-elevated`, `border-white/10`, `text-primary-container`, `text-status-success`, etc.) per `contexia-app/CLAUDE.md`'s hard rule against ad-hoc colors. Where a needed semantic color (e.g. warning/yellow) doesn't have an existing token, reuse the closest existing token rather than inventing a new one — flagged as an open question below if genuinely missing.
4. **Component boundaries**: `components/bunker/BunkerSidebar.tsx` (nav shell + active state prop), `components/bunker/InfrastructureDashboard.tsx` (Dashboard content), `components/bunker/CrmVentasSection.tsx` (existing client list, moved verbatim), `components/bunker/ComingSoonSection.tsx` (shared placeholder, takes a `label` prop for the 4 unbuilt sections). `page.tsx` becomes the composition root.
5. **Build path**: edit only under `contexia-app/`; run `npm run build`; sync `contexia-app/out/` → `app/` per the repo's established build-artifact rule (`CLAUDE.md` §9) — never hand-edit `app/bunker.html` directly.

6. **Route-group fix (discovered during implementation).** `/app/bunker` lived inside `contexia-app/app/app/`, a folder that is a real URL segment (not a route group) whose `layout.tsx` wraps every page under it in the PWA's `ClientTopBar` + `BottomNav` shell — so the Búnker was silently double-headered (PWA topbar above the Búnker's own header) in production, contradicting `ARCHITECTURE.md`'s framing of the Búnker as a separate internal-future surface, not a PWA tab. Fix: moved the PWA-tab pages (`fiscal`, `flujo-detalle`, `overview`, `patrimonio`, `radar`) and `layout.tsx` into a new `app/app/(shell)/` route group — route groups don't contribute a URL segment, so `/app/fiscal` etc. are unaffected — leaving `app/app/bunker/page.tsx` as a sibling outside `(shell)`, so `/app/bunker` no longer inherits the PWA shell. URL `/app/bunker` is unchanged; only the layout inheritance changed.

## Risks / Trade-offs

- [Reusing "coming soon" for 4 sections may look unfinished to a client demoing the Búnker] → Mitigation: this is an internal-only surface per `ARCHITECTURE.md` ("panel interno-futuro"), not customer-facing; acceptable for this change's scope.
- [Hardcoded dashboard numbers will drift from reality over time] → Mitigation: matches existing mock-first precedent for every other `contexia-app` screen; a future change can wire it to real provider APIs (out of scope here, matches user's own "próxima fase" note in the original mockup).
- [Static export (`next build` → `out/`) means no client-side dynamic segments] → Mitigation: single-page `useState` switching has no routing dependency, compatible with static export.

## Migration Plan

1. Build components under `contexia-app/components/bunker/`.
2. Refactor `contexia-app/app/app/bunker/page.tsx` to compose sidebar + sections.
3. `cd contexia-app && npm run build`.
4. Sync `contexia-app/out/` → `app/` (repo root), preserving `app/bunker.*` conventions per `CLAUDE.md` §9.
5. Commit, push to `main`, verify Vercel auto-deploy green, verify `https://contexia.online/app/bunker` live (Stage 11, `CLAUDE.md` §8).
6. Rollback: revert the commit on `main`; Vercel redeploys the prior build automatically.

## Open Questions

- None blocking — if a needed token color is missing during implementation, default to the closest existing semantic token (e.g. `text-status-success` for green, `text-on-surface-variant` for muted) rather than adding new ad-hoc hex values.
