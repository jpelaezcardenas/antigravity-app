## Why

The Búnker's "Social Content Ops" sidebar section (added in `bunker-admin-sidebar-nav`) is currently a "coming soon" placeholder, but a real, working implementation of this feature already exists: `frontend/dashboard/src/components/ops/SocialContentOps.tsx` (a separate, unlinked Vite/React admin app), wired to real backend endpoints already deployed on the canonical Railway backend (`apps/backend/presentation/social_ops_endpoints.py`), implementing the Tier 3 "Social Ops & Marketing" agents documented in `AGENTES.md` (Content Idea Generator, Lead Reply Drafter, Sales Closure Drafter, Metrics Analyzer). This work should not sit unreachable in an orphaned frontend — it should be the live content in the Búnker's Social Content Ops section, with all 9 of its tabs functional.

## What Changes

- Port `SocialContentOps.tsx` and its 5-tab structure (Inbox, Pipeline, Comandos, Aprobaciones, Integraciones) into `contexia-app/components/bunker/social-ops/`, calling the same real `/api/v1/social-ops/*` endpoints already live on the canonical Railway backend.
- Port "Ideas" (`IdeasOps.tsx`) as-is — already correctly calls the canonical `GET/POST /api/v1/social-ops/ideas*` endpoints (the real Content Idea Generator agent, LLM-powered).
- Port "Métricas" (`MetricasDashboard.tsx`) as-is — already correctly calls the canonical `GET /api/v1/social-ops/metrics` endpoint (the real Metrics Analyzer agent, Supabase-or-demo-fallback).
- **New backend work**: `CalendarioEditorial.tsx` and `BorradoresReview.tsx` currently query a stale, undocumented Supabase project (`wzqymuzpjbagnbgsiqig`, the Wizard's sandbox DB) directly via `lib/supabaseOps.ts`, with no equivalent in the canonical backend. Add 4 new canonical endpoints to `apps/backend/presentation/social_ops_endpoints.py` (`GET /social-ops/calendario`, `GET /social-ops/borradores`, `POST /social-ops/borradores/{id}/approve`, `POST /social-ops/borradores/{id}/update`), backed by `SocialOpsService` methods following the exact same Supabase-or-demo-fallback pattern already used for `ideas`/`metrics` — reading/writing the `calendario` and `contenido` tables on the **canonical** Supabase project, not the Wizard's.
- Port "Calendario Editorial" and "Borradores Review" into `contexia-app`, rewired to the new canonical endpoints instead of the old direct-Supabase pattern.
- Restyle everything from the old generic Tailwind classes (`bg-primary`, `text-obsidian`, `border-primary/30`, `text-ink`, `text-muted`, etc. — a different, unrelated design system) to this project's own `@theme` tokens, per `contexia-app/CLAUDE.md`'s hard rule against ad-hoc colors.
- Add `lib/social-ops-api.ts` (scoped to only the functions the 9 ported tabs use) to `contexia-app/lib/`, pointed at the same `API_BASE_URL` (`lib/config.ts`) already used by `CashTodayCard` — this becomes contexia-app's second data-bound exception to the mock-first rule, alongside Caja Real.

## Capabilities

### New Capabilities
- `bunker-social-content-ops`: real, backend-wired Social Content Ops surface under the Búnker's sidebar — Inbox, Pipeline, Comandos, Aprobaciones, Integraciones, Ideas, Métricas, Calendario, Borradores — each reading/writing the canonical `/api/v1/social-ops/*` endpoints, with the mandatory HITL approval flow intact.
- `social-ops-calendario-backend`: new canonical backend endpoints for the editorial calendar (`GET /social-ops/calendario`), replacing the ad-hoc Wizard-project query.
- `social-ops-borradores-backend`: new canonical backend endpoints for draft review/approval (`GET /social-ops/borradores`, `POST /borradores/{id}/approve`, `POST /borradores/{id}/update`), replacing the ad-hoc Wizard-project query.

### Modified Capabilities
(none — `bunker-admin-shell` already defines the "Social Content Ops" placeholder slot this change fills in; no requirement in that spec changes, only the placeholder's content)

## Impact

- New backend: 4 endpoints in `apps/backend/presentation/social_ops_endpoints.py`; corresponding methods (`list_calendario`, `list_borradores`, `approve_borrador`, `update_borrador`) plus demo-data seeding in `apps/backend/services/social_ops_service.py`; tests in `apps/backend/tests/test_social_ops_endpoints.py` and `test_social_ops_service.py` (TDD per `CLAUDE.md` §1).
- New frontend: `contexia-app/components/bunker/social-ops/SocialContentOpsSection.tsx` + one component per tab (9 total), `contexia-app/lib/social-ops-api.ts`.
- Modified: `contexia-app/app/app/bunker/page.tsx` — "Social Content Ops" section now renders `SocialContentOpsSection` instead of `ComingSoonSection`.
- Deploy: backend change needs Railway deploy (`-175a`) in addition to the usual Vercel frontend deploy — both covered under Stage 11.
