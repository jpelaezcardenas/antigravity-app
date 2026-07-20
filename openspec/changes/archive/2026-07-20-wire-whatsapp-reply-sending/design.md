## Context

`whatsapp_endpoints.py`'s `whatsapp_webhook` handler:
```python
for event in events:
    lead_id = find_or_create_lead(event["account_id"], full_name=event.get("actor_name"))
    if event.get("media_id"):
        await route_lead_document(lead_id, event["media_id"], event.get("mime_type") or "")
    else:
        route_lead_message(lead_id, event["text"])
```
The `else` branch's return value (a dict with `intent`, `confidence`, `reply`) is never used.
`route_lead_document`, by contrast, already sends `EXTRACTOS_REQUEST_MESSAGE` via
`send_whatsapp_message(phone, text)` after processing a RUT — the established, working precedent
this change follows. `send_whatsapp_message` (in `channels/whatsapp.py`) already has the
no-token-no-crash graceful-degradation pattern used throughout this session's Taty changes.

## Goals / Non-Goals

**Goals:**
- Every `route_lead_message` reply actually reaches the lead over WhatsApp, closing the gap found
  live during `taty-kb-and-react-router`'s Stage 11.

**Non-Goals:**
- **Not making `route_lead_message` itself `async` or move the send inside it.** The function
  stays a pure, synchronous "compute a reply" function — sending is the webhook handler's
  responsibility, consistent with `route_lead_document`'s existing pattern (that function does its
  own outbound send internally, but it's already `async def`; `route_lead_message` is not, and
  making it `async` would ripple into every existing call site and test across Changes D/H/I/
  taty-persona-fields/taty-kb-and-react-router). The handler is already `async def
  whatsapp_webhook`, so it can `await send_whatsapp_message(...)` right after the synchronous call
  without needing `route_lead_message` itself to change.
- **No retry/delivery-confirmation logic** — matches `route_lead_document`'s existing send, which
  also doesn't retry on failure.
- **No change to any reply's content** — this only wires the already-computed reply to actually
  send; the content itself (sales/payment/KB-grounded) is untouched, all from prior changes.

## Decisions

1. **Send from the webhook handler, not from inside `route_lead_message`.** Keeps
   `route_lead_message` a pure function (easier to unit-test, as it already is across 40+ existing
   tests that assert on its returned `reply` string without any WhatsApp mocking needed) and
   matches the separation `route_lead_document` already has between computing state changes and
   sending messages — actually, `route_lead_document` does the send inline; the meaningful
   precedent here is narrower: it's fine for the *handler* to own the send when the underlying
   function stays synchronous, which is exactly this case.
2. **Phone number is `event["account_id"]`**, not a new lookup via `_get_lead_phone` (already
   used elsewhere for the RUT/extractos flow). The webhook event already carries the sender's
   phone number directly from the inbound payload — no need to round-trip through `crm_leads` to
   fetch it back.

## Risks / Trade-offs

- **[Risk] `send_whatsapp_message` failing silently could mask real delivery problems** →
  **Mitigation**: out of scope — this is `send_whatsapp_message`'s existing, unmodified behavior,
  already relied upon by `route_lead_document`; not something this change introduces or should
  fix as a side effect.
- **[Trade-off] Still can't be verified end-to-end for real** — no real WhatsApp Business
  number/token exists yet (same limitation as every Taty change this session). Live verification
  is logic-only: confirm the send is attempted (a real, correctly-shaped outbound call is made)
  and no-ops gracefully.

## Migration Plan

No migration — pure logic addition to one existing handler. Stage 11: POST a fabricated WhatsApp
text-message webhook for a real disposable test lead, confirm `200` and (via Railway logs) that
`send_whatsapp_message` was actually invoked with the lead's phone and the computed reply text,
confirming it no-ops gracefully (no crash) since `WHATSAPP_TOKEN` is unset in production.
