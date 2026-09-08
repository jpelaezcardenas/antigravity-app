# pricing-quote-engine — implementation report (2026-09-08)

**Status:** implemented, tested, committed on branch `feat/pricing-quote-engine`.
**NOT pushed. NOT deployed. Migration NOT applied.** Both are the founder's call.

---

## What shipped

### 1. `uvt_values` table — the UVT stops being a constant

`apps/backend/migrations/0048_uvt_values_and_service_band.sql` (written, **not applied**).

`year` PK · `value_cop` bigint in **whole pesos** · `resolution` text · `created_at`. Seeded
with UVT 2025 ($49.799, Res. DIAN 000193 de 2024) and UVT 2026 ($52.374, Res. DIAN 000238 del
15-dic-2025), `ON CONFLICT DO NOTHING`.

`apps/backend/services/uvt_service.py` reads it. `get_uvt_for_year(year)` takes the tax year as
a **required** parameter — there is no "current UVT" concept, because in law there isn't one:
during 2026 the 2025 UVT governs año-gravable-2025 obligation thresholds while the 2026 UVT
governs 2026 sanctions and withholding. A year with no row raises `UvtNotFoundError`; nothing
falls back. A test reads the module's own source and fails if either figure is ever hardcoded.

RLS: reads open (public legal reference data), writes service-role only — two policies, not one
permissive `FOR ALL USING (true)`.

### 2. `b2b_clients.service_band` — where the agreed band lives

**Correction to the handoff's premise, verified live:** `b2b_clients` already had
`monthly_fee_cents` (bigint, nullable) since migration 0020 — confirmed both in the migration
file and by querying `information_schema.columns` against Supabase `kpynymwghfwshvcvevxq`. The
handoff described the table as having "`name`, `status`, `notes` and nothing more". So the real
gap was the **band**, not the amount, and the migration adds only `service_band`
(`micro|estandar|complejo`, CHECK, nullable, no default).

What that changed in scope: instead of adding a column that existed, I made the *existing* fee
editable after alta. Before this, `monthly_fee_cents` could only be set at creation time — there
was no write path to correct it later, which made the column nearly unusable in practice.

- `CrmService.create_b2b_client(..., service_band=...)` — validated in the service layer, so an
  invalid band is a 400 naming the allowed values, not a raw Postgres CHECK violation.
- New `CrmService.update_b2b_client_commercials()` + `PATCH /crm/b2b/clients/{id}/commercials`,
  mirroring the existing `/contact` write pattern. Omitting a field leaves it untouched; an
  empty-string band clears it to NULL.
- `list_b2b_clients` now projects `service_band` and `plan_tier`.
- Búnker: band selector in the alta form, plus a "Honorario / Banda" column with inline fee
  editing and a per-row band dropdown in `B2bRetainersTab.tsx`.

`SERVICE_BANDS` is defined once in `services/pricing_service.py` and imported by `CrmService`,
so the engine that suggests a band and the code that stores one cannot drift apart.

### 3. `GET /api/v1/pricing/pre-cotizacion`

New `services/pricing_service.py` + `presentation/pricing_endpoints.py`, mounted at `/pricing`.

Returns `ingresos_anualizados_cop` / `_uvt`, `movimientos_mes`, `meses_observados`,
`supera_umbral_declarante`, `umbral_declarante_uvt|_cop`, `banda_sugerida`, `confianza`,
`drivers_faltantes`, `criterio_evaluado`, `criterios_no_evaluables`, `uvt_cop`,
`uvt_resolucion`, `estado`.

---

## Decisions I made

