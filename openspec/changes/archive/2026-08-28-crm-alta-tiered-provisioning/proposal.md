## Why

Subdomain 4 of the freemium-onboarding master plan, depends on Subdomain 3
(`plan-tier-feature-gating`, archived). The B2B "Alta" flow
(`B2bRetainersTab.tsx` → `POST /api/v1/crm/b2b/clients` →
`CrmService.create_b2b_client`) already provisions a new tenant + client row + best-effort
login end to end, but it hardcodes every new client to the `starter` tier implicitly (via
migration 0043's column default — it never writes `plan_tier` explicitly) and discards a random
password that no one ever delivers to the client, so nobody has actually logged in. This blocks
onboarding a freemium client with the correct tier from day one.

## What Changes

- `CrmService.create_b2b_client` gains a `plan_tier` parameter (default `"starter"`, validated
  against the same 4 values `core/plan_features.py` defines), written explicitly to both
  `tenants.plan_tier` and `b2b_clients.plan_tier` at insert time — no longer relying on the
  column's default.
- `CrmService._provision_b2b_client_login` also receives `plan_tier` and writes it to
  `usuarios.plan` instead of the hardcoded `"starter"` string, closing the reconciliation gap
  Subdomain 3 flagged between this legacy per-user column and the new per-tenant `plan_tier`.
- Replaces the discarded random password with `client.auth.admin.generate_link(type="invite")`:
  no email is sent by Supabase (avoids depending on unverified SMTP configuration); the returned
  `action_link` is surfaced in the API response as `invite_link` for the vendor to copy and send
  manually (WhatsApp/email) — same "manual distribution" policy as before, now with an actual
  usable artifact instead of a value nobody ever sees.
- `B2bRetainersTab.tsx`'s alta form gains a tier selector (freemium/starter/growth/enterprise),
  and displays the returned `invite_link` after a successful alta with an email, so the vendor can
  copy it immediately.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `crm-b2b-retainers`: the B2B alta requirement gains an explicit `plan_tier` input and an
  invite-link response field, replacing the discarded-password behavior.

## Impact

- Backend: `apps/backend/services/crm_service.py` (`create_b2b_client`,
  `_provision_b2b_client_login`), `apps/backend/presentation/crm_endpoints.py`
  (`CreateB2bClientRequest`).
- Frontend: `contexia-app/lib/crm-api.ts` (`CreateB2bClientInput`, `B2bClient`),
  `contexia-app/components/bunker/crm/B2bRetainersTab.tsx` (tier selector + invite-link display).
- Does not touch `tenants`/`b2b_clients`/`usuarios` schema (columns already exist from Subdomain 3
  and prior migrations) — no new migration needed.
- Does not touch the alta form's other fields (email/phone/fee) or the baja/pago/contacto flows.
- No pricing numbers introduced — tier names only, consistent with the master plan.
