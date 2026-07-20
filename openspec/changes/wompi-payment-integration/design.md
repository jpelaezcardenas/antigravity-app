## Context

Contexia's backend (`apps/backend`, FastAPI, Railway `antigravity-app-production-175a`) has no *real* payment capability today — only a manual HITL "approve payment" endpoint. Wompi sandbox keys are already provisioned in the Wompi dashboard (comercio "contexia"). Wompi's API model is: (1) client requests an *acceptance token*, (2) client/backend creates a *transaction* signed with an integrity signature derived from `WOMPI_INTEGRITY_SECRET`, (3) Wompi posts asynchronous webhook *events* to a registered URL, verified with an event signature derived from `WOMPI_EVENTS_SECRET`.

Critically, this repo already anticipated this work: the `crm-b2c-sell-machine-cockpit` change (archived) built a B2C lead funnel (`crm_leads`, Renta Natural tax-filing service) with a `crm_wompi_transactions` table whose own design doc names this exact follow-up as "Change C" — real Wompi checkout + webhook verification, replacing/backing the current manual `approve-payment` endpoint. Data must remain tenant-scoped, consistent with the existing `TenantContextMiddleware` + RLS pattern; `crm_wompi_transactions` already has `tenant_id` + admin-only RLS.

## Goals / Non-Goals

**Goals:**
- Create Wompi checkout transactions from the backend, correctly signed per Wompi's integrity-signature algorithm.
- Receive and cryptographically verify Wompi webhook events; reject any request whose signature doesn't match.
- Persist transaction lifecycle (pending → approved/declined/voided/error) per tenant.
- Keep sandbox and production credentials fully separated via env vars, never hardcoded.

**Non-Goals:**
- Frontend checkout UI/widget integration (separate follow-up change once backend contract is proven).
- Recurring billing / subscription management (Wompi subscriptions API) — out of scope for this first change.
- Production go-live — this change targets sandbox only; a follow-up change flips to production keys after sandbox is verified end-to-end.

## Decisions

- **REUSE `crm_wompi_transactions`, do not create a new table.** Discovered mid-implementation: this table already exists (migration `0022_crm_b2c_sell_machine.sql`, change `crm-b2c-sell-machine-cockpit`, archived) and its own design doc explicitly reserved it for this exact work: *"crm_wompi_transactions will eventually be written by a webhook handler (Change C)"*. Confirmed with the founder (2026-07-19) that this change IS that Change C. An earlier version of this design proposed a new generic `payment_transactions` table for tenant SaaS subscriptions — that was based on an incomplete premise (assumed no prior Wompi work existed) and is superseded by this decision. The actual first real Wompi use case in this repo is the B2C Renta Natural lead funnel (`crm_leads` → `crm_wompi_transactions`), not a generic per-tenant subscription table.
- **Additive migration only** (`0025_wompi_webhook_columns.sql`): the existing table's shape is otherwise correct (`reference` UNIQUE, `amount_cents`, `currency`, `wompi_transaction_id`, `wompi_raw_response`, tenant/lead FKs). Two gaps needed closing for real webhook writes: (1) `wompi_transaction_id` had no uniqueness constraint (needed for idempotent upsert on webhook redelivery) — added as a partial unique index (`WHERE wompi_transaction_id IS NOT NULL`, since it's null until Wompi assigns it); (2) the `status` CHECK only allowed `PENDING/APPROVED/DECLINED` (sufficient for manual HITL approval) but Wompi also sends `VOIDED`/`ERROR` — widened the CHECK.
- **Signature verification, not trust-by-URL**: the webhook endpoint MUST recompute the event signature (SHA-256 over the properties Wompi specifies + `WOMPI_EVENTS_SECRET`, per Wompi's checksum spec) and compare it before touching any state. Rationale: the webhook URL is public; without this, anyone could POST forged "approved" events.
- **Checkout/webhook endpoints mounted at `/api/v1/crm`**, alongside the existing `crm_endpoints.py` router (`presentation/crm_endpoints.py`, behind `CRM_CANONICAL`), not a new `/api/v1/payments/*` namespace — this keeps all CRM B2C lead-payment concerns in one place, consistent with how `advance-payment`/`approve-payment` already live there.
- **Webhook writes use the service-role Supabase client** (`get_service_supabase()`, already used elsewhere in `crm_service.py`), since `crm_wompi_transactions` RLS is `FOR ALL ... role = 'admin'` — a public webhook request has no admin user session, so it must go through the same controlled RLS-bypass pattern as other backend-only writes.
- **Idempotent webhook handling**: webhook events are upserted by Wompi's transaction `id` (now unique), since Wompi may retry delivery. Avoids duplicate-processing risk.
- **Settings via `apps/backend/config.py` (pydantic-settings)**: `WOMPI_PUBLIC_KEY`, `WOMPI_PRIVATE_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`, `WOMPI_ENV` (sandbox/production) added as required-in-production settings, consistent with how `ALLOWED_ORIGINS` and other secrets are already handled — never committed, sourced from Railway env vars. (Already implemented — see tasks 1.1–1.4.)
- **Sandbox base URL is explicit and env-driven**, not hardcoded to production, so the same code path works for both by only swapping env vars.

## Risks / Trade-offs

- [Risk] Forged webhook events if signature verification is skipped or implemented incorrectly → Mitigation: unit tests with known Wompi sample payload/signature pairs from Wompi docs; reject on any mismatch, log and return 401.
- [Risk] Wompi retries webhook delivery, causing duplicate processing → Mitigation: unique constraint on Wompi transaction ID + upsert semantics.
- [Risk] Sandbox/production key confusion (keys were briefly visible in this chat) → Mitigation: keys stored only in Bitwarden + Railway env vars; rotate before going live if any doubt about exposure; `WOMPI_ENV` setting fails closed if mismatched with key prefix (e.g. `pub_test_` used while `WOMPI_ENV=production`).
- [Risk] No tenant on the transaction if checkout is initiated without auth context → Mitigation: checkout endpoint requires an authenticated tenant session, same as other `/api/v1/*` endpoints.

## Migration Plan

1. Add sandbox Wompi settings to `config.py` with fail-closed validation (done — tasks 1.1–1.4).
2. Add Supabase migration widening `crm_wompi_transactions` for real webhook writes (done — `0025_wompi_webhook_columns.sql`, applied).
3. Implement checkout + webhook endpoints under `/api/v1/crm`, sandbox-only initially.
4. Deploy to Railway (Stage 11); register the resulting webhook URL as "URL de Eventos" in Wompi's sandbox dashboard.
5. Verify end-to-end with a Wompi sandbox test transaction before any production key is introduced.
6. Rollback: endpoints are additive to an existing router — disable by removing the new routes from `crm_endpoints.py` and/or unsetting Railway env vars; the `0025` migration is additive (new index, widened CHECK) and does not need a down-migration to be safe to leave in place even if the endpoints are rolled back.

## Open Questions

None outstanding. Confirmed with the founder (2026-07-19, initial scoping): this integration is ultimately for Contexia's own revenue collection. Refined mid-implementation (2026-07-19, after discovering `crm_wompi_transactions`): the concrete first use case already built into this repo is the B2C Renta Natural lead funnel — Contexia charging individual `crm_leads` for its tax-filing service — not a generic per-tenant SaaS subscription table. This change (Change C) wires that up; a generic subscription-billing capability, if still needed later, is a separate future change.
