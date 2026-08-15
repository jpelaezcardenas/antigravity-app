## ADDED Requirements

### Requirement: WhatsApp webhook verification uses the standard hub.challenge handshake
The system SHALL expose `GET /channels/whatsapp/webhook`, which SHALL echo `hub.challenge` as
plain text when `hub.mode == "subscribe"` and `hub.verify_token` matches the configured
`WHATSAPP_WEBHOOK_VERIFY_TOKEN`, and SHALL reject the request with a 403 otherwise — mirroring the
existing Meta webhook's verification behavior exactly.

#### Scenario: A valid verification request is echoed back
- **WHEN** Meta calls `GET /channels/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<correct
  token>&hub.challenge=12345`
- **THEN** the response body is the plain-text string `12345`

#### Scenario: An invalid verify token is rejected
- **WHEN** the request's `hub.verify_token` does not match the configured token
- **THEN** the response is a 403 error

### Requirement: Inbound WhatsApp messages are normalized into a common event shape
The system SHALL normalize an inbound WhatsApp Cloud API webhook payload into the same event shape
used by the Telegram channel (`channel`, `account_id`, `source_event_id`, `actor_handle`,
`actor_name`, `text`, `raw_payload`), tolerating missing/malformed fields without raising. Document
and image messages SHALL also be normalized (additively — existing text-message normalization is
unaffected), populating `media_id` and `mime_type` on the event when present, with `text` empty for
these message types.

#### Scenario: A well-formed inbound text message normalizes correctly
- **WHEN** a WhatsApp Cloud API webhook payload containing one text message from a given phone
  number is normalized
- **THEN** the resulting event has `channel="whatsapp"`, the sender's phone number as
  `account_id`, and the message text in `text`

#### Scenario: A malformed or non-text payload does not crash normalization
- **WHEN** the payload is missing expected fields (e.g. a status/delivery-receipt webhook with no
  message text)
- **THEN** normalization returns an empty list of events rather than raising an exception

#### Scenario: A document message normalizes with media_id and mime_type populated
- **WHEN** a WhatsApp Cloud API webhook payload containing one document message (`type="document"`)
  is normalized
- **THEN** the resulting event has `channel="whatsapp"`, the sender's phone number as
  `account_id`, `media_id` and `mime_type` populated from the document payload, and empty `text`

#### Scenario: An image message normalizes the same way as a document message
- **WHEN** a WhatsApp Cloud API webhook payload containing one image message (`type="image"`) is
  normalized
- **THEN** the resulting event has `media_id` and `mime_type` populated the same way as a document
  message

### Requirement: Inbound sales-intent messages create or update a lead and advance NUEVOS to PROSPECTOS
The system SHALL route a normalized inbound WhatsApp message to `route_lead_message(lead_id,
message)`, which SHALL find-or-create a `crm_leads` row keyed by `tenant_id` AND `whatsapp_phone`
(never by `whatsapp_phone` alone), classify the message's intent, and SHALL advance the lead from
`NUEVOS` to `PROSPECTOS` (via the existing, unmodified `CrmService.advance_lead`) when sales intent
is detected. A lead already past `NUEVOS` SHALL NOT be advanced or regressed by this routing.

The find-or-create step SHALL delegate to `CrmService.whatsapp_intake` (the same tenant-scoped
implementation the Chatwoot-Hermes bridge uses) rather than running an independent, duplicate
Supabase query — this is the single implementation of "find-or-create a lead by WhatsApp phone" in
the codebase.

#### Scenario: A first-time WhatsApp sender becomes a new NUEVOS lead
- **WHEN** a WhatsApp message arrives from a phone number with no existing `crm_leads` row for the
  resolved tenant
- **THEN** a new `crm_leads` row is created with `stage="NUEVOS"`, that tenant's `tenant_id`, and
  that `whatsapp_phone`

#### Scenario: Sales intent advances a NUEVOS lead to PROSPECTOS
- **WHEN** a message expressing interest in Renta Natural arrives from a lead currently
  `stage="NUEVOS"`
- **THEN** the lead's stage becomes `PROSPECTOS`

