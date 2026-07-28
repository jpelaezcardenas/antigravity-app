# agent-endpoint-tenant-scoping Specification

## Purpose
Created by archiving change `agent-endpoints-real-tenant-filtering` (2026-07-23). Defines the
authentication and tenant-resolution contract shared by every agent-facing HTTP presentation
file: `agents_endpoints.py`, `pulso_diario_endpoints.py`, `centinela_agents_endpoints.py`,
`approval_queue_endpoints.py`, `taty_endpoints.py`, `centinela_endpoints.py`.

## Requirements

### Requirement: All agent HTTP endpoints require an authenticated caller
Every route in `agents_endpoints.py`, `pulso_diario_endpoints.py`,
`centinela_agents_endpoints.py`, `approval_queue_endpoints.py`, `taty_endpoints.py`, and
`centinela_endpoints.py` SHALL depend on `get_current_user`.

#### Scenario: Valid bearer token is accepted
- **WHEN** a caller sends a valid Supabase or backend session token
- **THEN** the endpoint resolves `user` via `get_current_user` and proceeds

#### Scenario: Missing token is rejected with 401 when AUTH_ENFORCED is true
- **WHEN** a caller sends no `Authorization` header and `AUTH_ENFORCED=true`
- **THEN** the endpoint returns HTTP 401

#### Scenario: Staging fallback identity is used when AUTH_ENFORCED is false
- **WHEN** a caller sends no token and `AUTH_ENFORCED=false`
- **THEN** `get_current_user` returns `_STAGING_USER` and the endpoint proceeds under the
  staging identity, unchanged from today's behavior

### Requirement: Every DB-touching agent route resolves tenant through one canonical helper
Any route that reads or writes tenant-scoped data SHALL resolve the caller's tenant via
`core/tenant_context.py::resolve_request_tenant_scope`, and SHALL NOT implement a second,
endpoint-local or file-local resolution ladder.

#### Scenario: Token with a resolved tenant scopes to that tenant
- **WHEN** `user["resolved_tenant_id"]` is present
- **THEN** the endpoint uses `resolve_request_tenant_scope(user, client).tenant_id` for every
  DB read/write

#### Scenario: Staging user falls back to Cliente Cero
- **WHEN** the caller is `_STAGING_USER` (`AUTH_ENFORCED=false`, no token)
- **THEN** the endpoint resolves to the real Cliente Cero tenant_id via the same helper

#### Scenario: Authenticated caller without a tenant is never given Cliente Cero
- **WHEN** a caller is authenticated but has no resolvable tenant membership
- **THEN** `resolve_request_tenant_scope` returns `None`, and the endpoint returns an empty
  result or a rejection (per its own contract), never Cliente Cero's data

#### Scenario: No second resolution helper exists
- **WHEN** the codebase is grepped for tenant-resolution logic outside
  `core/tenant_context.py::resolve_request_tenant_scope`
- **THEN** no file-local or endpoint-local 3-branch/4-branch ladder is found (the previously
  separate `resolve_caller_tenant` helper and Taty's inline resolution are both removed)

### Requirement: Pure-LLM agent endpoints are auth-gated without tenant scoping
`/social/generate-content`, `/pulso/analyze`, `/centinela/monitor`, `/centinela/decide`,
`/compliance/audit`, and `/task-info/{task_type}` touch no database and SHALL require only
an authenticated caller, with no tenant parameter threaded through.

#### Scenario: Analysis over client-supplied payload requires only identity
- **WHEN** an authenticated caller POSTs to `/pulso/analyze` with arbitrary analysis data
- **THEN** the endpoint returns the LLM response without consulting or requiring a tenant_id

### Requirement: The orchestrator demo pipeline remains demo but auth-gated
`POST /orchestrator/full-pipeline` SHALL keep returning its hardcoded `"mode": "demo"`
response and SHALL require an authenticated caller.

#### Scenario: Full pipeline returns mode=demo to an authenticated caller
- **WHEN** an authenticated caller POSTs to `/orchestrator/full-pipeline`
- **THEN** the response includes `"mode": "demo"` and the existing illustrative note,
  unchanged from today's payload shape

#### Scenario: Unauthenticated pipeline call is rejected
- **WHEN** a caller with no valid token POSTs to `/orchestrator/full-pipeline` under
  `AUTH_ENFORCED=true`
- **THEN** the endpoint returns HTTP 401 before returning any demo payload

### Requirement: Stub agent endpoints echo the resolved tenant, never the raw JWT claim
`pulso_diario_endpoints.py::/summary` and `centinela_agents_endpoints.py::/generate-draft`
SHALL resolve tenant via `resolve_request_tenant_scope` and SHALL NOT read
`request.state.tenant_id` directly.

#### Scenario: Summary reflects the resolved tenant UUID
- **WHEN** an authenticated caller with a resolved tenant POSTs to `/summary`
- **THEN** the response's tenant reference is the resolved tenant UUID

#### Scenario: Draft stub never emits "default-tenant"
- **WHEN** any caller (including the staging identity) POSTs to `/generate-draft`
- **THEN** the response never contains the literal string `"default-tenant"`
