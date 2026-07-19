## Context

`frontend/dashboard/src/components/ops/` is a separate, unlinked Vite + React admin dashboard, never wired to any deployed route. It contains a real Social Content Ops implementation (`SocialContentOps.tsx`, 685 lines, 5 tabs) plus 4 "legacy" sub-tabs. Of those 9 tabs, 7 already call real, live, canonical backend endpoints (`apps/backend/presentation/social_ops_endpoints.py` on Railway `-175a`); 2 (Calendario Editorial, Borradores Review) instead query a stale, undocumented Supabase project belonging to the Wizard product (`wzqymuzpjbagnbgsiqig`) via `lib/supabaseOps.ts`, with a hardcoded anon key.

`AGENTES.md` documents 4 "Tier 3: Social Ops & Marketing" agents (Content Idea Generator, Lead Reply Drafter, Sales Closure Drafter, Metrics Analyzer) — all 4 already implemented in `apps/backend/services/social_ops_service.py` using the shared `agents/llm_engine.py` for AI generation, mandatory HITL gating (drafts land in `pending_approval`, nothing outbound fires without explicit approval via the Approval Queue). Calendario/Borradores are extensions of the same Ideas→Drafts→Metrics pipeline `AGENTES.md` calls out as "preservado" (Regla 5) — they're the missing middle of that pipeline (an idea becomes a calendar entry, which produces a draft in `contenido`, which gets reviewed/approved in Borradores, which becomes a `publicacion`, which accrues `metricas`). Adding the 2 missing endpoints completes a pipeline that's already 90% built, rather than inventing a new one.

`contexia-app/CLAUDE.md` establishes one existing precedent for real backend calls from an otherwise mock-first codebase: `CashTodayCard` (`lib/api-client.ts` + `lib/config.ts`) — fetch on mount, explicit loading/ready/empty/error states, graceful fallback. This change follows the same pattern for a second, larger surface.

## Goals / Non-Goals

**Goals:**
- Make all 9 Social Content Ops tabs real and functioning in the Búnker, backed by the actual deployed/extended agents.
- Complete the Ideas→Calendario→Borradores→Métricas pipeline on the canonical Supabase project, replacing the ad-hoc Wizard-project queries.
- Reuse existing backend patterns exactly (Supabase-or-demo-fallback, same service class, same router file) rather than introducing a new backend module.
- Match `contexia-app`'s design tokens throughout.
- Preserve HITL approval semantics exactly.

**Non-Goals:**
- Not touching the old `frontend/dashboard/` Vite app — it stays as-is, unlinked; only read as a porting reference.
- Not migrating any data out of the Wizard's Supabase project — the new canonical endpoints start from demo-fallback data (matching the existing `ideas`/`metrics` pattern) rather than attempting a data migration from an undocumented, possibly-stale source.
- Not building the Insights table/endpoint (`fetchInsights` in the old `supabaseOps.ts`) — nothing in the 9 ported tabs reads it directly; out of scope unless a specific need surfaces.
- Not adding new LLM-generation logic beyond what `generate_idea_draft` already does — Calendario/Borradores are CRUD + status-transition endpoints, not new AI agents.

## Decisions

1. **New backend endpoints extend the existing `SocialOpsService` class and router file**, not a new module — `calendario`/`contenido` are natural extensions of the same domain (`ideas` → `calendario` → `contenido` → `publicaciones` → `metricas`), and `metrics`/`ideas` already set the exact pattern to follow (`self.<table>` in-memory dict/list in `reset_memory()`, seeded via `_seed_demo()`, Supabase-preferred-with-fallback in the read method, same fallback in write methods).
2. **Endpoint shapes**, matching the existing router's style (all mutations are `POST`, matching `ideas/{id}/status`, `metrics/simulate`):
   - `GET /social-ops/calendario?semana=<int|omitted>` → `{"source": "supabase"|"demo_fallback", "items": Calendario[]}`
   - `GET /social-ops/borradores` → `{"source": ..., "items": Contenido[]}` (filtered to `status IN (BORRADOR_IA, EDITADO_HUMANO)`, matching the old Wizard-side filter)
   - `POST /social-ops/borradores/{id}/approve` → sets `status=APROBADO`, `fecha_aprobacion=<today>`, `aprobado_por=<actor from request>`
   - `POST /social-ops/borradores/{id}/update` → partial update of `hook`/`hook_alt_1`/`hook_alt_2`/`copy_body`/`cta`/`hashtags`/`status` (mirrors old `updateContenido`)