#### Scenario: A lead past NUEVOS is not re-advanced or regressed
- **WHEN** a message arrives from a lead whose stage is already `PROSPECTOS`, `POR_APROBAR`, or
  `LISTOS_CONTADORA`
- **THEN** the lead's stage is left unchanged by this routing, regardless of detected intent

#### Scenario: The lookup never matches a lead belonging to a different tenant
- **WHEN** a `crm_leads` row exists with a matching `whatsapp_phone` but a different `tenant_id`
  than the one resolved for this inbound message
- **THEN** that row is NOT returned or reused; a new row is created for the correct tenant instead

### Requirement: Detected persona state is persisted to the lead's tax profile
The system SHALL persist detected persona fields (`es_asalariado`, `topes`, `obligado_declarar`)
into the lead's `crm_tax_profiles` row via the existing, unmodified `CrmService.update_tax_profile`,
creating an empty tax-profile row first if none exists yet for that lead. `topes` entries SHALL be
merged with any existing `topes` on the profile, never overwritten wholesale. `obligado_declarar`
SHALL be recomputed as a preliminary signal (not a legally authoritative determination) whenever
`topes` changes, comparing the known `ingresos`/`consignaciones` amount against
`core.constants.UMBRAL_RENTA_COP`.

#### Scenario: Persona state is saved for a lead with no existing tax profile
- **WHEN** a message reveals `es_asalariado=true` for a lead with no `crm_tax_profiles` row yet
- **THEN** a `crm_tax_profiles` row is created for that lead with `es_asalariado=true`

#### Scenario: A topes amount mentioned in a message is merged, not overwritten
- **WHEN** a lead's tax profile already has `topes={"consignaciones": 50000000}` and a new message
  mentions ingresos of 20,000,000
- **THEN** the profile's `topes` becomes `{"consignaciones": 50000000, "ingresos": 20000000}` —
  the existing `consignaciones` entry is preserved

#### Scenario: obligado_declarar is set true when a known topes amount meets the renta threshold
- **WHEN** a lead's `topes` includes an `ingresos` or `consignaciones` value greater than or equal
  to `UMBRAL_RENTA_COP`
- **THEN** the profile's `obligado_declarar` becomes `true`

#### Scenario: obligado_declarar is set false when known topes amounts stay below the threshold
- **WHEN** a lead's `topes` includes only `ingresos`/`consignaciones` values below
  `UMBRAL_RENTA_COP`
- **THEN** the profile's `obligado_declarar` becomes `false`

#### Scenario: A message with no detectable topes amount leaves obligado_declarar unset
- **WHEN** a message contains no category keyword + peso-amount pair
- **THEN** `topes` and `obligado_declarar` are left unchanged on the profile

### Requirement: Unmatched fiscal questions are answered via KB-grounded reasoning
The system SHALL, when `classify_lead_intent` returns `unknown`, route the message to
`TatyAgentService` (the same service Telegram and the PWA use, profile `taty-v1`) rather than
generating reply text via a router-local pair of raw LLM calls. `TatyAgentService` SHALL be given
the lead's WhatsApp channel context (recent conversation history, known persona fields, current
CRM stage) and SHALL retrieve grounding from the knowledge base itself as part of answering. If the
knowledge base has nothing relevant, or the service call fails, Taty SHALL reply with an honest
"let me get a human to help" message rather than a hardcoded string and rather than fabricating an
ungrounded answer.

#### Scenario: A fiscal question with matching KB content gets a grounded reply
- **WHEN** an unmatched message concerns a fiscal topic and the knowledge base has relevant content
- **THEN** Taty's reply is generated by `TatyAgentService` grounded in that content, not a static
  fallback string

#### Scenario: A fiscal question with no matching KB content gets a graceful fallback
- **WHEN** an unmatched message concerns a fiscal topic but the knowledge base has nothing relevant
- **THEN** Taty's reply honestly offers a human advisor's follow-up, without fabricating an answer

#### Scenario: A conversational, non-fiscal message gets a real conversational reply
- **WHEN** an unmatched message is a greeting, a contact question, or an acknowledgement (e.g.
  "Hola ayudame", "Xomo lo contacto?", "Ok")
