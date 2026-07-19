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

### Requirement: Payment-related tools are explicit stubs pending the Wompi integration
The system SHALL expose `generate_wompi_link` and `verify_wompi_transaction` as functions that
raise `NotImplementedError` naming the future Wompi integration as their closure. A detected
payment-confirmation intent ("ya pagué") SHALL be caught by the router and replied to with a
graceful "not yet available" message — never a fabricated payment confirmation.

#### Scenario: A payment-confirmation message gets a graceful not-yet-available reply
- **WHEN** a lead sends a message indicating they already paid
- **THEN** the reply states that payment confirmation isn't available yet and that a human will
  follow up, and no `crm_wompi_transactions` row is created or modified
