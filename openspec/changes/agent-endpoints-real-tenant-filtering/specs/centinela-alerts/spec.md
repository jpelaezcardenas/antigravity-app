## ADDED Requirements

### Requirement: Centinela endpoints resolve tenant through the shared canonical helper
`centinela_endpoints.py::/evaluate` and `centinela_endpoints.py::/alerts/{company_id}` SHALL
resolve the caller's tenant via `core/tenant_context.py::resolve_request_tenant_scope`, not the
now-removed `resolve_caller_tenant` helper. This is an internal refactor — the observable
behavior (alerts saved under the caller's own tenant; an unresolved caller gets an empty
result, never Cliente Cero's alerts) is unchanged.

#### Scenario: Evaluate saves alerts under the resolved tenant
- **WHEN** an authenticated caller with a resolved tenant POSTs to `/evaluate`
- **THEN** saved alerts carry `resolve_request_tenant_scope(user, client).tenant_id`, exactly
  as they previously carried `resolve_caller_tenant(user, client)`'s return value

#### Scenario: Unresolved caller still gets an empty, never-Cliente-Cero result
- **WHEN** an authenticated caller with no resolved tenant calls `GET /alerts/{company_id}`
- **THEN** the response has `alert_count == 0` and `source == "none"`, unchanged from before
  the helper migration
