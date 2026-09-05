### Requirement: Internal ingestion endpoints are machine-to-machine and fail closed

The poller-facing endpoints `POST /internal/siigo-sync/run` and `POST /internal/ingest/file`
SHALL be mounted outside `/api/v1/*` so no `vercel.json` rewrite exposes them publicly, and
SHALL authenticate with the `X-Internal-Api-Key` header matched against `INTERNAL_API_KEY`.

An unset `INTERNAL_API_KEY` SHALL reject every request rather than allowing unauthenticated
access.

#### Scenario: Missing server-side key rejects all callers
- **WHEN** `INTERNAL_API_KEY` is not configured on the backend
- **THEN** every request to an `/internal/*` ingestion route returns 503, never 200

#### Scenario: Wrong key is rejected
- **WHEN** a caller supplies an `X-Internal-Api-Key` that does not match
- **THEN** the request returns 401

#### Scenario: Internal routes are registered at boot
- **WHEN** the application starts
- **THEN** both `/internal/siigo-sync/run` and `/internal/ingest/file` are present in the route
  table; a router-registration exception SHALL be treated as a startup failure, not a warning

---

### Requirement: Siigo credentials are per tenant, env-var only, and the Partner-Id fails closed

Per-tenant Siigo credentials SHALL be read from dynamic env vars
(`SIIGO_USERNAME_<TENANT_UUID_WITH_UNDERSCORES>`, `SIIGO_ACCESS_KEY_<...>`) and SHALL NOT be
stored in the database or in source.

`SIIGO_PARTNER_ID` SHALL have no default value. `_partner_id()` SHALL raise
`SiigoConfigurationError` when it is unset, rather than sending an unverified value.

#### Scenario: A tenant without both credentials is not syncable
- **WHEN** only one of the username/access-key pair is set for a tenant
- **THEN** `get_siigo_credentials()` returns `None` and `SiigoApiClient.for_tenant()` returns
  `None`

#### Scenario: Sync request for an unconfigured tenant is a 404
- **WHEN** `/internal/siigo-sync/run` is called for a tenant with no credentials
- **THEN** the response is 404, not a 500 and not a silent no-op

#### Scenario: Unset Partner-Id refuses to call Siigo
- **WHEN** `SIIGO_PARTNER_ID` is empty and a Siigo call is attempted
- **THEN** `SiigoConfigurationError` is raised naming the variable

#### Scenario: No guessed Partner-Id survives in source
- **WHEN** `services/siigo_api_client.py` source is inspected
- **THEN** it contains neither `contexiaFinancialOS` nor `contexia-financial-os`

---

### Requirement: The Siigo sync is strictly read-only and partially fault-tolerant

`sync_to_shadow_gl()` SHALL only read from Siigo and write to Contexia's own Shadow GL. It SHALL
NEVER write back to the client's Siigo account.

A failure fetching journals SHALL NOT prevent invoices from being fetched, and vice versa; errors
SHALL be collected and returned in the summary.

#### Scenario: Partial failure still ingests what was retrieved
- **WHEN** the journals call fails but the invoices call succeeds
- **THEN** the invoice rows are ingested and the returned `errors` list names the journals failure

#### Scenario: Live sync data is marked as real
- **WHEN** rows fetched from the Siigo API are ingested
- **THEN** they are written with `is_verified_real=true`

#### Scenario: A dry run changes nothing
- **WHEN** the sync is invoked with `dry_run=true`
- **THEN** no rows are ingested and the response reports `dry_run: true`

---

### Requirement: The Gmail poller only marks mail processed when ingestion fully succeeded

The Gmail poller SHALL resolve a sender to a tenant via the `gmail_sender_map` table, and SHALL
apply the `contexia-processed` label to a message ONLY when every supported attachment on it was
ingested successfully.

Mail from an unmapped sender SHALL be skipped and left unlabeled.

#### Scenario: Unmapped sender is retryable later
- **WHEN** mail arrives from a sender absent from `gmail_sender_map`
- **THEN** the message is skipped, left unlabeled, and is ingested on a later tick once the
  mapping exists — with no manual replay

#### Scenario: A partly failed message is retried
- **WHEN** one attachment on a message fails to ingest
- **THEN** the message is NOT labeled processed, so the next tick retries it

#### Scenario: The poller is inert without configuration
- **WHEN** `INTERNAL_API_KEY` or the Supabase credentials are unset
- **THEN** the poller logs an error and exits without contacting Gmail or Railway

#### Scenario: Sender mapping is tenant-isolated
- **WHEN** `gmail_sender_map` is read by an authenticated non-service caller
- **THEN** RLS restricts the rows to that caller's own tenant
