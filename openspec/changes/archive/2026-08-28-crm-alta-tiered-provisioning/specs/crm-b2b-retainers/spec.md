## ADDED Requirements

### Requirement: B2B client alta accepts an explicit plan tier and returns an invite link

The system SHALL expose `POST /api/v1/crm/b2b/clients` accepting an optional `plan_tier`
(`freemium | starter | growth | enterprise`, default `starter` when omitted) alongside the
existing `name`/`email`/`phone`/`monthly_fee_cents` fields. The created `tenants` row and
`b2b_clients` row SHALL both carry this `plan_tier` value explicitly. When an `email` is supplied,
the system SHALL provision a Supabase Auth login for that email via `generate_link(type=
"invite")` rather than a discarded password, and SHALL return the resulting link as
`invite_link` in the response — Supabase SHALL NOT be relied upon to send this link itself.

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
