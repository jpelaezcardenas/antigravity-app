## ADDED Requirements

### Requirement: Inbound WhatsApp events are persisted before any processing
The webhook SHALL persist each normalized inbound event and return `200` without performing
classification, LLM inference, or outbound sending.

#### Scenario: A verified event is stored and acknowledged immediately
- **WHEN** a correctly signed payload containing one message arrives
- **THEN** the backend SHALL store one `whatsapp_inbound_events` row and respond `200`
- **AND** it SHALL NOT call the lead router or send a WhatsApp message during the request

#### Scenario: A crash after acknowledgement does not lose the message
- **WHEN** the event has been stored and the process restarts before it is processed
- **THEN** the event SHALL still be pullable, because durability does not depend on process state

### Requirement: Duplicate deliveries produce exactly one stored event
Meta retries failed deliveries and fans out to every subscribed app, so the same message id can
arrive many times. The system SHALL deduplicate on Meta's message id at the database level.

#### Scenario: The same message id delivered three times stores one row
- **WHEN** three payloads carrying the same Meta message id are received
- **THEN** exactly one `whatsapp_inbound_events` row SHALL exist for that id
- **AND** every request SHALL still respond `200`, so Meta stops retrying

#### Scenario: Concurrent duplicate deliveries do not race
- **WHEN** two deliveries of the same message id are processed concurrently
- **THEN** the unique constraint SHALL resolve the conflict, not application-level checking

### Requirement: The local node pulls unprocessed events over an authenticated endpoint
The backend SHALL expose an authenticated endpoint returning unprocessed, unclaimed events, and
an authenticated endpoint acknowledging events as processed. The local node SHALL never need to
be publicly reachable.

#### Scenario: A pull returns unprocessed events and claims them
- **WHEN** the poller calls the pull endpoint with a valid token
- **THEN** it SHALL receive the unprocessed events and those events SHALL be marked claimed

#### Scenario: A claimed event is not handed to a second puller
- **WHEN** a second pull happens while events are claimed and unexpired
- **THEN** those events SHALL NOT be returned again

#### Scenario: A crashed consumer gets its events back
- **WHEN** an event was claimed but never acknowledged and the claim has expired
- **THEN** a subsequent pull SHALL return it again

#### Scenario: Unauthenticated access is rejected
- **WHEN** either endpoint is called without a valid authentication token
- **THEN** the backend SHALL respond `401` and disclose no event data

### Requirement: Acknowledgement happens only after the event reaches Chatwoot
The poller SHALL acknowledge an event only after Chatwoot has accepted the injected message, so a
failure between pulling and injecting results in redelivery rather than a lost customer message.

#### Scenario: A failed Chatwoot injection leaves the event unacknowledged
- **WHEN** injecting into Chatwoot fails
- **THEN** the poller SHALL NOT acknowledge the event, and it SHALL be redelivered after the claim
  expires

### Requirement: Queue health is observable
The backend SHALL expose the count of unprocessed events and the age of the oldest unprocessed
event, so an offline local node is detectable rather than silent.

#### Scenario: A stalled consumer is visible
- **WHEN** the local node has been offline and events have accumulated
- **THEN** the backlog depth and oldest-event age SHALL be readable without querying the database
  directly
