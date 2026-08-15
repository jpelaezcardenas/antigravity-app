## Context

Confirmed live on Railway (`elegant-success` / `antigravity-app` / `production`) right now:
`WOMPI_ENV=sandbox`, `WOMPI_PUBLIC_KEY=pub_test_...`, `WOMPI_PRIVATE_KEY=prv_test_...`,
`WOMPI_INTEGRITY_SECRET=test_integrity_...`, `WOMPI_EVENTS_SECRET=test_events_...`,
`WOMPI_BASE_URL=https://sandbox.wompi.co/v1`. No production keys exist yet anywhere in this repo
or its deployed environment.

Re-read the live code before scoping this change:
- `apps/backend/config.py`'s `validate_wompi_config()` (called at startup, `main.py:29`) already
  fails closed: rejects an invalid `WOMPI_ENV`, rejects a sandbox-prefixed key when
  `WOMPI_ENV=production` (and vice versa), and requires all 4 credentials when
  `WOMPI_ENV=production`. This function needs zero changes — it was already written generically
  for both environments.
- `services/crm_service.py`'s `checkout_lead_payment(lead_id)` computes an integrity signature and
  returns `{public_key, currency, amount_in_cents, reference, signature}` — it makes **no outbound
  HTTP call to Wompi's API**. This is Wompi's **hosted Widget Checkout** model: the frontend takes
  this signed payload and redirects the browser to Wompi's checkout page, and Wompi itself
  determines sandbox vs. production purely from the `public_key` prefix (`pub_test_` vs.
  `pub_prod_`).
- `handle_wompi_webhook(event)` verifies the event's checksum against `WOMPI_EVENTS_SECRET` and
  writes to `crm_wompi_transactions` via the service-role Supabase client — same code path
  regardless of environment.
- **`WOMPI_BASE_URL` is referenced nowhere else in the codebase** (`grep` across
  `apps/backend/**/*.py` outside tests returns only its own declaration in `config.py`) — it is
  dead configuration, unrelated to the actual checkout flow. Confirmed, not assumed.

This means the entire "go-live" is credential provisioning + a config flip — genuinely zero code
to write, which is unusual for this repo's change history (every prior change had a TDD section).

## Goals / Non-Goals

**Goals:**
- Get real production Wompi credentials into Railway safely, verified by the existing fail-closed
  validation, without ever mixing sandbox/production keys.
- Register the production webhook in Wompi's dashboard (separate from the existing sandbox
  registration).
- Prove the cutover with exactly one real payment, performed by the founder — never by the agent.
- Leave a clear, explicit stopping point in `tasks.md` where execution must pause for a human
  financial action, rather than letting the change "flow through" that step implicitly.

**Non-Goals:**
- Any code change to `checkout_lead_payment`, `handle_wompi_webhook`, `validate_wompi_config`, or
  the endpoints — none are needed (see Context).
- Removing or fixing the dead `WOMPI_BASE_URL` config — out of scope for this change (it causes no
  harm and touching unrelated working code isn't warranted here); flagged as a minor follow-up
  opportunity only.
- Building any refund/dispute/reconciliation tooling — not requested, not scoped.

## Decisions

**1. Do not touch `WOMPI_BASE_URL`.**
Confirmed via `grep` that no backend code reads it. Updating it to a "production Wompi API base"
would be cargo-culting a value that has no effect — worse, it risks looking like a completed step
when it changes nothing. Left exactly as-is; noted in the deployment report as a "found but not
touched" observation for future cleanup.

**2. The real-money smoke test is an explicit founder checkpoint, not an agent-executed step.**
Every prior change in this session's Stage 11 pattern ends with the agent exercising the live
endpoint itself (curl, browser). That pattern is **not** appropriate here: completing a real Wompi
checkout means moving real money, which this agent will never execute or simulate on the user's
behalf (financial-transaction-execution is out of bounds regardless of who technically clicks
"pay"). `tasks.md`'s Stage 11 section explicitly stops and hands control to Juan David with a
concrete ask ("complete one real Renta Natural checkout with a real card, then give me the
resulting Wompi transaction reference"), and only resumes agent-driven verification (direct
Supabase SQL confirming the `crm_wompi_transactions` row) after he reports back.

**3. Reuse `validate_wompi_config()` as the acceptance gate, not a new check.**
Rather than writing new verification code, the go-live's "did this work" signal is simply: the
Railway deployment with the 4 new env vars boots successfully (proving `validate_wompi_config()`
passed) and the app answers requests. A failure here (mismatched key prefixes, a missing var)
surfaces as a startup crash — the exact fail-closed behavior the existing code was built for.

**4. No new OpenSpec capability requirements duplicate `wompi-payment-integration`'s.**
That spec's requirements (signed checkout creation, webhook signature verification, RLS-bypass via
service-role client, fail-closed env config) are behavior-level and hold identically in production.
This change's own spec is scoped narrowly to the go-live **process** itself (credential
provisioning checklist, production webhook registration, the real-payment verification checkpoint)
— it does not redefine or duplicate the code-level contract already specified.

## Risks / Trade-offs

- **[Risk] Real money moves during verification.** → Mitigation: exactly one transaction, performed
  by the founder himself, amount is the existing fixed `RENTA_NATURAL_PRICE_CENTS` (not
  agent-chosen), and the transaction is fully reversible/refundable through Wompi's own merchant
  tools if needed (outside this change's scope) — not a repo concern.
- **[Risk] Production webhook registration forgotten → payments succeed on Wompi's side but
  `crm_wompi_transactions` never updates from `PENDING`.** → Mitigation: `tasks.md` places webhook
  registration BEFORE the config flip and BEFORE the real-payment test, so this is caught before
  real money is involved, not after.
- **[Risk] Credentials pasted into a chat/log.** → Mitigation: instruct the founder to set them
  directly via `railway_set_variable` (values pass through the MCP tool call, not typed into chat
  as plain narrative) — same discipline as every prior credential-bearing change this session.

## Migration Plan

1. Founder obtains the 4 production Wompi credentials (manual, Wompi dashboard) and registers the
   production webhook URL (manual, Wompi dashboard) — both outside any tool's reach.
2. Agent sets the 4 Railway env vars + `WOMPI_ENV=production` via `railway_set_variable`, confirms
   the resulting deploy boots successfully (proving `validate_wompi_config()` passed).
3. **STOP — founder completes one real Renta Natural checkout with a real card** and reports the
   Wompi transaction reference back.
4. Agent confirms via direct Supabase SQL that the corresponding `crm_wompi_transactions` row is
   `APPROVED` with a real (non-`test_`) `wompi_transaction_id`.
5. Deployment report (noting the `WOMPI_BASE_URL` dead-config observation), archive.
- **Rollback**: revert the 4 env vars to their sandbox values (`WOMPI_ENV=sandbox` + the existing
  `pub_test_`/`prv_test_` keys, which remain valid and untouched) and redeploy — instant, no code
  or schema involved.

## Open Questions

- Should `WOMPI_BASE_URL` be removed from `config.py` as dead code in a future cleanup change?
  Deferred — not this change's scope.
