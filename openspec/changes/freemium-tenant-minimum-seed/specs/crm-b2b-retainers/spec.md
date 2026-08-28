## MODIFIED Requirements

### Requirement: B2B client alta accepts an explicit plan tier and returns an invite link

The system SHALL expose `POST /api/v1/crm/b2b/clients` accepting an optional `plan_tier`
(`freemium | starter | growth | enterprise`, default `starter` when omitted) alongside the
existing `name`/`email`/`phone`/`monthly_fee_cents` fields. The created `tenants` row and
`b2b_clients` row SHALL both carry this `plan_tier` value explicitly. When an `email` is supplied,
the system SHALL provision a Supabase Auth login for that email via `generate_link(type=
"invite")` rather than a discarded password, and SHALL return the resulting link as
`invite_link` in the response — Supabase SHALL NOT be relied upon to send this link itself.

When `plan_tier` is `"freemium"`, the request MAY also include an optional
`opening_balance_cents` (positive integer, COP minor units). When provided and greater than
zero, the system SHALL seed a single synthetic opening-balance entry into the new tenant's own
Shadow General Ledger (never Cliente Cero's, never another tenant's), reusing the
`SYNTH-{nit}-OPEN` / `SYNTH:per-tenant-client-access` naming convention from the existing
per-tenant-client-access seed pattern. `opening_balance_cents` SHALL be ignored (no seed, no
error) for any tier other than `freemium`. The seed SHALL be idempotent: submitting the same
alta twice SHALL NOT create a duplicate opening-balance entry.

#### Scenario: Alta with an explicit tier writes it to both tenants and b2b_clients
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` with `plan_tier: "growth"`
- **THEN** the newly created `tenants` row and `b2b_clients` row both have `plan_tier = "growth"`

#### Scenario: Alta with no tier defaults to starter, unchanged from prior behavior
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` without a `plan_tier` field
- **THEN** the newly created rows have `plan_tier = "starter"`

#### Scenario: Alta with an email returns a usable invite link, not a discarded password
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` with an `email`
- **THEN** the response includes a non-empty `invite_link` string, and no password is generated
  or persisted anywhere

#### Scenario: The provisioned login's legacy plan column matches the chosen tier
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` with `plan_tier: "enterprise"` and an
  `email`
- **THEN** the resulting `usuarios.plan` value is `"enterprise"`, not the literal string
  `"starter"`

#### Scenario: Freemium alta with an opening balance seeds the new tenant's Shadow GL
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` with `plan_tier: "freemium"` and
  `opening_balance_cents: 500000`
- **THEN** the new tenant's `erp_journal_entries` gains exactly one entry with
  `external_reference_id = "SYNTH-{nit}-OPEN"` and two `erp_journal_lines` (debit account `1110`,
  credit account `3105`, both for 500000 minor units), and no other tenant's Shadow GL is touched

#### Scenario: Freemium alta without an opening balance seeds nothing
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` with `plan_tier: "freemium"` and no
  `opening_balance_cents`
- **THEN** no Shadow GL entry is created for the new tenant

#### Scenario: opening_balance_cents on a non-freemium tier is ignored, not an error
- **WHEN** an admin calls `POST /api/v1/crm/b2b/clients` with `plan_tier: "starter"` and
  `opening_balance_cents: 500000`
- **THEN** the client is created successfully with `plan_tier = "starter"` and no Shadow GL entry
  is seeded

#### Scenario: Re-submitting the same freemium alta does not duplicate the seed
- **WHEN** the same alta request (same tenant, same `opening_balance_cents`) is effectively
  retried after the tenant and seed already exist
- **THEN** the seed function does not insert a second `SYNTH-{nit}-OPEN` entry for that tenant
