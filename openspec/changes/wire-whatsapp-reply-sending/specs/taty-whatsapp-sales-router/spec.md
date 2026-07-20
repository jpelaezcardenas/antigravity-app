## ADDED Requirements

### Requirement: route_lead_message replies are sent back to the lead over WhatsApp
The system SHALL, after `route_lead_message` computes a reply for an inbound text-message event,
send that reply to the lead via `send_whatsapp_message(event["account_id"], reply)`. This applies
to every intent branch (`sales_interest`, `payment_confirmation`, and `unknown`/KB-grounded)
without any change to the reply content itself. A send failure (e.g. `WHATSAPP_TOKEN` unset) SHALL
NOT raise or affect the webhook's `200` response.

#### Scenario: A sales-interest reply is sent to the lead
- **WHEN** an inbound text message classified as `sales_interest` is routed
- **THEN** `send_whatsapp_message` is called with the lead's phone number and the reply containing
  the Wompi checkout link

#### Scenario: A KB-grounded fiscal-question reply is sent to the lead
- **WHEN** an inbound text message triggers the KB-grounded `unknown` fallback
- **THEN** `send_whatsapp_message` is called with the synthesized (or graceful-fallback) reply

#### Scenario: A send failure does not affect the webhook response
- **WHEN** `send_whatsapp_message` returns `False` (e.g. `WHATSAPP_TOKEN` unset)
- **THEN** the webhook still returns `200` with `{"ok": true, "events_processed": N}`
