# Deployment Report — wompi-payment-integration

**Date:** 2026-07-20
**Deploy branch:** main
**Backend URL:** https://antigravity-app-production-175a.up.railway.app
**Environment:** Railway project `elegant-success`, service `antigravity-app`, environment `production` (the canonical `-175a` backend per ARCHITECTURE.md decision #9)

## Summary

Wired real Wompi (Bancolombia) checkout + webhook verification onto the existing `crm_wompi_transactions` table (built by the archived `crm-b2c-sell-machine-cockpit` change specifically for this follow-up, referred to there as "Change C"). Sandbox environment only — no production Wompi keys are configured or used.

## Commits

- `ce4c23a` — feat(wompi): real checkout + webhook for crm_wompi_transactions (Change C)
- `938dd16` — fix(wompi): translate postgrest single-row-not-found into 404, not 500 (hotfix, found via live smoke-test after first deploy)

## Deployments

| Deployment ID | Status | Notes |
|---|---|---|
| `b2445282-04fb-4c33-a6ee-957edabe83bd` | SUCCESS | Initial deploy of `ce4c23a`. Live smoke-test found a bug: checkout for an unknown lead returned 500 instead of 404. |
| `71c53eb2-b3ea-42e8-977b-39980ac4c9ac` | SUCCESS | Hotfix deploy of `938dd16`. Re-verified: checkout for an unknown lead now correctly returns 404. |

## What was completed automatically

- `apps/backend/config.py`: `WOMPI_ENV`, `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, `WOMPI_BASE_URL` settings, with `validate_wompi_config()` failing closed on sandbox/production key mismatch or missing production credentials. Wired into `main.py` startup.
- Railway env vars set (sandbox values, sourced from the founder's own Wompi sandbox dashboard, provided in-session): `WOMPI_ENV=sandbox`, `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, `WOMPI_BASE_URL`. Confirmed present via `railway_list_variables` after deploy.
- `apps/backend/services/wompi_signature.py`: pure functions for the checkout integrity signature and webhook event checksum verification, unit-tested.
- `apps/backend/services/crm_service.py`: `checkout_lead_payment()` (creates a signed Wompi checkout + `PENDING` transaction row) and `handle_wompi_webhook()` (verifies event signature, upserts transaction status, idempotent by `wompi_transaction_id`).
- `apps/backend/presentation/crm_endpoints.py`: `POST /api/v1/crm/leads/{lead_id}/checkout` and `POST /api/v1/crm/wompi/webhook`.
- `apps/backend/migrations/0025_wompi_webhook_columns.sql`: additive migration on `crm_wompi_transactions` (unique index on `wompi_transaction_id`, widened `status` CHECK to include `VOIDED`/`ERROR`). Applied directly to Supabase; `get_advisors` confirmed no new security/performance lint introduced.
- Full backend test suite run: 53/53 Wompi/CRM-related tests pass. 40 pre-existing unrelated failures (httpx/TestClient version mismatch, missing legacy-phase artifacts, Siigo CSV parser) confirmed unaffected by this change.
- Live production smoke-test: `POST /api/v1/crm/leads/does-not-exist/checkout` correctly returns `404 {"detail":"Lead 'does-not-exist' not found"}` after the hotfix.

## What still needs the founder's action (cannot be automated)

1. **Register the webhook URL in Wompi's sandbox dashboard** (Desarrollo → Programadores → "URL de Eventos"): `https://antigravity-app-production-175a.up.railway.app/api/v1/crm/wompi/webhook`. This requires the founder's own Wompi login session.
2. **Trigger one real Wompi sandbox test transaction end-to-end**: call the checkout endpoint for a real `crm_leads` row, complete payment on Wompi's hosted sandbox checkout page (requires a human on Wompi's UI — cannot be scripted), and confirm the webhook updates the corresponding `crm_wompi_transactions` row to `APPROVED` in production. This also closes task 6.2.

## Bug found and fixed during this deployment

Production smoke-testing (not just unit tests) caught a real bug: `postgrest-py`'s `.single().execute()` raises `APIError` when zero rows match, rather than returning `data=None` as the unit-test mocks assumed. This made checkout for an unknown lead return `500` instead of `404`. Fixed by catching `APIError` and translating it to the existing `LookupError → 404` path, with a regression test (`test_postgrest_single_row_not_found_error_becomes_lookup_error`) that reproduces the real raising behavior instead of the mocked one. Deployed as hotfix `938dd16` and re-verified live.

## Status

Change is **not yet fully closeable** — tasks 7.3 and 7.4 require the founder's manual action on Wompi's own UI. Once those are done, this change is ready to archive.
