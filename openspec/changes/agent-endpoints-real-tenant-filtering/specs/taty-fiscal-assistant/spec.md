## MODIFIED Requirements

### Requirement: `/api/v1/agents/ask` is authenticated and tenant-scoped
`POST` and `GET /api/v1/agents/ask` SHALL resolve the caller's tenant from the authenticated
session (never from a client-supplied `company_id`) and SHALL NOT answer using another tenant's
profile. The unauthenticated staging identity SHALL fall back to Contexia's own Cliente Cero
identity; an authenticated caller whose tenant is unresolved SHALL receive a clear in-band
error. Tenant resolution SHALL go through `core/tenant_context.py::resolve_request_tenant_scope`
— the endpoint's previous file-local inline resolution ladder (and its dedicated async
`_resolve_cliente_cero_tenant_id()` helper) is removed; the observable contract is unchanged.

#### Scenario: Authenticated client is scoped to their own tenant
- **WHEN** an authenticated user with a resolved tenant calls `/api/v1/agents/ask`
- **THEN** Taty answers using that user's own tenant profile, regardless of any `company_id`
  supplied in the request

#### Scenario: Authenticated caller with no resolved tenant gets a clear error
- **WHEN** an authenticated caller with no resolved tenant membership calls
  `/api/v1/agents/ask`
- **THEN** the response has `error_code = "tenant_not_resolved"` and
  `requires_human_review = true`, unchanged from before the helper migration
