## 1. Backend — Shared weekly aggregation helper

- [x] 1.1 Write a failing test for `_weekly_net_flux(tenant_id, week_start, week_end, supabase_client)` in `apps/backend/tests/test_radar_cash_projection.py`: given seeded `erp_journal_entries`/`erp_journal_lines` rows for one ISO week, asserts the correct net-flux minor-units value for that week and zero for a tenant with no rows in the window.
- [x] 1.2 Implement `_weekly_net_flux` in `services/radar_service.py`, extracted from the query shape already used by `calculate_cashflow_forecast` (single lookback-window fetch, bucketed by ISO week — not 13 separate round trips, per design.md Risk #2).
- [x] 1.3 Confirm the existing `/api/v1/radar/risk-score` tests still pass (no behavior change to `calculate_cashflow_forecast`). Ran `tests/test_radar.py` (1 passed, 8 skipped — RUN_SHADOW_GL not set) and `tests/test_radar_alert_count_tenant_scoping.py`; one pre-existing failure in the latter (`test_query_filters_by_company_id_and_tenant_id`) confirmed unrelated by reproducing it on a stash of this change's diff — out of scope here.

## 2. Backend — Projection service function

- [x] 2.1 Write a failing test asserting `calculate_cash_projection_13w(tenant_id)` returns exactly 13 weekly entries, each with `semana`, `fecha_inicio`, `caja_proyectada`, `confianza`, for a tenant seeded with 12 weeks of history.
- [x] 2.2 Write a failing test asserting weeks 1-4 are `confianza: "media"` and weeks 5-13 are `confianza: "baja"` (never `"alta"`).
- [x] 2.3 Write a failing test asserting a tenant with fewer than 4 weeks of `erp_journal_entries` history gets `estado: "sin_historico_suficiente"` and no `semanas` array.
- [x] 2.4 Write a failing test asserting `metodologia` is always `"solo_historico"` and `impuesto_futuro_estimado` is always `null`.
- [x] 2.5 Implement `calculate_cash_projection_13w(tenant_id, supabase_client=None)` in `services/radar_service.py` using `_weekly_net_flux`, projecting current Caja Real (account `1110`) forward week by week. Reused `financials_service._compute_caja_real_balance` for the starting balance (the exact cumulative-1110 calc, not a re-derivation) instead of a new balance query. Make the 4 tests above pass — all 4 green in `tests/test_radar_cash_projection.py`.

## 3. Backend — Tenant isolation test

- [x] 3.1 Write a failing test (mirroring `test_radar_alert_count_tenant_scoping.py`) seeding two tenants with different Shadow GL history and asserting Tenant A's projection never reflects Tenant B's rows.
- [x] 3.2 Confirm the test passes given the tenant-filtered queries from step 2.5 (no additional code expected if filtering is correct; fix if it fails) — passed once the mock fixture included the `id` field `_weekly_net_flux` needs; no production code change required, confirming `.eq("tenant_id", ...)` scoping was already correct.

## 4. Backend — Endpoint

- [x] 4.1 Write a failing test in `test_radar_cash_projection.py` asserting `GET /api/v1/radar/proyeccion-caja` requires authentication (401 without a token). Implemented as `test_endpoint_requires_get_current_user`, asserting the `user` param's default is `Depends(get_current_user)` — mirrors `test_agent_stub_endpoints_tenant.py`'s pattern (a real 401 is enforced by `get_current_user` itself, already covered by its own tests).
- [x] 4.2 Write a failing test asserting an authenticated caller with no resolvable tenant gets 200 with `estado: "tenant_no_resuelto"` and no `semanas` (never a Cliente Cero fallback) — corrected from the original 404 plan; see design.md Decision #2, this endpoint is read-only and follows `GET /centinela/alerts`'s precedent, not Approval Queue's write-route 404 policy.
- [x] 4.3 Write a failing test asserting an authenticated Cliente Cero caller gets a 200 with the full response shape (`client_tenant_id`, `generado_en`, `metodologia`, `semanas`/`estado`, `alerta_narrativa`).
- [x] 4.4 Implement `GET /api/v1/radar/proyeccion-caja` in `presentation/radar_endpoints.py`: `Depends(get_current_user)`, tenant resolved via `resolve_request_tenant_scope()` (no query-param tenant), calls `calculate_cash_projection_13w`. Make the 3 tests above pass. Also pulled in `generate_alerta_narrativa` (task 5.1) since the response shape needs it — done together, see 5.1 below.
- [ ] 4.5 Write a failing test asserting the endpoint responds in under 2 seconds for a tenant with 12 weeks of history; make it pass (optimize the query in step 1.2 if it fails).

## 5. Backend — Narrative copy

- [x] 5.1 Implement `alerta_narrativa` generation (plain Colombian-Spanish, `$X.XXX.XXX COP` formatting, no absolute-certainty language per design.md Risk #1) as a small pure function (`generate_alerta_narrativa` in `services/radar_service.py`). Dedicated unit tests added in `TestGenerateAlertaNarrativa` covering "bajando", "estable", and the honest no-history message — all green.

## 6. Frontend — Data-bound exception + tracking pattern (corrected — no new dependency)

- [x] 6.1 ~~Add `recharts`~~ Superseded: `contexia-app/CLAUDE.md` hard-bans new UI libraries without strong reason, and `components/radar/CashProjectionCard.tsx` already implements a 13-point-capable line chart as plain inline SVG (`viewBox="0 0 100 100"`, `path d="M.."`, `vectorEffect="non-scaling-stroke"`) — the exact technique task 7.2 will reuse. No package.json change, no install, no dependency added. See design.md Decision #6.
- [x] 6.2 Grep the existing `contexia-app/` codebase for the analytics/tracking pattern already used elsewhere — **finding: no such pattern exists.** No frontend event-tracking call, no analytics client, nothing in `lib/`; the closest thing (`metrics_snapshots` behind `MetricsDashboardSection`) is a nightly backend aggregation for the Búnker admin dashboard, not a per-screen-open event pipe. Building a new analytics pipeline here would itself be an unauthorized new dependency/infrastructure addition (same "no agregar dependencias sin razón fuerte" rule as 6.1). Task 7.3's tracking-event sub-item is descoped for this sprint as a result — see 7.3.
- [x] 6.3 Document `/app/radar`'s new cash-projection section as the 9th data-bound exception in `contexia-app/CLAUDE.md`'s "Pantallas data-bound" list (read-only, like `CashTodayCard`), and correct its "Radar... sigue siendo 100% mock" line in the `UpgradePlanBanner` section, which stops being fully true once this section reads live data. Done: hard-rules list updated, new "Radar → Radar de Caja 13 Semanas (novena excepción)" section added, `UpgradePlanBanner` paragraph corrected.

## 7. Frontend — Radar screen section

- [x] 7.1 Add a data-fetching hook/effect for `GET /api/v1/radar/proyeccion-caja` in the `/app/radar` route component, with explicit loading/ready/`sin_historico_suficiente`/`tenant_no_resuelto`/error states (mirroring `CashTodayCard`'s pattern per ARCHITECTURE.md §Caja Real wiring) — new component, additive alongside the existing mock `CashProjectionCard`/`EstimatedTaxProvisionCard`/etc., which stay as-is. Added `components/radar/CashProjection13wCard.tsx` + `fetchCashProjection13w()`/types in `lib/api-client.ts` + `radarCashProjection` in `lib/config.ts`.
- [x] 7.2 Build the 13-point line chart as plain inline SVG, reusing `CashProjectionCard`'s structure (grid lines, area gradient, `path d`, `vectorEffect="non-scaling-stroke"`) — normalize `caja_proyectada` values into a `viewBox="0 0 100 100"` path. Mobile-first. Two-color confidence coding via an SVG `linearGradient` with a hard stop at the media→baja boundary (media/baja only — never a third "alta" color, per design.md Decision #4).
- [x] 7.3 Render `alerta_narrativa` as a large text block below the chart. The adoption-tracking event from the original proposal is **descoped this sprint** (see 6.2 finding: no tracking infrastructure exists in `contexia-app` to hook into, and building one is out of scope for a single-screen addition) — the "≥40% weekly adoption" KPI from the idea doc will need its own future change once a tracking mechanism is chosen deliberately, not improvised here. Also added an honest methodology footnote (no CxC/CxP, no estimated future tax) so the UI never implies precision the model lacks.
- [x] 7.4 Render the honest empty states for `sin_historico_suficiente` and `tenant_no_resuelto`, with no chart and no invented numbers. Verified live in the browser preview: renders "Aún no tenemos suficiente historial para proyectar tu caja con confianza..." with no chart.
- [x] 7.5 Manually verify on a mobile viewport (or via the browser preview tool) that the chart and narrative are readable without horizontal scroll. Verified at 375x812: `tsc --noEmit` clean, `npm run build` green, chart renders with the teal→gray confidence split, "Hoy"/"En 13 semanas" figures, narrative and footnote all legible; no horizontal scroll; loading skeleton and error state also confirmed. Only console errors are `ERR_CONNECTION_REFUSED` from the other data-bound cards reaching for the Railway backend (expected with no local backend), none from this component.

## 8. Verification

- [x] 8.1 Run the full backend test suite — **no regressions, verified by A/B against a stash of this change's diff**: baseline (without this change) = 33 failed / 924 passed / 120 skipped; with this change = 33 failed / 938 passed / 120 skipped. The +14 are exactly this change's new tests; the 33 failures and 3 collection errors (`test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py` — they import `apps.backend.*`, which only resolves from the repo root) are all pre-existing and untouched by this change.
- [x] 8.2 Run `contexia-app` build (`npm run build`) and sync `out/` → `app/` per CLAUDE.md §9 — never hand-edit `app/`. Bumped `CACHE_VERSION` `v17-2026-08-15` → `v18-2026-09-04` first (mandatory per contexia-app/CLAUDE.md's service-worker rule). Synced with `robocopy /E` (copy, not mirror — matching the prior sync commit 897a2e7, which only added and never deleted). 33 files changed under `app/`; verified `app/app/radar.html` contains the new card and the built chunks reference `proyeccion-caja`.
- [ ] 8.3 Manually verify `/app/radar` against Cliente Cero data in a local/staging run before deploying. **Blocked locally** — needs the backend running against real Supabase credentials, unavailable in this session. Verified instead in the browser preview against injected fixtures matching the real response contract (ready / sin_historico_suficiente / error / loading all confirmed). Real Cliente Cero verification happens in Stage 11 against production (10.4).

## 9. Documentation

- [x] 9.1 Update `ARCHITECTURE.md` if this introduces a new architecturally-relevant flow (per CLAUDE.md §0 living-doc rule). Added a "Radar de Caja — proyección a 13 semanas" bullet to the Caja Real flow section documenting the endpoint, its reuse of `_compute_caja_real_balance`, the tenant-resolution divergence from the legacy `risk-score` route, and the four honesty constraints (`solo_historico`, `impuesto_futuro_estimado: null`, no `"alta"` band, honest empty state). `contexia-app/CLAUDE.md` was updated separately in 6.3.

## 10. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/radar
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 10.1 git commit + push to main
- [ ] 10.2 Vercel build complete (green ✅)
- [ ] 10.3 Railway deploy active (backend change — confirm health check passes)
- [ ] 10.4 Production URL: `/app/radar` shows the real chart + narrative for Cliente Cero, verified with hard refresh (Ctrl+F5)
- [ ] 10.5 Create report: `openspec/changes/radar-cash-projection-13w/reports/YYYY-MM-DD-deployment.md`

## 11. Archive

- [ ] 11.1 Confirm all tasks above are checked and Stage 11 report exists before archiving.
- [ ] 11.2 Run the archive step (`/opsx:archive` or equivalent) once deployment is verified in production — never archive with Stage 11 incomplete.
