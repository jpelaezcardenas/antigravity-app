## Context

Re-confirmed by reading the live source directly:
- `CrmService.checkout_lead_payment(lead_id)` (`crm_service.py:277`) creates a `PENDING`
  `crm_wompi_transactions` row and returns `{public_key, currency, amount_in_cents, reference,
  signature}` — data for Wompi's **Widget Checkout** (a JS embed), not a URL. There is no backend
  HTTP call to Wompi's REST API anywhere in this repo (confirmed via grep in an earlier session).
- Wompi's documented **Web Checkout** format is a hosted page that accepts exactly these same
  signed fields as URL query params: `public-key`, `currency`, `amount-in-cents`, `reference`,
  `signature:integrity` (plus optional `redirect-url`). This is the correct mechanism for a
  WhatsApp-shareable link — a widget embed cannot be sent as plain text.
- `crm_wompi_transactions` columns (confirmed live via Supabase MCP): `id, tenant_id, lead_id,
  reference, amount_cents, currency, status, wompi_transaction_id, wompi_raw_response,
  customer_email, customer_phone, customer_name, approved_by, approved_at, created_at, updated_at`.
- `CrmService.handle_wompi_webhook(event)` (`crm_service.py:326`) verifies the event checksum, then
  **UPDATEs by reference** the `crm_wompi_transactions` row with the real status
  (`PENDING/APPROVED/DECLINED/VOIDED/ERROR`, per the `wompi-payment-integration` spec). This means
  the local database already holds the authoritative, signature-verified transaction state by the
  time anyone asks — a second live API call to Wompi would be redundant and riskier (new
  credential-dependent code path this repo doesn't need).
- `route_lead_message` today: `sales_interest` only advances the stage and sends a generic reply
  (no link); `payment_confirmation` always sends a fixed "not available" reply without checking
  anything (the stubs always raised, so nothing ever called them).

## Goals / Non-Goals

**Goals:**
- Give Taty a real, shareable Wompi checkout link for `sales_interest`.
- Give Taty a real, honest payment-status check for `payment_confirmation`, sourced from the
  already-trusted local `crm_wompi_transactions` table.
- Avoid spamming a new `PENDING` checkout row on every message from the same lead.
- Keep the HITL gate intact: `payment_confirmation` → `APPROVED` only advances to `POR_APROBAR`
  (review-ready), never all the way to `LISTOS_CONTADORA` — that remains
  `CrmService.approve_payment`'s job, unmodified.

**Non-Goals:**
- RUT/extractos document collection — a separate, larger design question (how a document arrives
  via WhatsApp-only automation), explicitly deferred to a future change.
- Any ReAct/LLM-reasoning rearchitecture of Taty's intent classification — flagged to the founder
  as its own decision, not silently bundled here.
- A new outbound Wompi API call to "verify" a transaction — the webhook is the trusted source of
  truth; re-querying Wompi directly is unnecessary and out of scope.
- `topes`/`rut_status`/`extractos_status`/`obligado_declarar` persona fields — need real document
  data, not detectable from conversational text alone.

## Decisions

**1. `generate_wompi_link` builds a Web Checkout URL from `checkout_lead_payment`'s existing
signed payload — no new signing logic.**
`urlencode({"public-key": ..., "currency": ..., "amount-in-cents": ..., "reference": ...,
"signature:integrity": ...})` appended to `https://checkout.wompi.co/p/`. Reuses
`compute_integrity_signature` indirectly (via `checkout_lead_payment`, which already calls it) —
never recomputes a signature independently, avoiding any risk of a signing-logic drift between two
call sites.

**2. Reuse an existing `PENDING` transaction instead of creating a new one on every message.**
Before calling `checkout_lead_payment`, `generate_wompi_link` checks whether the lead already has a
`crm_wompi_transactions` row with `status='PENDING'` created recently (reuse it — return a
Web Checkout URL built from that row's existing `reference`/`amount_cents`/`currency`, recomputing
only the signature since `WOMPI_INTEGRITY_SECRET` is available server-side) rather than always
inserting a fresh row. This avoids a lead re-triggering "quiero declarar" mid-conversation from
generating a pile of abandoned `PENDING` rows. A new row is only created when no `PENDING` (or
later) transaction exists yet for that lead.

**3. `verify_wompi_transaction` reads `crm_wompi_transactions` directly — zero new Wompi API
calls.**
`SELECT * FROM crm_wompi_transactions WHERE lead_id = ? ORDER BY created_at DESC LIMIT 1` (isolated
in a `_get_latest_transaction(lead_id)` helper, matching the existing `_get_lead_stage` isolation
pattern in this file for clean test patching). Returns `{"status": ..., "wompi_transaction_id":
...}` or a "not found" shape if no row exists. The webhook (existing, unmodified) is what keeps
this row's `status` current — `verify_wompi_transaction` never second-guesses it.

**4. `payment_confirmation` → `APPROVED` advances to `POR_APROBAR`, not `LISTOS_CONTADORA`.**
`POR_APROBAR` is the existing stage a human reviews at the Búnker's "Aprobar Pago" HITL gate. Only
`CrmService.approve_payment` (unmodified) can move a lead to `LISTOS_CONTADORA`. This keeps the
autonomous verification loop strictly upstream of the human gate, per the original plan's own BOFU
description ("tu única intervención es hacer clic en Transferir a Contadora").

**5. `_detect_persona_fields` gains an "independiente" keyword set for `es_asalariado=False`.**
Narrow, symmetric addition to the existing `es_asalariado=True` detection — no new data model, no
migration.

## Risks / Trade-offs

- **[Risk] A generated Web Checkout link is untested against a real completed payment in this
  change** (Section 5's real-money smoke test already happened in `wompi-production-go-live`).
  → Mitigation: this change's live verification confirms the URL shape and a recomputable
  signature, and that a real `PENDING` row is created correctly — not a second full payment
  end-to-end, which isn't needed again.
- **[Risk] Reusing a stale `PENDING` transaction forever if a lead never completes payment.** →
  Mitigation: out of scope for this change (no TTL/expiry logic) — acceptable since Wompi checkout
  links themselves expire server-side; a future change can add explicit staleness handling if it
  becomes a real problem.
- **[Risk] `generate_wompi_link`'s live smoke test creates a real `PENDING` row against production
  Wompi.** → Mitigation: no real money moves for generating a signed URL (payment only happens if
  a card is actually charged on Wompi's hosted page, which the smoke test won't do) — same
  precedent as every other harmless demo row left in this session's Stage 11 verifications.

## Migration Plan

1. TDD in `taty_lead_router.py` + `test_taty_lead_router.py`, no new tables/migrations.
2. Stage 11: commit, merge, verify Railway deploy green (no new flag — reuses `WHATSAPP_CANONICAL`,
   already live). Live smoke test: create a test lead, call `generate_wompi_link` for real (hits
   the live `checkout_lead_payment` against production Wompi credentials), confirm the returned URL
   has the correct query-param shape and a signature that recomputes identically from the same
   inputs; call `verify_wompi_transaction` against that same lead and confirm it reports `PENDING`
   (no payment was made); confirm via direct Supabase SQL that exactly one `crm_wompi_transactions`
   row was created (not duplicated by re-calling `generate_wompi_link` again for the same lead).
3. Deployment report (noting the real `PENDING` row created during verification), archive.
- **Rollback**: revert `taty_lead_router.py` to the stub versions — no data/schema impact either
  way.

## Open Questions

- Should stale `PENDING` transactions eventually be cleaned up or re-generated with a fresh
  reference after some TTL? Deferred — not a problem yet at this business's volume.
