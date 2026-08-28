## Context

Verified directly (not from the master plan's original assumption, which was corrected during
Subdomain 3's research) by reading `apps/backend/services/crm_service.py:207-292` and
`apps/backend/presentation/crm_endpoints.py:42-60` in full:

- `create_b2b_client` (`:207-253`) inserts a new `tenants` row (`nit`, `legal_name`,
  `is_cliente_cero: False`) and a new `b2b_clients` row, neither of which writes `plan_tier` —
  both silently rely on migration 0043's `DEFAULT 'starter'`.
- `_provision_b2b_client_login` (`:255-292`), invoked only when an email is supplied, creates a
  Supabase Auth user with `client.auth.admin.create_user({..., "password":
  secrets.token_urlsafe(12), ...})` — the password is generated, used once to satisfy the API
  call, and then discarded; its own docstring says "distribution is the founder's
  responsibility," but nothing in this repo or process actually distributes it. It also writes
  `"plan": "starter"` (hardcoded) to `usuarios.plan` — a separate, legacy per-user column,
  unrelated to `tenants.plan_tier`/`b2b_clients.plan_tier` (confirmed in Subdomain 3's
  investigation).
- `B2bRetainersTab.tsx`'s alta form (`:52-55, 100-123, 247-288`) collects `name`, `email`,
  `phone`, `monthly_fee_cents` only — no tier field exists anywhere in this component.
- The Python `gotrue` client (confirmed via direct inspection of the installed package) exposes
  `client.auth.admin.generate_link({"type": "invite", "email": ...})`, returning a
  `GenerateLinkResponse` with `.properties.action_link` (the link) and `.user` (the created
  Auth user) — `generate_link` creates the link without Supabase sending anything itself,
  unlike `invite_user_by_email`, which does send via whatever SMTP the project has configured.

## Goals / Non-Goals

**Goals:**
- Let a vendor pick a real tier at alta time, written consistently to every place a tier concept
  exists today (`tenants.plan_tier`, `b2b_clients.plan_tier`, and the legacy `usuarios.plan`).
- Replace the discarded password with something a vendor can actually hand to a client.
- Reuse Subdomain 3's tier vocabulary and defaults — no second source of truth for tier names.

**Non-Goals:**
- No pricing numbers anywhere in code (master plan's explicit rule, carried over from Subdomain 3).
- Not verifying or configuring Supabase's SMTP — sidestepped entirely by using `generate_link`
  (no email sent by Supabase) instead of `invite_user_by_email` (would send one), per Decision D3
  below. The master plan's open question ("verify SMTP before trusting automatic Supabase
  sending") is resolved by not depending on Supabase sending at all.
- Not building a dedicated backend endpoint for the tier list — 4 static values, reused as a
  plain constant on both sides, matching the existing pattern (`PLAN_TIER_LABEL` in
  `TenantInfoCard.tsx`, Subdomain 3).
- Not touching baja/reactivar, pago, or contacto flows — alta only.

## Decisions

**D1 — `plan_tier` param on `create_b2b_client`, default `"starter"`, written explicitly.**
Matches migration 0043's own default so an alta with no tier selected behaves identically to
today (no regression for the existing workflow if a vendor ignores the new field). Written
explicitly to both `tenants.plan_tier` and `b2b_clients.plan_tier` at insert time rather than
left to the column default, so the alta response can honestly report the tier that was actually
chosen instead of inferring it. Values validated against the same 4 the migration's `CHECK`
constraint and `core/plan_features.py`'s `PLAN_FEATURES` map already define
(`freemium|starter|growth|enterprise`) — an invalid value raises before either insert, consistent
with the DB-level `CHECK` that would reject it anyway (fail fast in the service layer with a
clear error, not a raw Postgres constraint violation surfacing to the vendor).

**D2 — `_provision_b2b_client_login` also receives `plan_tier`, writes it to `usuarios.plan`
instead of hardcoding `"starter"`.** Closes the exact gap Subdomain 3's design.md flagged as an
open question: `usuarios.plan` and `tenants.plan_tier` are two different columns for the same
concept, and only one of them was being set correctly. This does not unify or deprecate
`usuarios.plan` (out of scope — see Non-Goals) — it just stops the two from silently diverging at
the one point where both are written in the same request.

**D3 — `generate_link(type="invite")`, not `invite_user_by_email`, not a discarded password.**
Alternatives considered:
- Keep the discarded password: rejected — this is the exact problem being fixed; a password
  nobody sees is equivalent to a client who can never log in.
- `invite_user_by_email`: rejected for now, because it depends on the Supabase project's SMTP
  configuration being correctly set up and reliable, which the master plan itself flagged as
  unverified. Sending a broken invite email silently would be worse than the current state (at
  least today everyone knows logins don't work yet).
- `generate_link(type="invite")` (chosen): creates the Auth user exactly like
  `invite_user_by_email` would, but returns the `action_link` to the caller instead of emailing
  it — Supabase sends nothing, so there is no SMTP dependency to verify. The link is surfaced in
  the API response (`invite_link`) for the vendor to paste into WhatsApp or email manually — the
  same "distribution is the vendor's responsibility" policy the code already documented, now with
  a link that actually works instead of a password that was never seen.

**D4 — Tier selector in the frontend is a plain constant array, not a new endpoint.** Four fixed
values, mirroring `core/plan_features.py`'s keys exactly (kept in sync by a comment referencing
that file, same pattern already used by `TenantInfoCard.tsx`'s `PLAN_TIER_LABEL` map from
Subdomain 3) — a dedicated `GET /api/v1/plan-tiers` endpoint would be over-engineering for 4
values that change rarely and require a backend deploy to add a 5th anyway.

## Risks / Trade-offs

- [Risk] A vendor could still ignore the tier selector and everything defaults to `starter`,
  same as today — no different from the current UX gap, not a regression. → Mitigation: none
  needed; this is acceptable, the selector makes the correct choice possible, not mandatory.
- [Risk] `generate_link` requires the caller to actually deliver the link somewhere (WhatsApp,
  email, etc.) — if the vendor forgets, the client still can't log in, same failure mode as
  today's discarded password, just now avoidable. → Mitigation: the UI surfaces the link
  immediately and prominently after a successful alta so it's hard to miss, per D5 below (frontend
  task).
- [Risk] `generate_link` and `create_user` behave slightly differently if the email already has an
  existing Auth user (e.g. a re-provisioning attempt) — `generate_link` for an existing user
  returns a link for that user rather than erroring the way `create_user` would on a duplicate
  email. → Mitigation: this is an improvement, not a regression — a retried alta for an
  already-provisioned email now degrades gracefully into "here's a fresh login link for the
  existing account" instead of a hard 500.

## Migration Plan

No new migration — `tenants.plan_tier`, `b2b_clients.plan_tier` already exist (migration 0043).
Deploy is backend (2 service methods + 1 endpoint) + frontend (1 form + 1 API client) together,
since the frontend's new `plan_tier` field would otherwise be silently dropped by the backend if
shipped alone. Rollback: revert both commits together; no data migration to undo (no schema
change in this subdomain).

## Open Questions

- [FOUNDER ACTION, carried from Subdomain 3] Confirm the 4 tier names match the eventual real
  pricing tiers — unchanged by this subdomain.
- [ENGINEERING, deferred] Whether `usuarios.plan` should eventually be deprecated in favor of
  `tenants.plan_tier` entirely — this subdomain only stops the two from diverging at write time,
  it doesn't unify them.
