## ADDED Requirements

### Requirement: Taty resolves a client profile from the caller's own tenant
The system SHALL derive a Taty client profile (legal name, NIT, tone, enabled knowledge sources,
escalation criteria) from the `tenants` table and an in-code default template, keyed by the
tenant uuid, with no per-client seeding step required. Any provisioned tenant SHALL be usable by
Taty without a code change.

#### Scenario: Provisioned tenant gets a scoped, working answer
- **WHEN** a request resolves to a real, provisioned tenant uuid
- **THEN** `ask()` builds its prompt using that tenant's `legal_name` and returns an answer with
  no `error_code`

#### Scenario: Unknown tenant fails clearly, not silently
- **WHEN** `ask()` is called with a tenant uuid that does not exist in `tenants`
- **THEN** the response has `error_code = "tenant_not_found"`, `confidence = 0.0`, and
  `requires_human_review = True` — never an unhandled exception, never a silent generic answer

#### Scenario: Retired legacy demo keys degrade gracefully
- **WHEN** `ask()` is called with a legacy non-uuid key such as `"ferez-001"`
- **THEN** the response has `error_code = "tenant_not_found"` (no exception)

### Requirement: Taty never asserts an unverified tax regime
The system SHALL NOT include a tax-regime claim (e.g. "Régimen Común") in the prompt for a
tenant whose regime is not actually known.

#### Scenario: Unknown regime is omitted, not assumed
- **WHEN** a tenant's profile has no resolved `regimen`
- **THEN** the built prompt contains no régimen assertion

### Requirement: `/api/v1/agents/ask` is authenticated and tenant-scoped
`POST` and `GET /api/v1/agents/ask` SHALL resolve the caller's tenant from the authenticated
session (never from a client-supplied `company_id`) and SHALL NOT answer using another tenant's
profile. The endpoint MAY fall back to Cliente Cero only for the unauthenticated/staging
identity; an authenticated caller whose tenant is unresolved SHALL receive a clear in-band error,
never Cliente Cero.

#### Scenario: Authenticated client is scoped to their own tenant
- **WHEN** an authenticated user with a resolved tenant calls `/api/v1/agents/ask`
- **THEN** Taty answers using that user's own tenant profile, regardless of any `company_id`
  present in the request body

#### Scenario: Staging identity falls back to Cliente Cero
- **WHEN** the unauthenticated staging identity calls `/api/v1/agents/ask`
- **THEN** Taty answers using the Cliente Cero tenant profile

#### Scenario: Unresolved authenticated caller does not leak another tenant
- **WHEN** an authenticated caller has no active tenant membership
- **THEN** the response has `error_code = "tenant_not_resolved"` and is never answered using
  Cliente Cero or any other tenant's profile

#### Scenario: A supplied `company_id` cannot be used to read another tenant's profile
- **WHEN** an authenticated caller (resolved to tenant A) supplies a `company_id` in the request
  body that corresponds to a different tenant B
- **THEN** Taty answers using tenant A's profile, and the supplied `company_id` is ignored

### Requirement: Telegram resolves its mapped company to a tenant before calling Taty
The Telegram webhook SHALL translate its `telegram_chat_mappings.company_id` to a tenant uuid via
`tenants.company_id` before calling Taty, and SHALL NOT call Taty with an untranslatable id.

#### Scenario: Mapped chat resolves and answers
- **WHEN** a Telegram chat is mapped to a `company_id` that matches a row in `tenants`
- **THEN** Taty is called with that tenant's uuid and answers normally

#### Scenario: Unmapped or untranslatable chat is rejected before calling Taty
- **WHEN** a Telegram chat's mapped `company_id` does not match any tenant
- **THEN** the existing "chat no configurado" reply is sent and Taty's `ask()` is never invoked

### Requirement: No duplicate or dead Taty entry points
The system SHALL expose exactly one authenticated Q&A entry point (`/api/v1/agents/ask`) backed
by exactly one profile-resolution path. Deprecated duplicate routes and unreferenced alternate
routers SHALL be removed rather than left coexisting.

#### Scenario: Deprecated wrapper route is gone
- **WHEN** a client calls `POST /api/v1/agents/taty/ask`
- **THEN** the route no longer exists (404), and `/api/v1/agents/ask` is the sole documented
  entry point

#### Scenario: No unreferenced intent router remains
- **WHEN** the codebase is searched for `taty_intent_router`
- **THEN** no such module or its test exists
