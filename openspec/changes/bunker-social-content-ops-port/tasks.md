## 1. Backend — Calendario endpoint (TDD)

- [ ] 1.1 Write failing tests in `apps/backend/tests/test_social_ops_service.py`: `list_calendario()` returns demo-fallback items when Supabase unset; `list_calendario(semana=2)` filters correctly.
- [ ] 1.2 Write failing tests in `apps/backend/tests/test_social_ops_endpoints.py`: `GET /social-ops/calendario` returns 200 with `items`; `GET /social-ops/calendario?semana=2` filters.
- [ ] 1.3 Add `self.calendario: List[Dict[str, Any]] = []` to `SocialOpsService.reset_memory()`, seed 3-4 illustrative entries in `_seed_demo()` matching the `Calendario` shape (id, semana, fecha_publicacion, dia_semana, idea_id, pilar, formato, titulo_trabajo, status, responsable, notas_editoriales, created_at).
- [ ] 1.4 Implement `list_calendario(semana: Optional[int] = None) -> Dict[str, Any]` in `SocialOpsService`, following the exact Supabase-preferred/demo-fallback pattern of `list_ideas()`.
- [ ] 1.5 Add `GET /social-ops/calendario` route in `apps/backend/presentation/social_ops_endpoints.py` accepting optional `semana` query param.
- [ ] 1.6 Run `pytest apps/backend/tests/test_social_ops_service.py apps/backend/tests/test_social_ops_endpoints.py` — all green.

## 2. Backend — Borradores endpoints (TDD)

- [ ] 2.1 Write failing tests: `list_borradores()` returns only `BORRADOR_IA`/`EDITADO_HUMANO` items (demo-fallback); `approve_borrador(id)` sets status `APROBADO` + `fecha_aprobacion` + `aprobado_por`, raises `KeyError` for unknown id; `update_borrador(id, updates)` applies partial update and sets `status=EDITADO_HUMANO`.
- [ ] 2.2 Write failing endpoint tests: `GET /social-ops/borradores`, `POST /social-ops/borradores/{id}/approve` (200 + 404 cases), `POST /social-ops/borradores/{id}/update`.
- [ ] 2.3 Add `self.contenido: Dict[int, Dict[str, Any]] = {}` to `reset_memory()`, seed 2-3 illustrative drafts in `_seed_demo()` matching the `Contenido` shape (id, cal_id, hook, hook_alt_1, hook_alt_2, copy_body, cta, hashtags, version, status, qa_humanizacion, created_at).
- [ ] 2.4 Implement `list_borradores()`, `approve_borrador(id, actor)`, `update_borrador(id, updates)` in `SocialOpsService`, same pattern.
- [ ] 2.5 Add `GET /social-ops/borradores`, `POST /social-ops/borradores/{id}/approve`, `POST /social-ops/borradores/{id}/update` routes.
- [ ] 2.6 Run `pytest apps/backend/tests/test_social_ops_service.py apps/backend/tests/test_social_ops_endpoints.py` — all green.

## 3. Backend deploy

- [ ] 3.1 Commit backend changes, push to `main`.
- [ ] 3.2 Confirm Railway (`-175a`) deploy completes and is healthy.
- [ ] 3.3 Flip `SOCIAL_OPS_CANONICAL=true` on Railway `-175a` (confirmed with user — see `design.md` decision 7: this replaces n8n as the Social Ops handler in production, not just adding endpoints).
- [ ] 3.4 `curl` all 7 existing `/social-ops/*` endpoints (inbox, pipeline, integrations, approvals, ideas, metrics + the 4 new calendario/borradores ones) against the live Railway URL — confirm 200 responses with expected shapes, none still 404.

## 4. Frontend — API client and shared pieces

- [ ] 4.1 Create `contexia-app/lib/social-ops-api.ts`: port types + fetch functions for the 9 tabs from `frontend/dashboard/src/lib/socialOpsApi.ts` (inbox, pipeline, integrations, diagnose, simulate event, parse command, lead reply/sales drafts, approvals, ideas, metrics) plus the 4 new calendario/borradores functions, using `API_BASE_URL` from `contexia-app/lib/config.ts`.

## 5. Frontend — Social Content Ops section (7 already-live tabs)

- [ ] 5.1 Create `contexia-app/components/bunker/social-ops/SocialContentOpsSection.tsx`: header/summary stats + Inbox/Pipeline/Comandos/Aprobaciones/Integraciones tabs, ported from `SocialContentOps.tsx`, tokens translated per `design.md` decision 5.
- [ ] 5.2 Create `contexia-app/components/bunker/social-ops/IdeasTab.tsx`, ported from `IdeasOps.tsx`, calling `social-ops-api.ts`.
- [ ] 5.3 Create `contexia-app/components/bunker/social-ops/MetricasTab.tsx`, ported from `MetricasDashboard.tsx`, calling `social-ops-api.ts`.

## 6. Frontend — Calendario and Borradores tabs (newly backed)

- [ ] 6.1 Create `contexia-app/components/bunker/social-ops/CalendarioTab.tsx`, ported from `CalendarioEditorial.tsx`, rewired from `lib/supabaseOps.ts` to `social-ops-api.ts`'s new `getCalendario(semana?)`.
- [ ] 6.2 Create `contexia-app/components/bunker/social-ops/BorradoresTab.tsx`, ported from `BorradoresReview.tsx`, rewired to `social-ops-api.ts`'s new `getBorradores()`/`approveBorrador(id)`/`updateBorrador(id, updates)`.

## 7. Wiring and local verification

- [ ] 7.1 Update `contexia-app/app/app/bunker/page.tsx`: "Social Content Ops" case renders `SocialContentOpsSection` (with its 4 legacy sub-tab buttons: Ideas/Calendario/Borradores/Métricas) instead of `ComingSoonSection`.
- [ ] 7.2 `cd contexia-app && npm run build` — green, no type errors.
- [ ] 7.3 Run locally, click through all 9 tabs against the live Railway backend (already deployed per Section 3): confirm real data loads, no console errors, HITL approve/reject actually calls the approvals endpoint.
- [ ] 7.4 Update `contexia-app/CLAUDE.md`'s "Pantallas data-bound" section to document Social Content Ops as the second data-bound exception, per design.md decision 1 and the repo's living-doc rule.

## 8. Frontend deploy

- [ ] 8.1 Sync `contexia-app/out/` → `app/` (bump `sw.js` `CACHE_VERSION`).
- [ ] 8.2 Commit, push to `main`.
- [ ] 8.3 Confirm Vercel build green.
- [ ] 8.4 Verify live at `https://contexia.online/app/bunker` → Social Content Ops: all 9 tabs functional against production backend. Hard refresh to bypass cache.
- [ ] 8.5 Create deployment report at `openspec/changes/bunker-social-content-ops-port/reports/YYYY-MM-DD-deployment.md`.

## 9. Archive

- [ ] 9.1 Run `openspec-archive-change` once Stage 11 is confirmed complete and verified live.
