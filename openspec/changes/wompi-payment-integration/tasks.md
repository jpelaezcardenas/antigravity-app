## 1. Configuration and secrets

- [x] 1.1 Add `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, `WOMPI_ENV`, `WOMPI_BASE_URL` to `apps/backend/config.py` (pydantic-settings), typed, no defaults for secrets in production.
- [x] 1.2 Write a failing test asserting the app fails closed (payment endpoints return 503, or startup fails) when a required Wompi var is missing while `WOMPI_ENV=production`; implement until it passes.
- [x] 1.3 Write a failing test asserting startup rejects a `pub_prod_`/`prv_prod_`-prefixed key when `WOMPI_ENV=sandbox`; implement until it passes.
- [x] 1.4 Set sandbox values for all 5 vars in Railway (`antigravity-app-production-175a`), sourced from Bitwarden (not pasted in chat/commits).

## 2. Data model

> Scope correction (2026-07-19): `crm_wompi_transactions` already exists (change `crm-b2c-sell-machine-cockpit`, archived), built specifically for this follow-up ("Change C"). No new table — see design.md Decisions.

- [x] 2.1 Write additive Supabase migration on `crm_wompi_transactions`: unique index on `wompi_transaction_id` (idempotent upsert) + widen `status` CHECK to include `VOIDED`/`ERROR`.
- [x] 2.2 Apply the migration to Supabase (`0025_wompi_webhook_columns.sql`) and confirm via `get_advisors` that no new security/performance lint was introduced.

## 3. Checkout transaction endpoint

- [x] 3.1 Write a failing test: checkout requested for a valid `lead_id` with amount/currency → `crm_wompi_transactions` row upserted with status `PENDING`, correct integrity signature returned.
- [x] 3.2 Write a failing test: checkout requested for an unknown/foreign-tenant `lead_id` → 404, no row created or modified.
- [x] 3.3 Implement the integrity-signature computation (`SHA256(reference + amountInCents + currency + integritySecret)` per Wompi's checksum spec) as a small pure function with its own unit test using a known input/output pair from Wompi docs.
- [x] 3.4 Implement the checkout endpoint in `presentation/crm_endpoints.py` (`POST /leads/{lead_id}/checkout`) + `services/crm_service.py` method, until tests from 3.1–3.2 pass.

## 4. Webhook endpoint

- [x] 4.1 Write a failing test: valid-signature Wompi event payload → corresponding `crm_wompi_transactions` row upserted by `wompi_transaction_id` with new status, 200 returned.
- [x] 4.2 Write a failing test: invalid-signature payload → no row modified, 401 returned.
- [x] 4.3 Write a failing test: same event delivered twice (idempotency) → no duplicate row (unique index from 2.1 enforces this), still 200.
- [x] 4.4 Implement the event-signature verification function with its own unit test using a known Wompi sample payload/signature pair.
- [x] 4.5 Implement the webhook endpoint in `presentation/crm_endpoints.py` (`POST /wompi/webhook`), writing via the service-role Supabase client, until tests from 4.1–4.3 pass.

## 5. RLS / access verification

- [x] 5.1 Write a failing test confirming a non-admin/foreign-tenant caller cannot read or write another tenant's `crm_wompi_transactions` rows through the checkout/webhook code paths → implement/verify existing RLS + service-role usage enforces this correctly. (crm_service uses the service-role client throughout — no per-request end-user session, matching this file's existing convention — so the property that actually matters is that tenant_id is always DB-sourced from the lead's own row and never accepted as caller/webhook input; verified in test_crm_wompi_tenant_scoping.py.)

## 6. Local verification

- [x] 6.1 Run full backend test suite: `python -m pytest tests/` — 53/53 Wompi/CRM tests pass; 40 pre-existing unrelated failures (httpx/TestClient version mismatch, missing legacy-phase artifacts, Siigo CSV parser) confirmed unaffected by this change (none reference wompi/crm).
- [ ] 6.2 Manually exercise the checkout endpoint against Wompi sandbox (using the sandbox keys already in Railway) and confirm a real sandbox transaction is created against a test `crm_leads` row. (Deferred to 7.4 — a real end-to-end transaction needs the webhook to be reachable at a public URL, which only exists after deploy.)

## 7. Stage 11. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [x] 7.1 git commit + push to main (ce4c23a, hotfix 938dd16)
- [x] 7.2 Railway deploy active with all Wompi sandbox env vars verified present (deployment 71c53eb2, status SUCCESS post-hotfix; WOMPI_ENV=sandbox + 4 sandbox-prefixed keys confirmed via railway_list_variables; live smoke-test confirms checkout endpoint returns 404, not 500, for an unknown lead)
- [ ] 7.3 **USER ACTION REQUIRED** — Register the deployed webhook URL (`https://antigravity-app-production-175a.up.railway.app/api/v1/crm/wompi/webhook`) as "URL de Eventos" in the Wompi sandbox dashboard (Desarrollo → Programadores). Cannot be automated — requires the founder's Wompi login session.
- [ ] 7.4 **USER ACTION REQUIRED** — Trigger one real Wompi sandbox test transaction end-to-end (needs a real `crm_leads` row + completing Wompi's hosted checkout page, which requires a human on Wompi's UI) and confirm the webhook updates `crm_wompi_transactions` status in production. Also closes 6.2.
- [x] 7.5 Create report: `openspec/changes/wompi-payment-integration/reports/2026-07-20-deployment.md`
