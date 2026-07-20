# wompi-payment-integration Specification

## Purpose

Integrate Wompi as the payment processor for B2C Renta Natural checkout: create signed checkout transactions for `crm_leads`, verify and process Wompi webhook events, and manage Wompi credentials safely across environments.

## Requirements

### Requirement: Create signed Wompi checkout transaction for a lead
The backend SHALL expose an endpoint that creates a Wompi transaction for a `crm_leads` (B2C Renta Natural) payment, computing the integrity signature from `WOMPI_INTEGRITY_SECRET` per Wompi's checksum specification.

#### Scenario: Valid lead requests a checkout transaction
- **WHEN** a checkout is requested for a lead in stage `POR_APROBAR` (or the stage designated for pending payment) with a valid amount and currency
- **THEN** the backend creates or updates the lead's `crm_wompi_transactions` row with status `PENDING`, computes the correct integrity signature, and returns the data needed to redirect to Wompi checkout

#### Scenario: Unknown lead is rejected
- **WHEN** a checkout is requested for a `lead_id` that does not exist or does not belong to the caller's tenant
- **THEN** the backend SHALL return 404 and SHALL NOT create or modify any `crm_wompi_transactions` row

### Requirement: Verify Wompi webhook event signatures
The backend SHALL expose a webhook endpoint that receives Wompi transaction-status events and SHALL verify the event signature using `WOMPI_EVENTS_SECRET` before processing any event data.

#### Scenario: Valid signature updates transaction status
- **WHEN** Wompi posts an event whose computed signature matches the signature header
- **THEN** the backend upserts the corresponding `crm_wompi_transactions` row by `wompi_transaction_id` with the new status (`PENDING`/`APPROVED`/`DECLINED`/`VOIDED`/`ERROR`) and returns 200

#### Scenario: Invalid signature is rejected
- **WHEN** Wompi posts an event whose computed signature does NOT match the signature header
- **THEN** the backend SHALL NOT modify any `crm_wompi_transactions` row and SHALL return 401

#### Scenario: Duplicate event delivery is idempotent
- **WHEN** Wompi redelivers an event for a `wompi_transaction_id` already processed with the same status
- **THEN** the backend upserts without creating a duplicate row (enforced by the unique index on `wompi_transaction_id`) and returns 200

### Requirement: Webhook writes bypass RLS through the service-role client only
Since `crm_wompi_transactions` RLS restricts writes to admin users and a Wompi webhook request carries no user session, the webhook handler SHALL write using the backend's existing service-role Supabase client, never by relaxing the table's RLS policy.

#### Scenario: Webhook updates a transaction without an admin session
- **WHEN** a verified Wompi webhook event arrives with no `Authorization` header
- **THEN** the backend SHALL still be able to update the corresponding `crm_wompi_transactions` row via the service-role client, and the table's RLS policy SHALL remain admin-only for all other callers

### Requirement: Wompi credentials sourced from environment, never hardcoded
`WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, and `WOMPI_ENV` SHALL be read from environment variables (Railway) via `apps/backend/config.py` and SHALL fail closed if required variables are missing in a given environment.

#### Scenario: Missing required Wompi env var in production
- **WHEN** the backend starts with `WOMPI_ENV=production` and a required Wompi variable is unset
- **THEN** `validate_wompi_config()` SHALL raise, and the backend SHALL NOT start with a silently missing credential

#### Scenario: Sandbox/production key mismatch
- **WHEN** `WOMPI_ENV=sandbox` and a `pub_prod_`/`prv_prod_`-prefixed key is configured (or vice versa)
- **THEN** `validate_wompi_config()` SHALL raise and refuse startup
