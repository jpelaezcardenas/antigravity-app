## Why

`route_lead_message(lead_id, message)` computes a real reply for every intent (sales_interest,
payment_confirmation, and — as of this session's `taty-kb-and-react-router` — the KB-grounded
`unknown` fallback), but `presentation/whatsapp_endpoints.py`'s webhook handler calls it and
discards the return value entirely for text messages. Only `route_lead_document` (the RUT/
extractos flow) ever calls `send_whatsapp_message`. This means Taty's entire text-message reply
content has never actually reached a lead over WhatsApp, in any archived change to date — found
live during `taty-kb-and-react-router`'s Stage 11 verification (2026-07-20), invisible until now
because no real WhatsApp Business number/token exists yet to notice it with (same accepted
limitation as every Taty change this session).

## What Changes

- `whatsapp_endpoints.py`'s webhook handler, after calling `route_lead_message` for a text-message
  event, sends the resulting `reply` back to the lead via the existing, unmodified
  `send_whatsapp_message(phone, text)` — mirroring exactly how `route_lead_document` already sends
  `EXTRACTOS_REQUEST_MESSAGE` after processing a RUT document.
- The lead's phone number is `event["account_id"]` (already present on every normalized event,
  confirmed via `normalize_whatsapp_webhook`'s existing shape) — no new lookup needed.
- `send_whatsapp_message` already fails gracefully (returns `False`, logs, never raises) when
  `WHATSAPP_TOKEN` is unset — this change doesn't alter that behavior, so live verification remains
  logic-only (send is attempted and correctly no-ops) until a real WhatsApp number exists, same
  limitation as every prior Taty change.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `taty-whatsapp-sales-router`: the router's intent-handling requirements (sales_interest,
  payment_confirmation, unknown/KB-grounded) are unchanged in their reply *content*; this adds the
  requirement that the computed reply is actually sent back over WhatsApp, not just returned.

## Impact

- `apps/backend/presentation/whatsapp_endpoints.py` — the only file touched.
- `services/taty_lead_router.py` — reused as-is (`route_lead_message`'s return shape), not
  modified.
- No migration, no new endpoint, no frontend change.
