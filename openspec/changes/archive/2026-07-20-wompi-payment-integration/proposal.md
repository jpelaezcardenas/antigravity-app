## Why

Contexia currently has no way to collect real payments from PyME customers (subscription/billing) or process any Wompi-mediated transaction. Wompi (Bancolombia) sandbox credentials are already provisioned, so the backend can now be wired to create signed checkout transactions and receive/verify Wompi webhook events. Without this, no revenue flow can go live.

## What Changes

- Add a backend endpoint to create a Wompi checkout/transaction request for a `crm_leads` (Renta Natural) payment, signed using `WOMPI_INTEGRITY_SECRET` per Wompi's signature spec.
- Add a backend webhook endpoint that receives Wompi transaction-status events, verifies the event signature using `WOMPI_EVENTS_SECRET`, and rejects unverified requests.
- Wire real transaction state into the existing `crm_wompi_transactions` table (built by the archived `crm-b2c-sell-machine-cockpit` change specifically for this follow-up, "Change C") — no new payments table.
- Add `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET` as Railway env vars (sandbox values first; production values added later, never hardcoded).
- Add Stage 11 deployment tasks (commit, Railway env vars verified, production URL check, deployment report) per CLAUDE.md §8.

## Capabilities

### New Capabilities
- `wompi-payment-integration`: backend capability to create signed Wompi checkout transactions and to receive, verify, and process Wompi webhook events for the B2C Renta Natural lead funnel, writing real state into `crm_wompi_transactions`.

### Modified Capabilities
(none — no existing spec's requirements change; `crm-b2c-sell-machine-cockpit` is already archived and this change only adds new endpoints/columns, it does not alter that capability's existing requirements)

## Impact

- **Affected code**: `apps/backend/presentation/crm_endpoints.py` (new checkout + webhook routes), `apps/backend/services/crm_service.py` (new methods), `apps/backend/migrations` (additive migration on `crm_wompi_transactions`), `apps/backend/config.py` (new settings for Wompi keys).
- **New dependency**: Wompi REST API (sandbox: `https://sandbox.wompi.co`, production: `https://production.wompi.co`).
- **Infra**: new Railway env vars on `antigravity-app-production-175a`; new "URL de Eventos" registered in Wompi dashboard once the webhook endpoint is deployed.
- **Data**: additive migration on the existing `crm_wompi_transactions` table (unique index on `wompi_transaction_id`, widened `status` CHECK) — no schema-breaking change, already tenant-scoped via existing RLS.
