## MODIFIED Requirements

### Requirement: An authenticated caller with no resolved tenant never defaults to Cliente Cero
A caller who is authenticated (not the unauthenticated staging identity) but has no resolved
tenant SHALL receive no queue access — an empty list on read, and a rejection on write. This
path SHALL NEVER resolve to Cliente Cero. Write-path rejections (`enqueue`, `approve`,
`reject`) SHALL return HTTP 404, not 403 — a 403 would confirm the existence of a resource the
caller isn't allowed to see; 404 does not.

#### Scenario: Unresolved authenticated caller sees an empty queue
- **WHEN** an authenticated caller with no active `user_tenants` membership calls
  `GET /api/v1/approval-queue`
- **THEN** the response is an empty list, and Cliente Cero's tenant is never queried for this
  purpose

#### Scenario: Unresolved authenticated caller cannot enqueue
- **WHEN** the same caller calls `POST /enqueue`
- **THEN** the request is rejected with HTTP 404 before any Cliente Cero resolution occurs

#### Scenario: Unresolved authenticated caller cannot approve or reject
- **WHEN** the same caller calls `POST /approve` or `POST /reject`
- **THEN** the request is rejected with HTTP 404, not 403
