## Why

A live test message ("quiero saber si me toca declarar renta") just proved, against real production
infrastructure, that `route_lead_message`'s `sales_interest` branch generates a real Wompi
checkout link (`WOMPI_ENV=production`, `pub_prod_...`) and sends it to the customer's real
WhatsApp number **with zero human review**. This is not a new bug — `taty-wompi-tools-integration`
built this behavior deliberately — but today was the first time it reached a real phone, and it
surfaced two risks the architecture/legal review from this same line of work had already flagged
and left unresolved:

1. **Merchant-of-record risk (critical).** The founder confirmed live that the Wompi account
   behind `WOMPI_PUBLIC_KEY` is registered to **Contexia (Entidad B, the tech company)**, not the
   regulated accounting firm (Entidad A). Every link this flow sends bills a "Renta Natural"
   accounting-service fee to Contexia's own merchant account — the exact scenario the earlier
   legal analysis ranked as the single highest-severity risk in this whole line of work: it
   creates a DIAN-registered factura electrónica of a non-JCC-inscribed tech SAS billing
   accounting fees, which the company's own ground truth says must never happen.
2. **No human-in-the-loop gate.** Nothing between "customer says a sales keyword" and "real payment
   link sent" is reviewed by anyone. The `approval_queue` HITL mechanism already exists and is
   already used for `tax_correction` drafts — it was simply never wired into this specific path.

Fixing risk 1 (which Wompi account should actually be used) is a business/ops action outside this
change's scope — it requires the founder to set up and verify a merchant account for Entidad A.
This change fixes risk 2, which is fully within engineering's control today and, as a side effect,
acts as an immediate safety brake on risk 1: no link goes out — under either entity's account —
without a human confirming it first.

## What Changes

- `route_lead_message`'s `sales_interest` branch no longer calls `generate_wompi_link` or sends
  anything directly. It enqueues a `wompi_payment_link` draft into the existing `approval_queue`
  table and replies to the customer that an advisor will follow up — no link, no amount, no
  merchant name in that reply.
- `ApprovalQueueService.approve_draft` gains a branch for `draft_type == "wompi_payment_link"`:
  on human approval, it generates the real Wompi link (unmodified `generate_wompi_link`) and
  delivers it via the existing `channels/whatsapp.py::send_whatsapp_message`, using the lead's
  phone recorded in the draft's payload. A delivery failure here does not roll back the approval
  (mirrors the existing "vectorization failure doesn't roll back approval" behavior) — it is
  logged and left for manual follow-up, since the human already made the real decision.
- **BREAKING**: a `sales_interest` message no longer produces a payment link in the same
  turn — by design. This is the point of the change.

## Capabilities

### New Capabilities
- `taty-wompi-link-hitl-gate`: the invariant that no Wompi payment link reaches a real customer
  without an explicit human approval action, and the `approval_queue` payload contract
  (`draft_type="wompi_payment_link"`, `payload={"lead_id": ...}`) that carries the pending request.

### Modified Capabilities
- `taty-wompi-tools-integration`: `generate_wompi_link` itself is unmodified; who is allowed to
  call it and when changes — only a human-approved draft can trigger a real send now.

## Impact

- **Code**: `apps/backend/services/taty_lead_router.py` (sales_interest branch, new enqueue
  helper), `apps/backend/services/approval_queue_service.py` (new `wompi_payment_link` branch in
  `approve_draft`).
- **No migrations** — reuses `approval_queue` as-is; every column this insert needs already has a
  safe default except `tenant_id`/`draft_id`/`draft_type`/`payload`, all of which are supplied.
- **No frontend changes** — the Búnker's existing approval-queue UI (if any) or the
  `/api/v1/approval-queue/*` endpoints already used for `tax_correction` drafts work unmodified
  for this new draft type; it appears in the same list.
- **Out of scope**: resolving which entity should actually own the Wompi merchant account
  (founder decision, tracked separately, not an engineering task); a dedicated UI for reviewing
  `wompi_payment_link` drafts specifically (the generic approval-queue surface is enough for now).
