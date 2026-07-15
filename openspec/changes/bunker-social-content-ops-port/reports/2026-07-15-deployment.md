# Deployment Report — bunker-social-content-ops-port

**Date:** 2026-07-15

## What shipped

1. **Backend** (`apps/backend`, Railway `-175a`):
   - New endpoints: `GET /social-ops/calendario?semana=<int>`, `GET /social-ops/borradores`, `POST /social-ops/borradores/{id}/approve`, `POST /social-ops/borradores/{id}/update` — same Supabase-preferred/demo-fallback pattern as the existing `ideas`/`metrics` endpoints, on the canonical Supabase project.
   - TDD: 10 new tests (`test_social_ops_service.py`, `test_social_ops_endpoints.py`), 21/21 social-ops tests green. Full suite: 40 pre-existing failures in unrelated subsystems (Shadow GL/Siigo CSV, wizard auditoría sombra) — none touch social_ops.
   - **`SOCIAL_OPS_CANONICAL` flipped to `true`** on Railway `-175a` (confirmed with user first — this is a production cutover, replacing n8n as the Social Ops handler, not just adding endpoints).

2. **Frontend** (`contexia-app`, Vercel):
   - Búnker's "Social Content Ops" sidebar section: from "coming soon" placeholder to a fully functional 9-tab surface (Inbox, Pipeline, Comandos, Aprobaciones, Integraciones, Ideas, Calendario, Borradores, Métricas).
   - Ported from `frontend/dashboard/src/components/ops/` (an old, unlinked Vite dashboard) and rewired to the real, canonical `/api/v1/social-ops/*` backend.
   - New: `lib/social-ops-api.ts` (contexia-app's second data-bound exception, alongside `CashTodayCard`), `components/bunker/social-ops/*` (5 components).
   - Documented in `contexia-app/CLAUDE.md`'s "Pantallas data-bound" section per the living-doc rule.

## Commits

- `123cdc7` — backend: Calendario/Borradores endpoints (TDD)
- `8126f79` — frontend: Social Content Ops wired to real backend
- `c39db80` — docs: CLAUDE.md data-bound section update

## Verification performed

- Backend: `curl` against production confirmed `SOCIAL_OPS_CANONICAL=true` mounted the router — all 9 endpoints return 200 (previously 404). `calendario` connected to canonical Supabase (`"source":"supabase"`, table exists, currently 0 rows).
- Frontend: `npm run build` green, no type errors. Verified locally against the live Railway backend (temporarily pointed `.env.development.local` at production, reverted after) — all 9 tabs render real data: 3 real seeded inbox leads with diagnostics, pipeline kanban across real stages (Auditoría Sombra, Formalización), 1 real pending HITL approval (Aprobar/Rechazar functional), Calendario/Borradores/Métricas correctly show empty states (real canonical tables currently have 0 rows — expected, not a bug). No console errors throughout.
- Production: deployment `dpl_3rRSTKY24BHKtFUfnUg9KynYjMcs` READY, aliased to `contexia.online`. Confirmed live via `curl` (200) and `WebFetch` (sidebar shows all 6 items including Social Content Ops, Dashboard renders by default).

## Known follow-ups (not in this change's scope)

- Calendario/Borradores tables are empty on the canonical Supabase project — no data migration was attempted from the old Wizard-project tables (per `design.md` non-goals, that data was undocumented/possibly stale).
- Onboarding and Agentic OS sidebar sections remain "coming soon" placeholders — `OnboardingOps.tsx`/`AgenticOpsView.tsx` exist in the same old Vite dashboard with their own backend wiring, but were out of scope for this change (user asked specifically about Social Content Ops).
- Calendario Editorial / Borradores Review's *legacy* implementation (querying the Wizard's Supabase project directly) remains dead code in `frontend/dashboard/` — not deleted, just unused; that whole directory was already unlinked from any deployed route before this change.
