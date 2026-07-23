## ADDED Requirements

### Requirement: Tenant-scoped alerts feed for the authenticated caller

The system SHALL expose `GET /api/v1/centinela/alerts`, distinct from the existing
`GET /centinela/alerts/{company_id}` (unchanged, still consumed by the Hermes
`CentinelaAlertsTool`). The new route SHALL require `Depends(get_current_user)` and SHALL resolve
the caller's tenant using the same policy as `GET /api/v1/financials`: the caller's own resolved
tenant if present; Cliente Cero only for the unauthenticated staging identity
(`AUTH_ENFORCED=False`); an empty result for an authenticated caller whose tenant did not resolve
— **never** Cliente Cero's alerts for an unrelated authenticated client. The route SHALL filter
`centinela_alerts` by `tenant_id` and SHALL NOT apply the existing route's demo fallback.

#### Scenario: A client with resolved tenant sees only their own alerts
- **WHEN** an authenticated caller with `resolved_tenant_id = T1` calls `GET
  /api/v1/centinela/alerts`
- **THEN** the response's `alerts` contains only rows from `centinela_alerts` where
  `tenant_id = T1`, and rows belonging to a different tenant `T2` are never included

#### Scenario: Two clients never see each other's alerts
- **WHEN** tenant `T1` has 2 alert rows and tenant `T2` has 3 alert rows in `centinela_alerts`
- **THEN** `GET /api/v1/centinela/alerts` for a caller resolved to `T1` returns exactly 2 alerts,
  and for a caller resolved to `T2` returns exactly 3, with no overlap

#### Scenario: Staging identity resolves to Cliente Cero
- **WHEN** the caller is the permissive staging identity (`AUTH_ENFORCED=False`, no token)
- **THEN** the response reflects Cliente Cero's `tenant_id` alerts, preserving existing local
  dev/Contexia-overview behavior

#### Scenario: Authenticated caller with unresolved tenant gets an empty list, never Cliente Cero
- **WHEN** the caller is authenticated but has no `resolved_tenant_id` and is not the staging
  identity
- **THEN** the response is `{ alerts: [], alert_count: 0, critical_count: 0, warning_count: 0,
  risk_level: "none", source: "supabase" }` — the Cliente-Cero-resolution helper is never invoked

#### Scenario: No rows returns an honest empty list, not a demo fallback
- **WHEN** the resolved tenant has zero rows in `centinela_alerts`
- **THEN** the response's `alerts` is `[]` — the route never synthesizes demo alert data (unlike
  the legacy `/alerts/{company_id}` route)

#### Scenario: The legacy Hermes-consumed route is unaffected
- **WHEN** `GET /centinela/alerts/{company_id}` is called with an arbitrary `company_id`, as
  Hermes's `CentinelaAlertsTool` does today
- **THEN** its behavior (including the demo fallback) is unchanged by this change