3. **Demo-fallback seed data** for `calendario`/`contenido` mirrors the shape already used for `ideas` (2-3 illustrative rows in `_seed_demo()`), so the tabs render meaningfully even when Supabase env vars aren't set locally — same UX as Ideas/Métricas today.
4. **Frontend component structure**: `contexia-app/components/bunker/social-ops/SocialContentOpsSection.tsx` (composition root + the 5 "new" tabs), `IdeasTab.tsx`, `MetricasTab.tsx`, `CalendarioTab.tsx`, `BorradoresTab.tsx` as siblings — 4 sub-tab buttons preserved exactly as in the original (Ideas/Calendario/Borradores/Métricas).
5. **Token translation**, same approach as `InfrastructureDashboard`: old classes (`bg-primary`, `text-obsidian`, `text-ink`, `text-muted`, `border-outline/40`, `bg-slate-950/60`, rose/amber/emerald/violet/blue severity maps) map to `contexia-app`'s `@theme` tokens (`bg-primary-container`/`text-on-primary`/`text-on-surface`/`text-on-surface-variant`/`border-outline-variant`/`bg-surface-container`, `status-critical`/`status-warning`/`status-success`/`secondary`/`primary`). No new ad-hoc hex values.
6. **TDD for the new backend endpoints** per `CLAUDE.md` §1: write failing tests in `apps/backend/tests/test_social_ops_service.py` (service methods) and `test_social_ops_endpoints.py` (HTTP layer) before implementing, following the existing test file's structure for `list_ideas`/`get_metrics_dashboard`.

7. **`SOCIAL_OPS_CANONICAL` feature flag must be flipped to `true` on Railway `-175a`.** Verified empirically: `GET /api/v1/financials` returns 200 (backend healthy) but `GET /api/v1/social-ops/ideas` returns 404 — the social-ops router is not mounted at all (`presentation/router.py` includes it only `if settings.SOCIAL_OPS_CANONICAL`). Per the archived `2026-06-24-agentic-performance-management-phase4` deployment report, this flag's default-off state means **n8n remains the active Social Ops handler in production**; flipping it to `true` **replaces** n8n with the FastAPI implementation — this is a real production cutover, not just "turning on new endpoints," and was previously explicitly deferred (Task 4.7). Confirmed with the user before proceeding — flipping is in scope for this change (see tasks.md §3).

## Risks / Trade-offs

- [New backend endpoints could theoretically write to the canonical Supabase project's `calendario`/`contenido` tables if `SUPABASE_URL`/`SUPABASE_KEY` are set but those tables don't exist yet] → Mitigation: matches the exact same risk profile already accepted for `ideas`/`metrics` (which have the identical try/except-log-and-fallback pattern); if the tables are missing, the `except Exception` branch logs a warning and falls back to demo data — never a hard failure.
- [Reusing generic `SUPABASE_URL`/`SUPABASE_KEY` env names could be ambiguous about which Supabase project they point to] → Not a new risk introduced here — same env vars `ideas`/`metrics` already use; this change doesn't touch backend Supabase configuration, only extends usage of the existing client.
- [Two data-bound exceptions (Caja Real + Social Ops) erode `contexia-app`'s mock-first simplicity] → Mitigation: documented explicitly in `contexia-app/CLAUDE.md`, both follow the identical fetch-on-mount-with-fallback pattern.
- [`lib/social-ops-api.ts` calls a production backend directly from the browser] → Mitigation: same Railway backend + `ALLOWED_ORIGINS` config already serving `CashTodayCard`'s calls from the same origin; no new CORS surface.
- [Flipping `SOCIAL_OPS_CANONICAL=true` stops n8n from handling Social Ops in production; if n8n workflows have any in-flight state or scheduled jobs specific to Social Ops, they lose their handler] → Mitigation: confirmed explicitly with the user before flipping (see decision 7); the FastAPI implementation covers the same 7-tab surface (inbox, pipeline, commands, approvals, integrations, ideas, metrics) per `AGENTES.md`'s Tier 3 catalog, so this is a like-for-like handler swap, not a capability loss.

## Migration Plan

1. Backend: write failing tests for `list_calendario`/`list_borradores`/`approve_borrador`/`update_borrador`, then implement the service methods + demo seed data + router endpoints. Run `pytest apps/backend/tests/test_social_ops_*.py` green.
2. Commit + push backend change to `main` → Railway auto-deploys `-175a`. Verify the 4 new endpoints respond (`curl` against the live Railway URL).
3. Frontend: add `contexia-app/lib/social-ops-api.ts`, build `SocialContentOpsSection.tsx` + 4 sub-tab components under `contexia-app/components/bunker/social-ops/`.
4. Wire `contexia-app/app/app/bunker/page.tsx`'s "Social Content Ops" case to the new section.
5. `npm run build`, verify locally against the now-live Railway endpoints (all 9 tabs load, no console errors, empty/error states render sanely).
6. Sync `contexia-app/out/` → `app/`, commit, push `main`, verify Vercel green, verify live at `https://contexia.online/app/bunker` (Stage 11).
7. Rollback: revert the frontend commit for a UI-only rollback; revert the backend commit separately if the new endpoints misbehave in production — the two are independently revertable since the frontend tolerates a 404 from missing endpoints via its existing error state.

## Open Questions

- None blocking.
