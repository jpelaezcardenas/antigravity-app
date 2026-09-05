## Context

`/app/radar` today renders a static mock. A sibling endpoint,
`GET /api/v1/radar/risk-score`, already exists (`presentation/radar_endpoints.py` +
`services/radar_service.py`) and computes a 30-day linear cashflow forecast from
`erp_journal_entries`/`erp_journal_lines` net flux, plus a deterministic 0-100 risk score.
It takes `tenant_id` as a query parameter — a pre-Decision-#17 pattern that the rest of the
agent HTTP surface (`ARCHITECTURE.md` Decision #17) has since moved away from in favor of
`core/tenant_context.py::resolve_request_tenant_scope()` resolving the tenant from the
authenticated caller. This change must follow the current pattern, not the older one it
sits next to.

There are no accounts-receivable/payable tables with due dates in the schema
(`dian_xml_documents` has `issue_date` only, no `due_date`; no CxC/CxP table exists). There
is no tax-forecast calculation anywhere in the backend. Both are hard data-model
constraints, not implementation choices — they set the ceiling on what this endpoint can
honestly claim.

## Goals / Non-Goals

**Goals:**
- A 13-week cash projection endpoint, tenant-scoped via the current standard resolver.
- Weekly aggregation of the same Shadow GL data already used for the 30-day forecast,
  extended to a longer, week-bucketed horizon.
- Explicit, non-overstated confidence and methodology fields so the UI never implies
  precision the model doesn't have.
- A real (not mocked) chart + narrative on `/app/radar` for Cliente Cero.

**Non-Goals:**
- Building CxC/CxP data model or ingestion — out of scope; `metodologia` field exists
  precisely to make this gap visible to the user and to future sessions.
- Computing "Impuesto Futuro Estimado" — no backend calculation exists; this endpoint must
  not synthesize one.
- Any write path to `approval_queue` or any other actionable draft — this is strictly
  read/projection (Nous Never Approves).
- Refactoring or replacing the existing `/api/v1/radar/risk-score` endpoint.

## Decisions

1. **New function in `services/radar_service.py`, not a new service file.**
   `calculate_cashflow_forecast` already contains the exact Shadow GL query shape
   (`erp_journal_entries` → `erp_journal_lines`, `dian_xml_documents`, tenant-filtered,
   date-windowed) this endpoint needs, just for a single 30-day window instead of 13 weekly
   buckets. Extracting a shared `_weekly_net_flux(tenant_id, week_start, week_end)` helper
   and calling it 13 times (or once with a grouped query) avoids duplicating the
   ORM-shaped Supabase query logic. Alternative considered: a standalone
   `radar_cash_projection_service.py` — rejected, since it would fork the Shadow GL access
   pattern into two slightly different implementations that drift over time.

2. **Tenant resolution via `resolve_request_tenant_scope()`, endpoint requires
   `Depends(get_current_user)`.** This matches Decision #17 (single tenant-resolution
   contract for the agent HTTP surface) and explicitly diverges from the older
   `risk-score` endpoint's `tenant_id: str = Query(...)` pattern, which predates that
   decision and is not to be copied forward. **Correction during implementation**: the
   original proposal.md/specs draft said an unresolved tenant should return 404, copying
   the anti-enumeration policy verbatim from Decision #17 — but that policy is scoped to
   write/ownership-check routes (`approval_queue_endpoints.py`'s enqueue/approve/reject).
   `GET /centinela/alerts` — the actual precedent for a read-only per-tenant feed — returns
   200 with a graceful empty body when the tenant doesn't resolve, never 404. This endpoint
   follows that read-only precedent: 200 with `estado: "tenant_no_resuelto"` and no
   `semanas`, never a Cliente-Cero fallback for an authenticated caller.

3. **`metodologia: "solo_historico"` is a static value for this version, not computed.**
   Since no CxC/CxP tables exist, there is only one code path. The field is still explicit
   in the response schema (rather than omitted) so the door is open for a future
   `historico_mas_cxc_cxp` value without a breaking response-shape change.

4. **Confidence bands: weeks 1-4 `"media"`, weeks 5-13 `"baja"`. No `"alta"` band exists in
   this version.** The original idea sketch proposed `"alta"` for weeks 1-4, but that
   presumes CxC/CxP grounding this endpoint doesn't have. Claiming "alta" confidence from
   trend extrapolation alone would misrepresent the model to a PyME owner making real
   decisions — rejected for both honesty and consistency with the KPI ("error medio < 15%
   en las primeras 2 semanas" only makes sense to validate against a confidence band that
   isn't already overstating itself).

5. **Insufficient-history threshold: fewer than 4 weeks of `erp_journal_entries` for the
   tenant → `estado: "sin_historico_suficiente"`, no `semanas` array.** 4 weeks (not 8) is
   chosen as the hard floor because it's the minimum needed to compute even one weekly
   net-flux data point with any trend signal; 8 weeks remains the target for a "media"
   confidence read, reflected in the weekly bucket count feeding the trend, not the gate
   itself.

6. **Correction during implementation: plain inline SVG, not Recharts.**
   `contexia-app/CLAUDE.md` has a hard rule — "No agregar dependencias sin razón fuerte (no
   librerías de UI)" — and the existing `components/radar/CashProjectionCard.tsx` (the
   30-day mock projection card already on this screen) proves the pattern already in use
   for exactly this kind of chart: a plain `<svg><path d="M0,40 L20,55 ...">` with
   `preserveAspectRatio="none"` and a `viewBox="0 0 100 100"`, no library at all. Adding
   Recharts here would violate a standing rule for a chart this simple, when the repo
   already has a working, established technique one component away. The 13-point line is
   built the same way: normalize each week's `caja_proyectada` into a `viewBox="0 0 100
   100"` path string, reusing `CashProjectionCard`'s SVG structure (grid lines, area
   gradient, `vectorEffect="non-scaling-stroke"`) rather than introducing a new dependency.

