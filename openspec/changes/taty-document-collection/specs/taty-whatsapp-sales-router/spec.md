## MODIFIED Requirements

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
