### Requirement: Each B2B client has its own tenant and distinct financial data
The system SHALL provision one `tenants` row per B2B retainer client (plus new prospects such as
CÓDIGO 520), and SHALL seed distinct synthetic Shadow GL (`erp_journal_entries` / `erp_journal_lines`)
per client tenant such that `GET /api/v1/financials` returns a materially different `caja_real` for
each client.

#### Scenario: Two clients see different Caja Real
- **WHEN** client A and client B each authenticate and call `GET /api/v1/financials`
- **THEN** each response reflects that client's own tenant and `caja_real(A) != caja_real(B)`, and
  neither equals the Cliente Cero balance

#### Scenario: Synthetic rows are identifiable and reversible
- **WHEN** the per-tenant Shadow GL seed is applied
- **THEN** every seeded journal row carries a `SYNTH:`/`SYNTH-` prefix in its `memo` and
  `external_reference_id`, so it can be located and removed without touching real Cliente Cero data

### Requirement: B2B clients carry contact data and a login linkage
The system SHALL extend `b2b_clients` with `email`, `phone`, `contact_name`, `client_tenant_id`
(FK `tenants`), `login_user_id` (FK `auth.users`), and `provision_status`. Contact data SHALL be
backfilled from the source ledger.

#### Scenario: Roster exposes contact + provisioning state
- **WHEN** an admin lists the B2B roster
- **THEN** each client row includes its `email`/`phone` (when known), its `client_tenant_id`, and a
  `provision_status` indicating whether a login exists

### Requirement: Client PWA logins are provisioned without outbound email
The system SHALL create an `auth.users` record for each client that has an email, with
`email_confirmed_at` set, `app_metadata.role = 'cliente'`, and a temporary password, and SHALL wire
`user_tenants` + `user_roles` (+ `usuarios`) to that client's own tenant. The provisioning flow SHALL
NOT send any email to the client.

#### Scenario: Provisioned client can authenticate and is routed to the end-user PWA
- **WHEN** a provisioned client signs in at `login.html`
- **THEN** authentication succeeds and `destinationForRole` routes them to `/app/overview` (role
  `cliente`), not `/app/bunker`

#### Scenario: A roster client with no email is not given a login
- **WHEN** a roster client has no email in the source ledger
- **THEN** it is NOT provisioned a login and its `provision_status` reflects "pending email" until an
  email is added; if the client turns out to never have been a real client at all, the founder removes
  it from the roster entirely rather than leaving a dangling unprovisioned row

### Requirement: Financials are scoped to the caller's tenant
`GET /api/v1/financials` SHALL resolve the caller's tenant from the authenticated session and SHALL NOT
return another tenant's data. It MAY fall back to Cliente Cero only for the unauthenticated/local
staging path (no real session); an authenticated caller whose tenant is unresolved SHALL receive an
empty snapshot, never Cliente Cero.

#### Scenario: Authenticated client is scoped to own tenant
- **WHEN** an authenticated client calls `GET /api/v1/financials`
- **THEN** the snapshot is computed for that client's `client_tenant_id`

#### Scenario: Unresolved authenticated caller does not leak Cliente Cero
- **WHEN** an authenticated caller has no active `user_tenants` membership
- **THEN** the response is an empty snapshot (`status: "empty"`), not the Cliente Cero balance

### Requirement: Supabase session tokens are verified regardless of signing scheme
The backend SHALL verify Supabase Auth session tokens whether they are signed with the legacy shared
HS256 secret or with Supabase's current asymmetric scheme (an `alg`/`kid`-bearing header, verified via
the project's JWKS endpoint). A token using either scheme SHALL resolve to a valid identity when it is
otherwise valid (correct signature, not expired, correct audience).

#### Scenario: An asymmetric (ES256/JWKS) session token is accepted
- **WHEN** a client authenticates and Supabase issues a session token signed with an asymmetric key
  (`kid` present in the header)
- **THEN** the backend fetches (or uses its cached copy of) the project's JWKS, finds the matching key,
  and verifies the token successfully

#### Scenario: A legacy HS256 session token is still accepted
- **WHEN** a session token is signed with the legacy shared secret (`SUPABASE_JWT_SECRET`, no `kid`
  routing to an asymmetric algorithm)
- **THEN** the backend verifies it via the shared-secret path, unaffected by JWKS support