| Decision | Why |
|---|---|
| `value_cop` in **whole pesos**, one `// 100` conversion in `_annualised_revenue_cop` | The UVT is published in whole pesos. Storing it in minor units for symmetry with the Shadow GL invites a 100× error in the dangerous direction — a threshold 100× too high marks everyone a non-declarant. |
| New `/pricing` router, not `/crm` | `crm_router` is CRM_CANONICAL-flag-gated and scoped to Cliente Cero's operator roster — the wrong tenant semantics for an endpoint that must resolve the *caller's own* tenant. |
| Default `anio_gravable` = previous calendar year | That is the año gravable currently being assessed, and it correctly selects UVT 2025 for those thresholds. Overridable via query param. |
| `supera_umbral_declarante` reports **one** criterion, and says so in-band | Only gross revenue is observable. `false` would otherwise read as "not obligated to file", which is not what was measured. `criterio_evaluado` + `criterios_no_evaluables` carry the asymmetry in the payload, following the Radar precedent. |
| Band thresholds anchored in **UVT**, not pesos | Peso constants rot with the UVT. `MICRO_MAX_UVT` = the 1.400 UVT filing threshold; `COMPLEJO_MIN_UVT` = 5.000 UVT; volume thresholds 20 / 200 monthly lines. All named module constants. |
| `micro` is **always** `confianza: "baja"` | Micro is defined as "minimal movement **without labour load**". The absence of payroll is precisely what cannot be observed, so a micro suggestion is the least grounded output the engine can produce. |
| Minimum 3 distinct months of history | Annualising one month ×12 is fabrication with a decimal point. Below the minimum: `estado: "sin_historico_suficiente"`, `banda_sugerida: null`. |
| `isinstance(anio_gravable, int)` rather than `is not None` | A **real bug the tests caught**: called directly (not through a FastAPI request), the parameter defaults to the `Query(...)` sentinel object, which `is not None` passes straight through as the tax year. The clean `Annotated` fix is unusable — FastAPI 0.104.1 mishandles Annotated query params against the installed Pydantic 2.x (`'FieldInfo' object has no attribute 'in_'`). |
| `tfoot` `colSpan` 4 → 6 | Pre-existing off-by-one (5 leading columns, `colSpan={4}`) that adding a 6th column forced me to recompute. Now correct. |

---

## Constraints honoured

- ✅ **`core/plan_features.py` untouched.** It carries uncommitted changes from the separate
  `hermes-jarvis-contexia` effort (`jarvis_chat` / `jarvis_voice`); those are **excluded from
  this commit**, along with `TenantInfoCard.tsx` and `UpgradePlanBanner.tsx`, which belong to
  the same unrelated work.
- ✅ **Tenant resolved only via `resolve_request_tenant_scope()`.** No tenant query param — a
  test asserts no parameter name contains "tenant". Unresolved tenant → **404**, never Cliente
  Cero.
- ✅ **Migration number taken from a real directory listing.** Highest existing is `0047`; `0048`
  is free. A test asserts nothing else claims `0048_*`.
- ✅ **Migration written, not applied.**
- ✅ **No test mocks the boundary it verifies.** The Supabase client and the tenant resolver are
  stubbed (collaborators behind the code); the annualisation, unit conversion, banding,
  confidence, UVT-year selection and validation logic all execute for real. The endpoint tests
  that assert tax-year behaviour deliberately do **not** fake `compute_pre_quote`.
- ✅ **Stage 11 present in `tasks.md`** per CLAUDE.md §8.

---

## Tests

| Suite | Result |
|---|---|
| `test_uvt_service.py` | 11 passed |
| `test_pricing_service.py` | 25 passed |
| `test_pricing_endpoint.py` | 12 passed |
| `test_uvt_values_migration.py` | 18 passed |
| `test_crm_service_service_band.py` | 11 passed |
| `test_crm_endpoints.py` (regression) | passed |
| `npx tsc --noEmit` | clean |

**77 new tests, all green.** Full-suite result recorded below.

Interpreter note: `python` and `python3` on this machine resolve to interpreters without pytest
(`python` → the Hermes agent venv). The suite runs under
`C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe`. This means `init.sh`'s
pytest gate finds no interpreter here — pre-existing, not introduced by this change.

---

## What is still pending — and the order matters

1. **Apply migration `0048` — BEFORE deploying, not after.**
   `list_b2b_clients` now selects `service_band`, and its `except` branch falls back to **demo
   data** on any Supabase error. Deploying the code against a database without the column would
   make the Búnker's B2B roster silently show demo clients instead of real ones. Apply first,
   then push. (The pre-quote endpoint degrades safely either way — `uvt_no_disponible` — and
   `service_band` writes fail loudly.)

2. **Push and deploy.** The commit sits on `feat/pricing-quote-engine`. `main` auto-deploys to
   Vercel and Railway, so the push is the founder's call.

3. **No UI for the pre-quote result yet.** The backend contract ships; rendering it in the CRM
   is deliberately a separate change (proposal.md, Non-goals).

4. **No `service_band` backfill for the existing roster.** Nobody recorded which band those fees
   were quoted under, and guessing it from the amount is the inference this change exists to
   remove.
