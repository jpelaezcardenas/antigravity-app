# Deployment Report — wompi-payment-integration

**Date:** 2026-07-20
**Deploy branch:** main
**Backend URL:** https://antigravity-app-production-175a.up.railway.app
**Environment:** Railway project `elegant-success`, service `antigravity-app`, environment `production` (the canonical `-175a` backend per ARCHITECTURE.md decision #9)

## Summary

Wired real Wompi (Bancolombia) checkout + webhook verification onto the existing `crm_wompi_transactions` table (built by the archived `crm-b2c-sell-machine-cockpit` change specifically for this follow-up, referred to there as "Change C"). Sandbox environment only — no production Wompi keys are configured or used. Verified fully end-to-end with a real Wompi sandbox payment.

## Commits

- `ce4c23a` — feat(wompi): real checkout + webhook for crm_wompi_transactions (Change C)
- `938dd16` — fix(wompi): translate postgrest single-row-not-found into 404, not 500 (hotfix #1, found via live smoke-test)
- `7ad44ae` — fix(wompi): webhook writes via update-by-reference, not upsert (hotfix #2, found via a real Wompi sandbox webhook)
- `23bab8c` — docs(wompi): Stage 11 deployment report + tasks.md status update

## Deployments

| Deployment ID | Status | Notes |
|---|---|---|
| `b2445282-04fb-4c33-a6ee-957edabe83bd` | SUCCESS | Initial deploy of `ce4c23a`. Live smoke-test found bug #1: checkout for an unknown lead returned 500 instead of 404. |
| `71c53eb2-b3ea-42e8-977b-39980ac4c9ac` | SUCCESS | Hotfix deploy of `938dd16`. Re-verified: checkout for an unknown lead now correctly returns 404. |
| `32202b0d-db16-4876-96f1-93d4cca04d50` | SUCCESS | Deploy of docs commit `23bab8c`. The founder's real Wompi sandbox payment landed here — surfaced bug #2 (webhook signature verified correctly, but the DB write failed). |
| `eae3a6fc-66b8-4423-b4dd-5f7818f058fe` | SUCCESS | Hotfix deploy of `7ad44ae`. Verified by replaying the same real transaction's webhook event — write now succeeds. |

## What was completed automatically

- `apps/backend/config.py`: `WOMPI_ENV`, `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, `WOMPI_BASE_URL` settings, with `validate_wompi_config()` failing closed on sandbox/production key mismatch or missing production credentials. Wired into `main.py` startup.
- Railway env vars set (sandbox values, sourced from the founder's own Wompi sandbox dashboard): `WOMPI_ENV=sandbox`, `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, `WOMPI_BASE_URL`. Confirmed present via `railway_list_variables`.
- `apps/backend/services/wompi_signature.py`: pure functions for the checkout integrity signature and webhook event checksum verification. **Independently validated against a real Wompi webhook payload** — the signature check passed on the first real delivery, confirming the checksum algorithm exactly matches Wompi's actual implementation.
- `apps/backend/services/crm_service.py`: `checkout_lead_payment()` (creates a signed Wompi checkout + `PENDING` transaction row) and `handle_wompi_webhook()` (verifies event signature, updates transaction status by `reference`, idempotent on redelivery).
- `apps/backend/presentation/crm_endpoints.py`: `POST /api/v1/crm/leads/{lead_id}/checkout` and `POST /api/v1/crm/wompi/webhook`.
- `apps/backend/migrations/0025_wompi_webhook_columns.sql`: additive migration on `crm_wompi_transactions` (unique index on `wompi_transaction_id`, widened `status` CHECK to include `VOIDED`/`ERROR`). Applied directly to Supabase; `get_advisors` confirmed no new security/performance lint introduced.
- Full backend test suite: 56/56 Wompi/CRM-related tests pass (after hotfix regression tests added). 40 pre-existing unrelated failures (httpx/TestClient version mismatch, missing legacy-phase artifacts, Siigo CSV parser) confirmed unaffected by this change.
- **Full end-to-end verification with a real transaction**: the founder registered the webhook URL in Wompi's sandbox dashboard (Desarrollo → Programadores → "URL de Eventos") and completed a real $89.000 COP sandbox payment via Wompi's hosted checkout, for lead "Ana SEED (Por Aprobar)" (`crm_leads.id=4d500757-27c9-40b1-b9f6-27afe30fc230`). Final confirmed state in `crm_wompi_transactions`: `status=APPROVED`, `wompi_transaction_id=12141585-1784507850-60928`, same row updated throughout (no duplicates).

## Bugs found and fixed during this deployment

Both were caught by testing against the real, deployed system — not just unit tests — which is exactly what Stage 11 verification is for.

1. **Checkout 500 instead of 404 for an unknown lead.** `postgrest-py`'s `.single().execute()` raises `APIError` when zero rows match, rather than returning `data=None` as the unit-test mocks assumed. Fixed by catching `APIError` and translating it to the existing `LookupError → 404` path. Regression test: `test_postgrest_single_row_not_found_error_becomes_lookup_error`. Hotfix `938dd16`.
2. **Webhook signature verified correctly but the DB write failed** (`23502` NOT NULL violation on `tenant_id`), found via the founder's real Wompi sandbox payment. Root cause: the webhook handler used `upsert(payload, on_conflict="reference")` with a payload that omitted `tenant_id`. Postgres validates NOT NULL constraints on the proposed row for `INSERT ... ON CONFLICT DO UPDATE` *before* resolving the conflict — even though the conflict path was always going to be taken, since `checkout_lead_payment()` guarantees the row already exists by the time a webhook for it arrives. Fixed by switching to a plain `UPDATE ... WHERE reference = ...`, which needs no NOT NULL columns and is naturally idempotent on redelivery. Verified by replaying the real transaction's exact webhook event (same `wompi_transaction_id`, `status`, `amount_in_cents`, `reference`) after the fix deployed — confirmed 200 response and `status=APPROVED` persisted in Supabase. Hotfix `7ad44ae`.

## Status

**All 23/23 tasks complete.** This change is fully verified end-to-end in production (sandbox) and ready to archive.