7. **Radar becomes a 9th data-bound exception in `contexia-app/CLAUDE.md`.** That file
   currently lists 8 named data-bound exceptions to its "sin backend, sin fetch" rule, and
   explicitly calls Radar "100% mock" in the `UpgradePlanBanner` section. Wiring the new
   endpoint into `/app/radar` is squarely what this OpenSpec change was asked to do, but
   the living-doc rule (`contexia-app/CLAUDE.md` itself, mirroring the root `CLAUDE.md`
   §0 pattern for `ARCHITECTURE.md`) requires documenting a new data-bound screen in the
   same change that introduces it — not silently drifting the doc out of sync with reality
   the way `app/`-as-build-artifact once did (CLAUDE.md §9 incident). This is a
   documentation correction, not a scope change: it makes the doc match what was already
   approved.

8. **The endpoint needs its own PWA-facing router at `/radar`, mounted separately from
   the agent router.** Found only after the first production deploy answered **404** for
   the documented path: `presentation/router.py` mounts `radar_endpoints.router` at
   `/agents/radar-predictivo`, so the new route landed at
   `/api/v1/agents/radar-predictivo/proyeccion-caja`, not `/api/v1/radar/proyeccion-caja`.
   The repo consistently splits the agent-internal surface (`/agents/centinela`,
   `/agents/pulso-diario`, `/agents/radar-predictivo`) from the clean per-tenant paths the
   PWA reads (`/financials`, `/centinela`, `/tenant`) — `centinela_endpoints.py` vs
   `centinela_agents_endpoints.py` is the exact precedent, and `jarvis_endpoints.py`
   (`webhook_router` + `api_router`) is the precedent for exporting two routers from one
   module. Fix: `radar_endpoints.py` now also exports `pwa_router`, carrying only
   `/proyeccion-caja`, mounted at `/radar`. The legacy `/risk-score` route stays exactly
   where it was.

   **Why the tests missed it:** every endpoint test called `get_cash_projection()` as a
   plain async function (the `test_agent_stub_endpoints_tenant.py` pattern), which passes
   regardless of where — or whether — the router is mounted. `TestRouteRegistration` was
   added to pin the actual mounted path against `presentation.router.api_router`, and it
   reproduces the 404 when the mount is wrong.

## Risks / Trade-offs

- **[Risk] A tenant with volatile week-to-week net flux gets a projection that looks
  confident but swings wildly.** → Mitigation: confidence is capped at "media" and the
  narrative copy must avoid absolute language ("vas a tener exactamente X"); this is a
  copy-review gate in `tasks.md`, not just a data concern.
- **[Risk] Reusing `erp_journal_entries`/`lines` queries per-week (13 iterations) could
  exceed the 2s budget for tenants with a long history.** → Mitigation: fetch the full
  8-12 week lookback window in one query, bucket in Python/SQL by ISO week rather than
  issuing 13 separate round trips; add a timing assertion in the test suite.
  entries/lines
- **[Risk] Copying the query pattern from `calculate_cashflow_forecast` without extracting
  a shared helper would duplicate tenant-filtering logic that later needs a fix in two
  places.** → Mitigation: Decision #1 above — extract the shared weekly-aggregation helper
  before writing endpoint-specific code.
- **[Trade-off] `solo_historico` methodology means the projection is a naive trend
  extrapolation, not a real forecast with known commitments.** Accepted for this sprint;
  the honest `metodologia` field and capped confidence exist specifically so the product
  doesn't overpromise while the data model gap remains open.

## Migration Plan

No data migration. Deploy is additive: new backend route + new frontend section, both
behind existing auth. Rollback is a plain revert (no schema change, no feature flag
needed) — Railway/Vercel redeploy of the previous commit removes the route and reverts
`/app/radar` to its prior state.

## Open Questions

- What tracking mechanism does the rest of the PWA use for adoption events today (to reuse
  rather than invent a new one for `radar_cash_projection_opened`)? To be confirmed during
  implementation by grepping the frontend for the existing pattern before adding this
  event.
