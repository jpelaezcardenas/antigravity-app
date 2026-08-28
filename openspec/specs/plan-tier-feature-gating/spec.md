# plan-tier-feature-gating Specification

## Purpose
TBD - created by archiving change plan-tier-feature-gating. Update Purpose after archive.
## Requirements
### Requirement: Tenants carry an enforced plan tier

The system SHALL persist a `plan_tier` column on `tenants` (mirrored on `b2b_clients` for CRM
listing) as `text` with a `CHECK` constraint restricting values to
`'freemium' | 'starter' | 'growth' | 'enterprise'`, defaulting to `'starter'`. Every row that
exists before this column is added SHALL receive the default via the column's own `DEFAULT`
clause — no separate backfill script SHALL be required.

#### Scenario: Existing tenant keeps full access after migration
- **WHEN** the `plan_tier` column is added to a `tenants` table containing pre-existing rows
- **THEN** every pre-existing row's `plan_tier` is `'starter'`, not `NULL` and not `'freemium'`

#### Scenario: An invalid tier value is rejected at the database level
- **WHEN** an `INSERT` or `UPDATE` attempts to set `tenants.plan_tier` to a value other than
  `'freemium'`, `'starter'`, `'growth'`, or `'enterprise'`
- **THEN** the write is rejected by the `CHECK` constraint

### Requirement: A tier-to-feature map governs which features a tenant may use

The system SHALL expose `core/plan_features.py` with an explicit map from each plan tier to the
set of features it includes, and a `has_feature(plan_tier: str, feature: str) -> bool` function.
`'freemium'` SHALL include only `pulso_diario`. `'starter'`, `'growth'`, and `'enterprise'` SHALL
each include every feature that exists at the time this change ships: `pulso_diario`,
`centinela_alerts`, `liquidity_bridge`. An unrecognized or missing tier value passed to
`has_feature` SHALL return `True` for every feature (fail open), never `False`.

#### Scenario: Freemium tenant is granted Pulso Diario only
- **WHEN** `has_feature("freemium", "pulso_diario")` is called
- **THEN** it returns `True`
- **WHEN** `has_feature("freemium", "centinela_alerts")` or `has_feature("freemium",
  "liquidity_bridge")` is called
- **THEN** each returns `False`

#### Scenario: Every non-freemium tier has full access to today's features
- **WHEN** `has_feature(tier, feature)` is called for `tier` in `{"starter", "growth",
  "enterprise"}` and `feature` in `{"pulso_diario", "centinela_alerts", "liquidity_bridge"}`
- **THEN** every combination returns `True`

#### Scenario: An unrecognized tier value fails open, not closed
- **WHEN** `has_feature("some-future-tier-not-yet-in-the-map", "centinela_alerts")` is called
- **THEN** it returns `True`

### Requirement: The caller can retrieve their own tenant's identity and plan tier

The system SHALL expose `GET /api/v1/tenant/me`, requiring `Depends(get_current_user)` and
resolving the caller's tenant via the canonical `core/tenant_context.py::resolve_request_tenant_scope`.
On a resolved tenant, it SHALL return `{legal_name, plan_tier}` for that tenant. On an
unresolved tenant, it SHALL return `{legal_name: null, plan_tier: null, status: "empty"}` —
mirroring the existing `_empty_snapshot()` explicit-empty pattern used by `GET /api/v1/financials`
— and SHALL NOT fall back to Cliente Cero's identity.

#### Scenario: A resolved tenant sees their own legal name and tier
- **WHEN** an authenticated caller with `resolved_tenant_id = T1` (whose `tenants` row has
  `legal_name = "Acme SAS"`, `plan_tier = "growth"`) calls `GET /api/v1/tenant/me`
- **THEN** the response is `{legal_name: "Acme SAS", plan_tier: "growth"}`

#### Scenario: An unresolved tenant never sees Cliente Cero's identity
- **WHEN** an authenticated caller with no resolved tenant (and not the staging identity) calls
  `GET /api/v1/tenant/me`
- **THEN** the response is `{legal_name: null, plan_tier: null, status: "empty"}`, never Cliente
  Cero's `legal_name`/`plan_tier`
