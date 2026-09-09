# Tasks — pricing-catalog-and-operator-quote

## Stage 1. Price catalog (TDD)

- [x] 1.1 Failing tests: catalog covers exactly `plan_features.PLAN_FEATURES` keys (no missing,
      no extra) and exactly `pricing_service.SERVICE_BANDS`
- [x] 1.2 Failing tests: every software tier has a commercial name and either a `price_cents` or
      an explicit quoted marker; every band has `min_cents` and a nullable `max_cents`
- [x] 1.3 Failing test: every monetary identifier ends in `_cents` (no bare `price`)
- [x] 1.4 Failing test: the official amounts are exactly the founder's figures (GPS 249.000,
      Micro 890.000, Estándar 1.490.000–2.400.000), pinned so a silent edit fails
- [x] 1.5 Implement `apps/backend/core/pricing_catalog.py`

## Stage 2. Fee/band coherence (TDD)

- [x] 2.1 Failing tests: fee inside range → no warning; below min → warning; above max → warning
- [x] 2.2 Failing tests: open-ended band never warns on the upper bound; missing fee or missing
      band produces no warning
- [x] 2.3 Implement `check_fee_band_coherence()` in the catalog module
- [x] 2.4 Surface it in `CrmService.list_b2b_clients` output (additive field, never a rejection)

## Stage 3. Pre-quote reports the band's price (TDD)

- [x] 3.1 Failing test: an `ok` pre-quote includes the suggested band's min/max
- [x] 3.2 Failing test: `sin_historico_suficiente` and `uvt_no_disponible` report no price range
      (null, not zero)
- [x] 3.3 Implement in `pricing_service.compute_pre_quote` + `PreQuoteResponse`

## Stage 4. Operator route (TDD)

- [x] 4.1 Failing tests: operator scope → 200 scoped to the client's own tenant; single-tenant
      scope → 404; unresolved scope → 404; unauthenticated → 401
- [x] 4.2 Failing test: roster client with null `client_tenant_id` → explicit state, not 500
- [x] 4.3 Failing test: the self route still accepts no tenant/client parameter
- [x] 4.4 Implement `GET /pricing/pre-cotizacion/cliente/{b2b_client_id}`

## Stage 5. Búnker integration

- [x] 5.1 `lib/crm-api.ts`: types + `fetchClientPreQuote(clientId)`
- [x] 5.2 `B2bRetainersTab.tsx`: per-row "Pre-cotizar" action showing band, price range,
      confidence and missing drivers
- [x] 5.3 Render the coherence warning in the roster
- [x] 5.4 `npx tsc --noEmit` clean

## Stage 6. Documentation

- [x] 6.1 `docs/pricing.md` — English body per documentation-standards, bilingual founder summary
      (CLAUDE.md §2 carve-out), naming `core/pricing_catalog.py` as authoritative
- [x] 6.2 Cost-structure section: inference consolidating on owned local hardware, therefore not
      a per-client variable cost; no invented margin figure
- [x] 6.3 ARCHITECTURE.md settled decision for the catalog + operator route
- [x] 6.4 Flag the Taty-prompt implication for the founder (do not change the sales agent)

## Stage 7. Verification

- [x] 7.1 Full backend suite, compared against `main` for zero regressions
- [x] 7.2 Confirm `core/plan_features.py` untouched

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [x] 11.0 **Rebuild the static export and sync it** (`npm run build` in `contexia-app`,
      `out/app/*` → `app/`, rest → repo root, bump `sw.js` CACHE_VERSION). Not optional:
      `vercel.json` serves the repo root with no build step, so a source-only commit ships an
      invisible UI — the gap caught in the previous change
- [x] 11.1 git commit + push to main — DONE 2026-09-09, fast-forward `29bfdfa..821d693`
- [x] 11.2 Vercel: `contexia.online/app/bunker` → 200, `sw.js` at `v20-2026-09-09`, served chunk `11bepc041jvkm.js` verified to contain `Pre-cotizar`
- [x] 11.3 Railway deployment `d5925dd6-873c-43ed-a5ed-907d35dbb8e3` live, `/api/v1/health` 200
- [x] 11.4 `GET /api/v1/pricing/pre-cotizacion/cliente/x` → 401 (mounted, auth enforced); siblings unchanged
- [x] 11.5 Report: `openspec/changes/pricing-catalog-and-operator-quote/reports/2026-09-09-deployment.md`

**No migration in this change** — no schema change is required.
