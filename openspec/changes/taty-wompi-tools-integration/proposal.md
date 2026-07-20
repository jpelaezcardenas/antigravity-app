## Why

A plan-vs-build audit against the original Antigravity SOTA Sell Machine design found the single
most critical gap: `services/taty_lead_router.py`'s `generate_wompi_link`/`verify_wompi_transaction`
(Change D, archived) are still `NotImplementedError` stubs, explicitly deferred to "Change C" — but
Change C (`wompi-payment-integration`) has since been built, archived, and is now **live in
production** (`WOMPI_ENV=production`, confirmed on Railway). Nobody wired the stubs to the real
Wompi functions afterward. Today, a WhatsApp lead saying "ya pagué" gets told Taty can't confirm
payments automatically — the exact opposite of the autonomous BOFU loop the plan called for.

## What Changes

- `generate_wompi_link(lead_id)`: calls the existing, unmodified
  `CrmService.checkout_lead_payment(lead_id)` and builds a real, shareable Wompi **Web Checkout**
  URL (`https://checkout.wompi.co/p/?public-key=...&currency=...&amount-in-cents=...&reference=...
  &signature:integrity=...`) from its signed payload — no new signing logic, reuses the existing
  integrity signature computed by `checkout_lead_payment`.
- `verify_wompi_transaction(lead_id)`: reads the lead's `crm_wompi_transactions` row directly
  (already kept authoritative by the existing, unmodified webhook handler) — makes **no** new
  outbound HTTP call to Wompi.
- Wires both into `route_lead_message`:
  - `sales_interest` → generates (or reuses) a checkout link and includes it in Taty's reply,
    matching the original plan's Kanban column semantics ("PROSPECTOS: Link Wompi Enviado").
  - `payment_confirmation` → checks the real transaction status; `APPROVED` advances the lead to
    `POR_APROBAR` (still HITL-gated at `CrmService.approve_payment`, unmodified) and confirms
    receipt; `PENDING` asks the lead to wait; no transaction found says so honestly.
- Completes the other narrow half of the audit's persona-state gap: detects "es independiente" as
  `es_asalariado=False` (today only the `True` case is detected).

## Capabilities

### New Capabilities
(none — extends the existing `taty-whatsapp-sales-router` capability's behavior)

### Modified Capabilities
- `taty-whatsapp-sales-router`: the "payment-related tools are explicit stubs" requirement is
  superseded — `generate_wompi_link`/`verify_wompi_transaction` are now real, and the
  payment-confirmation reply changes from a fixed "not yet available" message to a real status
  check.

## Impact

- **Modified**: `apps/backend/services/taty_lead_router.py` only.
- **Untouched**: `crm_service.py`'s `checkout_lead_payment`/`handle_wompi_webhook` (reused exactly
  as-is), `crm_wompi_transactions` schema (no migration), `CrmService.approve_payment` (still the
  only path to `LISTOS_CONTADORA`).
- **No new Railway flag** — this extends existing WhatsApp-channel logic already gated by
  `WHATSAPP_CANONICAL` (live in production).
- **Explicitly out of scope**: RUT/extractos document collection (a separate future change — real
  design question of how a document arrives via WhatsApp, not a one-liner); any ReAct/LLM-reasoning
  rearchitecture of Taty (flagged to the founder as its own design conversation, not bundled here).
