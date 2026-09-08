# Design — pricing-quote-engine

## Verified facts this design rests on

| Fact | How it was verified |
|---|---|
| `b2b_clients.monthly_fee_cents` **already exists** (bigint, nullable) | Live `information_schema.columns` query against Supabase `kpynymwghfwshvcvevxq`, 2026-09-08; also present in `apps/backend/migrations/0020_crm_b2b_retainers.sql` |
| Next free migration number is **0048** | `ls apps/backend/migrations/` — highest is `0047_radar_module_opens.sql`. (0032 was never used; 0033/0034 collided once — see ARCHITECTURE.md Decisión #15 — so the number was taken from the real directory listing, not inferred.) |
| `resolve_request_tenant_scope()` is the single canonical caller-tenant resolver | `apps/backend/core/tenant_context.py` docstring + ARCHITECTURE.md Decisión #17 |
| Shadow GL amounts are COP **minor units (cents)** | `erp_journal_lines.debit_minor` / `credit_minor`, bigint |
| Revenue accounts are `4100` / `4105` (credits) | `financials_service._classify_ventas_salidas` |

**Correction to the original request:** it stated `b2b_clients` has "`name`, `status`, `notes` and
nothing more: no place to store the agreed fee". That is not the live schema —
`monthly_fee_cents` has existed since migration 0020 and is already written by
`CrmService.create_b2b_client` and surfaced in the alta form. The real gap is the **band**, so
this change adds only `service_band` and makes the *existing* fee column visible and editable
after alta (today it can only be set at alta time).

---

## Decision 1 — `uvt_values` stores whole pesos, and the Shadow GL is converted at the boundary

`uvt_values.value_cop` is `bigint` in **whole COP**, per the request. Everything else in the
Shadow GL is in **minor units (cents)**. Mixing the two is exactly the class of bug this repo has
shipped before, so the conversion happens in exactly one place: `pricing_service` converts its
minor-unit revenue total to whole COP (`// 100`) once, immediately before any UVT comparison, and
the response carries both `ingresos_anualizados_cop` (whole COP) and `ingresos_anualizados_uvt`
(float). No other function in the module sees mixed units.

Rejected: storing the UVT in minor units for symmetry with the ledger. The UVT is a legal figure
published in whole pesos; storing $4.979.900 to mean $49.799 invites a 100× error in the far more
dangerous direction (a threshold silently 100× too high classifies every lead as non-declarant).

## Decision 2 — the tax year is a required parameter, and a missing UVT row is an error, not a fallback

`get_uvt_for_year(year)` reads `uvt_values` and raises `UvtNotFoundError` when the year is absent.
There is no default constant anywhere in the module. The endpoint catches it and returns
`estado: "uvt_no_disponible"` with the requested year echoed back, so the operator sees "we don't
know 2027's UVT yet" instead of a confidently wrong number computed from 2026's.

The endpoint's `anio_gravable` query parameter defaults to **the previous calendar year**
(2025 while today is 2026-09-08). That is the year whose obligation thresholds are currently
being assessed, and it correctly selects UVT 2025 = $49.799 for those thresholds — matching the
verified rule that año-gravable-2025 thresholds use UVT 2025, while UVT 2026 governs 2026
sanctions and withholding (which this endpoint does not compute).

## Decision 3 — `supera_umbral_declarante` reports ONE criterion, and the response says so

Five independent quantitative criteria (each 1.400 UVT except patrimonio at 4.500 UVT) plus one
qualitative criterion (responsable de IVA at 31 December) determine the filing obligation; any
one of them triggers it. From the Shadow GL we can observe **only gross revenue**.

Therefore `supera_umbral_declarante: true` is a genuine positive signal, but `false` **does not
mean "not obligated"** — it means "the one criterion we can see was not crossed". Encoding that
asymmetry only in documentation would guarantee it gets misread, so the response carries it
in-band:

- `criterio_evaluado: "ingresos_brutos"` — the single criterion behind the boolean.
- `criterios_no_evaluables: [...]` — the four unobservable quantitative criteria plus
  `responsabilidad_iva`, each named, always present.
- `umbral_declarante_uvt: 1400` and `umbral_declarante_cop` — the actual threshold used, so the
  number can be audited against the resolution rather than trusted.

This follows `GET /api/v1/radar/proyeccion-caja`'s precedent exactly (ARCHITECTURE.md, Radar
section): the endpoint declares its own limits in its payload, not only in docs.

## Decision 4 — the band is a suggestion anchored in UVT, and it can never be "alta" confidence

