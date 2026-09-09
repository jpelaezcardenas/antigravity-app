# Tasks — pricing-quote-engine

## Stage 0. Ground the design in the live schema

- [x] 0.1 Verify `b2b_clients` live columns against Supabase (confirm whether `monthly_fee_cents`
      already exists) and record the finding in `design.md`
- [x] 0.2 List `apps/backend/migrations/` and take the next genuinely free number (0033/0034
      collided once — ARCHITECTURE.md Decisión #15)
- [x] 0.3 Confirm `resolve_request_tenant_scope()` is the only tenant resolver to use
      (Decisión #17), and confirm revenue account codes from `financials_service`

## Stage 1. Migration (written, NOT applied)

- [x] 1.1 Write `0048_uvt_values_and_service_band.sql`: create `uvt_values` (`year` PK,
      `value_cop` bigint whole COP, `resolution` text, `created_at`), idempotent
- [x] 1.2 Seed UVT 2025 ($49.799, Res. 000193 de 2024) and UVT 2026 ($52.374, Res. 000238 del
      15-dic-2025) with `ON CONFLICT DO NOTHING`
- [x] 1.3 Add `b2b_clients.service_band` text + `CHECK (service_band IN
      ('micro','estandar','complejo'))`, nullable, idempotent
- [x] 1.4 Enable RLS on `uvt_values` with a read-only policy (it is public legal reference data,
      not tenant data) — never `USING (true)` for writes
- [x] 1.5 Add a schema test asserting the migration file declares the table, the seed rows, the
      CHECK constraint, and idempotency guards (mirrors `test_crm_b2b_schema.py`)
- [x] 1.6 **Do NOT apply to production.** Applying migrations requires the founder's explicit
      approval; the report must say the migration is pending

## Stage 2. UVT lookup service (TDD)

- [x] 2.1 Failing tests: `get_uvt_for_year` returns the 2025 value for 2025 and the 2026 value
      for 2026; raises `UvtNotFoundError` for an unseeded year; asserts no UVT constant exists
      in the module
- [x] 2.2 Implement `services/uvt_service.py` — reads `uvt_values`, no fallback constant
- [x] 2.3 Failing test + implementation for `cop_to_uvt()` conversion, asserting the whole-COP
      (not minor-unit) contract at the boundary

## Stage 3. Pre-quote engine service (TDD)

- [x] 3.1 Failing tests: annualised revenue from 4100/4105 credits over a trailing 12-month
      window; minor-units → whole COP conversion happens exactly once
- [x] 3.2 Failing tests: `movimientos_mes` averages the real `erp_journal_lines` count;
      `meses_observados` reports the real observed month count
- [x] 3.3 Failing test: fewer than 3 distinct months → `estado: "sin_historico_suficiente"`,
      `banda_sugerida: null`
- [x] 3.4 Failing tests: band heuristics (micro / estandar / complejo) at their UVT boundaries
- [x] 3.5 Failing tests: `confianza` is never `"alta"`; `micro` always yields `"baja"`;
      thin history yields `"baja"`
- [x] 3.6 Failing tests: `drivers_faltantes` always contains the payroll driver;
      `criterios_no_evaluables` always names the 4 unobservable quantitative criteria + IVA
- [x] 3.7 Failing test: tenant isolation — tenant A's pre-quote never reads tenant B's rows
- [x] 3.8 Implement `services/pricing_service.py` to make Stage 3 green

## Stage 4. HTTP surface (TDD)

- [x] 4.1 Failing tests: unauthenticated → 401; authenticated with unresolved tenant → 404
      (never Cliente Cero); resolved tenant → 200
- [x] 4.2 Failing test: the endpoint signature has no `tenant_id` query parameter
- [x] 4.3 Failing test: `anio_gravable` defaults to the previous calendar year and selects that
      year's UVT; an unseeded year returns `estado: "uvt_no_disponible"`
- [x] 4.4 Implement `presentation/pricing_endpoints.py` and mount at `/pricing` in
      `presentation/router.py`
- [x] 4.5 Failing test + assertion that the endpoint performs no writes (no approval_queue, no
      telemetry)

## Stage 5. Service band capture in the Búnker (TDD where testable)

- [x] 5.1 Failing tests: `CrmService.create_b2b_client` accepts and persists `service_band`;
      an invalid band raises `ValueError` (→ 400), not a Postgres CHECK violation
- [x] 5.2 Failing tests: a new `update_b2b_client_commercials` write path sets
      `monthly_fee_cents` and/or `service_band` on an existing client and rejects an invalid band
- [x] 5.3 Implement the service methods and the `PATCH /crm/b2b/clients/{id}/commercials`
      endpoint, mirroring the existing `/contact` write pattern
- [x] 5.4 Add `service_band` to `list_b2b_clients`'s projection so the roster returns it
- [x] 5.5 Frontend: extend `B2bClient` / `CreateB2bClientInput` types and add
      `updateB2bClientCommercials` in `lib/crm-api.ts`
- [x] 5.6 Frontend: add the band selector to the alta form and a "Honorario / Banda" column with
      inline editing in `B2bRetainersTab.tsx`, using the tab's existing write pattern
- [x] 5.7 `npx tsc --noEmit` clean

## Stage 6. Constraint compliance check

- [x] 6.1 Confirm `apps/backend/core/plan_features.py` is untouched by this change and excluded
      from its commit
- [x] 6.2 Confirm no test mocks the boundary it claims to verify (the rule
      `real-data-ingestion-mvp` left behind after two production bugs)
- [x] 6.3 Run the full backend test suite and compare failures against `main` to prove zero
      regressions

## Stage 7. Documentation

- [x] 7.1 Add the pre-quote endpoint and the `uvt_values` dependency to `ARCHITECTURE.md`
      (new settled decision, per CLAUDE.md §0's living-doc rule)
- [x] 7.2 Update `feature_list.json`'s active pointer

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main — **BLOCKED BY FOUNDER**: this change stops at a commit on a
      feature branch. `main` auto-deploys to Vercel and Railway; the push to production is the
      founder's call
- [ ] 11.2 Vercel build complete (green ✅) — blocked by 11.1
- [ ] 11.3 Railway deploy active (backend change) — blocked by 11.1
- [ ] 11.4 Production URL: changes visible and working — blocked by 11.1
- [x] 11.4b Apply migration `0048` to Supabase **BEFORE 11.1** — **DONE 2026-09-08**, applied
      with the founder's explicit approval and verified live (see
      `reports/2026-09-08-migration.md`). **Ordering is not cosmetic.** `CrmService.list_b2b_clients`
      now selects `service_band`, and its `except` branch falls back to demo data on any
      Supabase error — so deploying the code before applying the migration would make the
      Búnker's B2B roster silently show demo clients instead of the real ones. Apply the
      migration first, then push. `/pricing/pre-cotizacion` degrades safely either way
      (`estado: "uvt_no_disponible"`), and `service_band` writes fail loudly
- [ ] 11.5 Create report: `openspec/changes/pricing-quote-engine/reports/2026-09-08-deployment.md`
