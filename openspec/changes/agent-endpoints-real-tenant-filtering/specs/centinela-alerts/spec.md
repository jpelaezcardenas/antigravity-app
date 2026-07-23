## ADDED Requirements

### Requirement: Alert evaluation persists alerts under the caller's tenant
`POST /api/v1/centinela/evaluate` SHALL pass the caller's resolved tenant_id into
`CentinelaService.save_alerts`, which SHALL require it explicitly instead of hardcoding
Cliente Cero.

#### Scenario: Saved alerts carry the resolved tenant, not a hardcoded one
- **WHEN** an authenticated caller resolved to tenant A triggers alert evaluation
- **THEN** the persisted alerts' `tenant_id` is tenant A's, not Cliente Cero's

### Requirement: Alert reads never cross tenants
`GET /api/v1/centinela/alerts/{company_id}` SHALL verify that `company_id` belongs to the
caller's resolved tenant before returning any alert data.

#### Scenario: Own company's alerts are returned
- **WHEN** a caller resolved to tenant A requests alerts for a company belonging to tenant A
- **THEN** the endpoint returns that company's alerts

#### Scenario: A cross-tenant company_id returns 404
- **WHEN** a caller resolved to tenant A requests alerts for a company belonging to tenant B
- **THEN** the endpoint returns HTTP 404, not tenant B's alert data
