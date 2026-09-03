# centinela-alerts Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: Centinela enriches alerts with similar past decisions
When Centinela detects a DIAN ↔ Siigo anomaly, it queries the knowledge base for similar past approvals and includes them in the alert payload.

#### Scenario: Centinela alert includes similar decisions
- **WHEN** Centinela detects a transaction mismatch
- **THEN** system generates embedding for the transaction
- **AND** calls `/api/v1/kb/search-similar` to find related past approvals
- **AND** alert context includes: `{ similar_decisions: [...], best_match_confidence: 0.85 }`

#### Scenario: Resolution Agent can reference historical approval
- **WHEN** similar_decisions[0] is returned with high confidence (> 0.8)
- **THEN** Resolution Agent can optionally base new draft on historical approval reason
- **AND** new draft can inherit accounting treatment from similar case

#### Scenario: No similar decisions found
- **WHEN** Centinela query returns no matches (< threshold)
- **THEN** alert is still sent, similar_decisions = []
- **AND** Resolution Agent drafts from scratch (normal flow)

### Requirement: Centinela logs similarity match metrics
The system SHALL record how often similar decisions are found and used.

#### Scenario: Match metrics logged
- **WHEN** Centinela finds similar decisions for an alert
- **THEN** logs entry includes: transaction_id, best_similarity_score, num_matches, alert_timestamp

#### Scenario: Ops team can monitor compounding memory growth
- **WHEN** weekly metrics aggregated
- **THEN** shows: "60% of alerts now have similar decisions (up from 10% last month)"
- **AND** ops team can see knowledge base is learning

### Requirement: Centinela alert payload compatible with Hermes UI
The similarity search data in Centinela alert is formatted for display in Hermes Desktop Approval Queue UI.

#### Scenario: Alert JSON schema includes similar_decisions array
- **WHEN** Centinela publishes alert to Telegram or Hermes
- **THEN** JSON includes: `{ similar_decisions: [{ content, similarity, decided_by, timestamp }, ...] }`
- **AND** Hermes UI can render "Similar approvals" card inline with Centinela alert

### Requirement: Centinela endpoints resolve tenant through the shared canonical helper
`centinela_endpoints.py::/evaluate` and `centinela_endpoints.py::/alerts/{company_id}` SHALL
resolve the caller's tenant via `core/tenant_context.py::resolve_request_tenant_scope`, not a
second, endpoint-local resolution helper. Alerts SHALL be persisted under the caller's own
tenant, never a hardcoded default; an unresolved caller SHALL see an empty result, never
Cliente Cero's data.

#### Scenario: Evaluate saves alerts under the resolved tenant
- **WHEN** an authenticated caller with a resolved tenant POSTs to `/evaluate`
- **THEN** saved alerts carry `resolve_request_tenant_scope(user, client).tenant_id`

#### Scenario: Unresolved caller gets an empty, never-Cliente-Cero result
- **WHEN** an authenticated caller with no resolved tenant calls `GET /alerts/{company_id}`
- **THEN** the response has `alert_count == 0` and `source == "none"`

### Requirement: Tenant-scoped alerts feed for the authenticated caller

The system SHALL expose `GET /api/v1/centinela/alerts`, distinct from the existing
`GET /centinela/alerts/{company_id}` (unchanged, still consumed by the Hermes
`CentinelaAlertsTool`). The new route SHALL require `Depends(get_current_user)` and SHALL resolve
the caller's tenant using the same policy as `GET /api/v1/financials`: the caller's own resolved
tenant if present; Cliente Cero only for the unauthenticated staging identity
(`AUTH_ENFORCED=False`); an empty result for an authenticated caller whose tenant did not resolve
— **never** Cliente Cero's alerts for an unrelated authenticated client. The route SHALL filter
`centinela_alerts` by `tenant_id` and SHALL NOT apply the existing route's demo fallback.

Before querying `centinela_alerts` for a resolved tenant, the system SHALL check whether that
tenant's `plan_tier` includes the `centinela_alerts` feature (via
`core/plan_features.py::has_feature`). A `freemium` tenant does not include this feature; the
route SHALL return `{ alerts: [], alert_count: 0, critical_count: 0, warning_count: 0, risk_level:
"none", source: "supabase", status: "not_in_plan" }` instead of querying `centinela_alerts` — the
new `status` field is additive-only and SHALL NOT appear (or SHALL be omitted/absent) for any
tenant whose plan includes this feature, so no existing caller's response shape changes.

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
- **THEN** its behavior (including the demo fallback) is unchanged by this change — the plan-tier
  check applies only to `GET /api/v1/centinela/alerts`

#### Scenario: A freemium tenant gets an explicit not_in_plan signal, distinct from a genuine empty list
- **WHEN** a resolved tenant's `plan_tier` is `"freemium"` calls `GET /api/v1/centinela/alerts`
- **THEN** the response has `alerts: []` and `status: "not_in_plan"`, distinguishable from a paid
  tenant with genuinely zero alerts (which omits `status` or has no such field set)

