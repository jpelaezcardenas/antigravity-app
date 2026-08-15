## Why

The Wompi (Bancolombia) payment integration for the B2C Renta Natural 2026 funnel is fully built
and verified in sandbox (Change `wompi-payment-integration`, archived, two real sandbox payments
confirmed end-to-end). It cannot accept real money yet because Railway's production environment
still runs `WOMPI_ENV=sandbox` with `pub_test_`/`prv_test_` credentials. This change is the
production cutover: obtain real Wompi production credentials, configure them, and verify one real
payment — pure configuration/operations work, not a rebuild.

## What Changes

- **Founder-only manual steps** (cannot be executed by an agent): obtain the 4 production Wompi
  credentials from the Wompi merchant dashboard (production mode, not sandbox), and register the
  existing webhook URL in Wompi's **production** dashboard (a separate registration from the
  sandbox one already in place).
- Update 4 Railway production env vars: `WOMPI_ENV=production`, `WOMPI_PUBLIC_KEY` (`pub_prod_...`),
  `WOMPI_PRIVATE_KEY` (`prv_prod_...`), `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET` (all
  production-prefixed/valued). **`WOMPI_BASE_URL` is NOT touched** — confirmed by reading the
  codebase that no backend code references it; see design.md Decision 1.
- Rely entirely on the already-shipped `validate_wompi_config()` (`apps/backend/config.py`) to
  fail closed on any mismatch — no code changes to that function or any other.
- **One real-money transaction**, performed by the founder himself (never executed or simulated by
  the agent — a financial transaction is outside anything this agent will execute on the user's
  behalf), used as the live Stage 11 smoke test.
- **BREAKING**: none for existing sandbox testing — sandbox stays fully functional if `WOMPI_ENV`
  is ever reverted; this change only flips the live environment forward.

## Capabilities

### New Capabilities
- `wompi-production-go-live`: the operational go-live process and its verification checklist
  (credential provisioning, production webhook registration, config flip, live smoke test) —
  distinct from `wompi-payment-integration`'s existing code-level requirements, which this change
  does not modify.

### Modified Capabilities
(none — `wompi-payment-integration`'s requirements, including `validate_wompi_config()`'s fail-closed
behavior, hold unchanged in production; this change only supplies the production values that
requirement was designed to validate)

## Impact

- **Railway env vars** (project `elegant-success`, service `antigravity-app`, environment
  `production`): `WOMPI_ENV`, `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`,
  `WOMPI_EVENTS_SECRET` updated to production values.
- **Wompi dashboard** (external, founder-only): production webhook URL registration.
- **No code changes** — confirmed by re-reading `config.py`, `crm_service.py`'s
  `checkout_lead_payment`/`handle_wompi_webhook`, and `crm_endpoints.py`'s checkout/webhook routes.
- **No new tables/migrations** — reuses `crm_wompi_transactions` (Change B/C) as-is.
- **No frontend changes.**
- One real `crm_wompi_transactions` row will be created with a genuine (non-`test_`-prefixed)
  `wompi_transaction_id`, as the smoke-test artifact — the founder's own real payment, not a demo
  row like prior changes' harmless test data (this one involves real money, so its disposition is
  the founder's call, not left in place casually).