Band heuristics are module constants expressed in **UVT** (so they don't rot when the UVT moves)
plus a raw movement count:

| Band | Rule |
|---|---|
| `micro` | annualised revenue < 1.400 UVT **and** avg monthly lines < `MICRO_MAX_MONTHLY_LINES` (20) |
| `complejo` | annualised revenue ≥ `COMPLEJO_MIN_UVT` (5.000 UVT) **or** avg monthly lines ≥ `COMPLEJO_MIN_MONTHLY_LINES` (200) |
| `estandar` | everything else (the deliberate majority case) |

Confidence is capped at `"media"` and is **never `"alta"`** — same rule the Radar projection
follows, and for the same reason: the payroll/labour driver is half the fee criterion and is
structurally absent from the data model, so no output of this engine is ever fully grounded.

`confianza` is `"baja"` when either:
- the tenant has 3–5 distinct months of history (thin extrapolation), **or**
- the suggested band is `micro` — because Micro is *defined* as "movimiento mínimo **sin carga
  laboral**", and the absence of payroll is precisely the thing we cannot observe. A `micro`
  suggestion is therefore the least grounded output the engine can produce, and says so.

## Decision 5 — thin history returns an explicit state, never a fabricated band

Fewer than `MIN_HISTORY_MONTHS` (3) distinct months of `erp_journal_entries` activity in the
trailing 12 months returns `estado: "sin_historico_suficiente"` with `banda_sugerida: null`.
Annualising one month by ×12 is fabrication with a decimal point, and this repo's rules
(CLAUDE.md §9, hard rule 1) forbid inventing data to make an output look complete. Mirrors
`calculate_cash_projection_13w`'s `sin_historico_suficiente`.

Annualisation for a partial window is `observed_revenue * 12 / months_observed`, and
`meses_observados` is always in the response so the extrapolation factor is visible.

## Decision 6 — unresolved tenant returns 404, diverging from the Radar read-endpoint precedent

Decisión #17 sets 404 (anti-enumeration) for write/ownership routes, and
`GET /radar/proyeccion-caja` chose a graceful 200 for read-only routes. This endpoint returns
**404** on an unresolved tenant, per the founder's explicit instruction for this change.

That is defensible on its own terms: unlike a projection the client reads about their own
business, a pre-quote is a *commercial sizing* artifact. A 200-with-empty-state would let an
authenticated caller with no tenant membership probe the endpoint's existence and shape. Either
way, the binding constraint is identical to every sibling: **never fall back to Cliente Cero.**

## Decision 7 — new `/pricing` router, not `/agents/*` and not bolted onto `/crm`

The repo splits agent-internal routes (`/agents/*`) from clean per-tenant read surfaces
(`/financials`, `/centinela`, `/radar`, `/tenant`). This is a per-tenant read surface, so it gets
`/pricing`. It is deliberately *not* added to `crm_endpoints.py`: that router is mounted behind
the `CRM_CANONICAL` feature flag and carries a blanket router-level
`dependencies=[Depends(get_current_user)]` scoped to Cliente Cero's operator roster — the wrong
tenant semantics entirely for an endpoint that must resolve the *caller's own* tenant.

## Decision 8 — no plan gating, and `core/plan_features.py` is not touched

Explicit constraint from the request, and correct on the merits: Pro Micro and Pro Estándar are
the *same software product*. Gating the pre-quote engine by tier would also defeat its purpose,
which is sizing **freemium** leads for an upsell conversation.

Note for the reviewer: `core/plan_features.py` currently has uncommitted working-tree changes
belonging to the separate `hermes-jarvis-contexia` effort (`jarvis_chat` / `jarvis_voice`
features). This change neither modifies that file nor includes it in its commit.

## Decision 9 — the pre-quote endpoint is strictly read-only

No `approval_queue` row, no telemetry write, no state change of any kind. The Radar projection's
`radar_module_opens` write is an explicitly-scoped exception owned by `radar-adoption-tracking`;
it is not a pattern to copy by default.

## Out of scope (named, not silently dropped)

- Rendering the pre-quote result anywhere in the PWA or Búnker UI.
- Deriving `patrimonio bruto` from balance-sheet accounts. The Shadow GL's coverage of asset
  accounts is not established as complete for any tenant; a partial patrimony figure compared
  against a 4.500 UVT legal threshold would be worse than an honest `null`.
- Backfilling `service_band` for the existing roster — nobody has recorded which band those fees
  were quoted under, and guessing it from the amount is exactly the inference this change exists
  to stop.