- **THEN** Taty replies conversationally via `TatyAgentService`, not the prior static "No estoy
  segura de tu pregunta..." string that a keyword-only classifier produced regardless of message
  intent

#### Scenario: A `TatyAgentService` failure degrades gracefully
- **WHEN** the call to `TatyAgentService` raises or times out
- **THEN** Taty's reply falls back to an honest "a human will help you shortly" message rather than
  the request failing or a WhatsApp send being silently dropped

### Requirement: route_lead_message replies are sent back to the lead over WhatsApp
The system SHALL, after a reply is computed for an inbound text-message event, deliver that reply
via exactly one configured channel — either the direct `send_whatsapp_message` path, or Chatwoot
(see `chatwoot-whatsapp-delivery`), selected by a `deliver` flag on `POST /leads/{id}/reply` — never
both for the same inbound message. This applies to every intent branch
(`sales_interest`, `payment_confirmation`, and the `TatyAgentService`-routed fallback) without any
change to how each branch's reply content is computed. A send failure on either path SHALL NOT
raise or affect the webhook's `200` response.

#### Scenario: A sales-interest reply is delivered exactly once
- **WHEN** an inbound text message classified as `sales_interest` is routed and a delivery channel
  is configured
- **THEN** the reply is delivered through that one channel — never sent both directly and via
  Chatwoot for the same inbound message

#### Scenario: A TatyAgentService-routed reply is delivered the same way as any other branch
- **WHEN** an inbound text message triggers the `TatyAgentService`-routed fallback
- **THEN** its reply is delivered through the same single configured channel as `sales_interest`
  and `payment_confirmation` replies

#### Scenario: A send failure does not affect the webhook response
- **WHEN** the configured delivery channel fails to send
- **THEN** the webhook still returns `200` with `{"ok": true, "events_processed": N}`

### Requirement: Payment-related tools are real, backed by the live Wompi integration
The system SHALL expose `generate_wompi_link` and `verify_wompi_transaction` as real functions (no
longer stubs). `generate_wompi_link(lead_id)` SHALL return a valid Wompi Web Checkout URL built
from `CrmService.checkout_lead_payment`'s signed payload, reusing an existing `PENDING` transaction
for that lead if one exists rather than creating a duplicate. `verify_wompi_transaction(lead_id)`
SHALL report the lead's current `crm_wompi_transactions` status by reading it directly, making no
new outbound call to Wompi's API. A detected payment-confirmation intent SHALL check the real
status: `APPROVED` advances the lead to `POR_APROBAR` (still HITL-gated at
`CrmService.approve_payment` for the final `LISTOS_CONTADORA` transition) and confirms receipt;
`PENDING` asks the lead to wait; no transaction found says so honestly.

#### Scenario: A sales-interest reply includes a real checkout link
- **WHEN** a lead expresses sales interest and no `PENDING`/`APPROVED` transaction exists yet for
  them
- **THEN** a new `crm_wompi_transactions` row is created and Taty's reply includes a valid Wompi
  Web Checkout URL built from it

#### Scenario: A second sales-interest message reuses the existing pending transaction
- **WHEN** a lead already has a `PENDING` `crm_wompi_transactions` row and sends another
  sales-interest message
- **THEN** no new `crm_wompi_transactions` row is created; the existing reference is reused to
  build the checkout link

#### Scenario: A payment-confirmation message with an approved transaction advances the lead
- **WHEN** a lead sends a payment-confirmation message and their latest `crm_wompi_transactions`
  row has `status="APPROVED"`
- **THEN** the lead's stage advances to `POR_APROBAR` (never directly to `LISTOS_CONTADORA`) and
  Taty's reply confirms the payment was received

#### Scenario: A payment-confirmation message with a pending transaction asks the lead to wait
- **WHEN** a lead sends a payment-confirmation message and their latest transaction is still
  `status="PENDING"`
- **THEN** Taty's reply states the payment hasn't been confirmed yet, and the lead's stage is
  unchanged

#### Scenario: A payment-confirmation message with no transaction on file is handled honestly
- **WHEN** a lead sends a payment-confirmation message and has no `crm_wompi_transactions` row at
  all
- **THEN** Taty's reply states there is no pending payment on file, and no stage change occurs
