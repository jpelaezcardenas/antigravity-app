## ADDED Requirements

### Requirement: Approval queue endpoints require authentication
All 4 `/api/v1/approval-queue/*` endpoints (list, enqueue, approve, reject) SHALL resolve the
caller via `get_current_user` before doing any queue read or write. No endpoint SHALL rely on
the fail-open `TenantContextMiddleware` state as its sole identity source.

#### Scenario: Unauthenticated caller in production is rejected
- **WHEN** `AUTH_ENFORCED=true` and a caller has no valid token
- **THEN** every approval-queue endpoint responds `401`, matching `get_current_user`'s
  standard behavior

### Requirement: Drafts are stamped with the caller's resolved tenant, never a silent default
`enqueue_draft` SHALL require an explicit `tenant_id` and SHALL NOT resolve Cliente Cero
internally. Every enqueue call site (HTTP endpoint or internal service) SHALL pass a tenant_id
it resolved explicitly.

#### Scenario: A client's draft is stamped with the client's own tenant
- **WHEN** an authenticated client with a resolved tenant calls `POST /enqueue`
- **THEN** the persisted `approval_queue` row's `tenant_id` equals that client's tenant, not
  Cliente Cero's

#### Scenario: Missing tenant_id fails the enqueue instead of defaulting
- **WHEN** `enqueue_draft` is called without a truthy `tenant_id`
- **THEN** it returns a failure with no row inserted, and never falls back to Cliente Cero

### Requirement: Reads and decisions are scoped to the caller's tenant
`GET /api/v1/approval-queue`, `POST /approve`, and `POST /reject` SHALL be scoped to the
caller's own tenant unless the caller is a Contexia operator (see next requirement). A caller
SHALL NOT be able to list, approve, or reject a draft belonging to a different tenant.

#### Scenario: A client only sees its own tenant's queue
- **WHEN** tenant A and tenant B each have enqueued drafts and a tenant-A client calls
  `GET /api/v1/approval-queue`
- **THEN** the response includes only tenant A's drafts

#### Scenario: A client cannot approve or reject another tenant's draft
- **WHEN** a tenant-B client calls `POST /approve` with a `decision_id` belonging to tenant A
- **THEN** the request fails with the same "not found" error as a nonexistent id — the
  response does not reveal that the draft exists under another tenant

### Requirement: A Contexia operator sees and can act on every tenant's queue
A caller whose resolved tenant is Cliente Cero (Contexia's own tenant) SHALL be treated as an
operator: `GET /api/v1/approval-queue` returns drafts across all tenants (optionally filtered
by an explicit `?tenant_id=` query parameter), and `POST /approve` / `POST /reject` are
unrestricted by tenant. Each returned draft SHALL include its `tenant_id` so an operator can
distinguish rows.

#### Scenario: Operator lists all tenants' drafts
- **WHEN** a Cliente Cero-resolved caller calls `GET /api/v1/approval-queue` with no
  `tenant_id` filter
- **THEN** the response includes drafts from every tenant, each item carrying its `tenant_id`

#### Scenario: Operator filters to one tenant
- **WHEN** a Cliente Cero-resolved caller calls `GET /api/v1/approval-queue?tenant_id=<X>`
- **THEN** the response includes only tenant X's drafts

### Requirement: An authenticated caller with no resolved tenant never defaults to Cliente Cero
A caller who is authenticated (not the unauthenticated staging identity) but has no resolved
tenant SHALL receive no queue access — an empty list on read, and a rejection on write. This
path SHALL NEVER resolve to Cliente Cero.

#### Scenario: Unresolved authenticated caller sees an empty queue
- **WHEN** an authenticated caller with no active `user_tenants` membership calls
  `GET /api/v1/approval-queue`
- **THEN** the response is an empty list, and Cliente Cero's tenant is never queried for this
  purpose

#### Scenario: Unresolved authenticated caller cannot enqueue
- **WHEN** the same caller calls `POST /enqueue`
- **THEN** the request is rejected before any Cliente Cero resolution occurs

### Requirement: The unauthenticated local/staging path preserves existing behavior
When `AUTH_ENFORCED=false` and no token is supplied, the caller falls back to the staging
identity, which resolves to a Cliente Cero-scoped operator — matching today's local
development behavior.

#### Scenario: Local dev without a token still works
- **WHEN** `AUTH_ENFORCED=false` and a request carries no Authorization header
- **THEN** the caller is scoped as a Cliente Cero operator (unrestricted reads, enqueues under
  Cliente Cero), unchanged from current behavior

### Requirement: `approval_queue.tenant_id` is enforced NOT NULL at the schema level
The `approval_queue.tenant_id` column SHALL NOT permit `NULL` and SHALL NOT default to a
placeholder (zeros) UUID — every row must carry a real tenant id at write time.

#### Scenario: A write that omits tenant_id fails at the database
- **WHEN** any insert into `approval_queue` omits `tenant_id`
- **THEN** the database rejects it with a NOT NULL violation rather than silently applying a
  placeholder tenant
