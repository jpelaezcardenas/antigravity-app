## ADDED Requirements

### Requirement: Production Wompi credentials are validated before accepting real payments
The system SHALL refuse to start with `WOMPI_ENV=production` unless all four production Wompi
credentials (`WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`,
`WOMPI_EVENTS_SECRET`) are set and correctly prefixed for production
(`pub_prod_`/`prv_prod_`), reusing the existing `validate_wompi_config()` unmodified.

#### Scenario: Production deploy with correct credentials boots successfully
- **WHEN** Railway's production environment is configured with `WOMPI_ENV=production` and all four
  production-prefixed credentials
- **THEN** the backend starts successfully and `GET /api/v1/crm/leads/{lead_id}/checkout`-driven
  flows use the production credentials

#### Scenario: A leftover sandbox-prefixed key blocks production startup
- **WHEN** `WOMPI_ENV=production` is set but `WOMPI_PUBLIC_KEY` or `WOMPI_PRIVATE_KEY` still carries
  a `pub_test_`/`prv_test_` prefix
- **THEN** the backend SHALL refuse to start (existing `validate_wompi_config()` behavior)

### Requirement: The production webhook is registered separately from the sandbox webhook
The same webhook URL (`/api/v1/crm/wompi/webhook`) SHALL be registered in Wompi's production
dashboard as a distinct registration from the existing sandbox registration, so production
transaction-status events are delivered once production credentials are live.

#### Scenario: A production transaction's webhook event is received
- **WHEN** a real production Wompi transaction changes status
- **THEN** Wompi delivers the event to the same `/api/v1/crm/wompi/webhook` endpoint, which
  verifies it against `WOMPI_EVENTS_SECRET` (production value) and updates
  `crm_wompi_transactions` accordingly (existing, unmodified behavior)

### Requirement: The go-live is verified with exactly one real transaction, performed by a human
The go-live process SHALL be verified by one real Renta Natural payment completed by an authorized
human operator (never executed, simulated, or fabricated by an automated agent), with its
resulting `crm_wompi_transactions` row confirmed `APPROVED` with a genuine (non-`test_`-prefixed)
`wompi_transaction_id`.

#### Scenario: A real payment lands correctly in the database
- **WHEN** a human operator completes one real Renta Natural checkout with production credentials
  live
- **THEN** a `crm_wompi_transactions` row exists with `status="APPROVED"` and a
  `wompi_transaction_id` that is not `test_`-prefixed
