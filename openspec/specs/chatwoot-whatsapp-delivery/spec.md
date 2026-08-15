## ADDED Requirements

### Requirement: Chatwoot is the sole outbound sender for the Taty WhatsApp channel
The Chatwoot WhatsApp inbox used for the Taty sales channel SHALL be the real Meta-linked inbox
(`Channel::Whatsapp`, not a test/injection channel), and it SHALL be the only system that delivers
outbound messages to the customer's WhatsApp for this channel. The backend SHALL return reply text
without delivering it directly when called from this channel's flow.

#### Scenario: A Taty-generated reply reaches the customer exactly once
- **WHEN** Taty computes a reply for an inbound WhatsApp message on this channel
- **THEN** the customer receives exactly one message — delivered by Chatwoot, not duplicated by a
  direct backend send

#### Scenario: A human's Chatwoot reply reaches the customer
- **WHEN** a human agent types a reply directly in the Chatwoot conversation (not through Taty)
- **THEN** that reply is delivered to the customer's real WhatsApp via Chatwoot's own Meta
  credentials

#### Scenario: The bridge is pointed at the real inbox, not the test inbox
- **WHEN** the bridge polls for and injects inbound events
- **THEN** it targets the inbox backed by real Meta credentials (verified phone number, WABA), not
  an API-only test channel that cannot deliver to a real phone

### Requirement: The bot_off pause remains the human handover mechanism
Tagging a Chatwoot conversation with the `bot_off` label SHALL continue to pause Taty's automated
replies on this channel, unchanged by the delivery-path change, so a human can take over a
conversation Taty escalates or a customer explicitly asks to speak to a person.

#### Scenario: A bot_off-tagged conversation does not receive an automated reply
- **WHEN** a conversation carries the `bot_off` label and a new inbound customer message arrives
- **THEN** no automated Taty reply is generated or delivered for that message
