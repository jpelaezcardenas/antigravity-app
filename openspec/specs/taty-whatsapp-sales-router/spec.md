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
`actor_name`, `text`, `raw_payload`), tolerating missing/malformed fields without raising.

#### Scenario: A well-formed inbound text message normalizes correctly
- **WHEN** a WhatsApp Cloud API webhook payload containing one text message from a given phone
  number is normalized
- **THEN** the resulting event has `channel="whatsapp"`, the sender's phone number as
  `account_id`, and the message text in `text`

#### Scenario: A malformed or non-text payload does not crash normalization
- **WHEN** the payload is missing expected fields (e.g. a status/delivery-receipt webhook with no
  message text)
- **THEN** normalization returns an empty list of events rather than raising an exception

### Requirement: Inbound sales-intent messages create or update a lead and advance NUEVOS to PROSPECTOS
The system SHALL route a normalized inbound WhatsApp message to `route_lead_message(lead_id,
message)`, which SHALL find-or-create a `crm_leads` row keyed by `whatsapp_phone`, classify the
message's intent, and SHALL advance the lead from `NUEVOS` to `PROSPECTOS` (via the existing,
unmodified `CrmService.advance_lead`) when sales intent is detected. A lead already past `NUEVOS`
SHALL NOT be advanced or regressed by this routing.

#### Scenario: A first-time WhatsApp sender becomes a new NUEVOS lead
- **WHEN** a WhatsApp message arrives from a phone number with no existing `crm_leads` row
- **THEN** a new `crm_leads` row is created with `stage="NUEVOS"` and that `whatsapp_phone`

#### Scenario: Sales intent advances a NUEVOS lead to PROSPECTOS
- **WHEN** a message expressing interest in Renta Natural arrives from a lead currently
  `stage="NUEVOS"`
- **THEN** the lead's stage becomes `PROSPECTOS`

#### Scenario: A lead past NUEVOS is not re-advanced or regressed
- **WHEN** a message arrives from a lead whose stage is already `PROSPECTOS`, `POR_APROBAR`, or
  `LISTOS_CONTADORA`
- **THEN** the lead's stage is left unchanged by this routing, regardless of detected intent

### Requirement: Detected persona state is persisted to the lead's tax profile
The system SHALL persist detected persona fields (`es_asalariado`, `topes`) into the lead's
`crm_tax_profiles` row via the existing, unmodified `CrmService.update_tax_profile`, creating an
empty tax-profile row first if none exists yet for that lead.

#### Scenario: Persona state is saved for a lead with no existing tax profile
- **WHEN** a message reveals `es_asalariado=true` for a lead with no `crm_tax_profiles` row yet
- **THEN** a `crm_tax_profiles` row is created for that lead with `es_asalariado=true`

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
