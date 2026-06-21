## ADDED Requirements

### Requirement: Taty routes Telegram messages to the correct agent by intent
The system SHALL receive Telegram webhook messages, classify intent, and delegate to Pulso Diario, Radar Predictivo, Auditoría Sombra, or Centinela read paths as appropriate.

#### Scenario: Status intent routed to Pulso
- **WHEN** a Telegram message is classified as a daily-status intent
- **THEN** Taty calls Pulso Diario's summary endpoint and replies with a formatted summary

#### Scenario: Risk intent routed to Radar
- **WHEN** a Telegram message is classified as a risk-inquiry intent
- **THEN** Taty calls Radar Predictivo's risk-score endpoint and replies with the score and forecast

#### Scenario: Unrecognized intent falls back gracefully
- **WHEN** intent classification confidence is below threshold
- **THEN** Taty replies with a clarifying message rather than guessing a route
- **AND** no agent endpoint is called

### Requirement: Taty escalates sensitive intents to Approval Queue instead of acting directly
The system SHALL NOT allow Taty to directly trigger any write-capable action (journal correction, write-back, report sign-off); sensitive intents are translated into an Approval Queue entry for human review.

#### Scenario: User requests a correction via chat
- **WHEN** a Telegram message expresses intent to correct a transaction (e.g., "arregla la factura X")
- **THEN** Taty creates an `approval_queue` row with `draft_type = 'taty_escalation'` describing the request
- **AND** Taty replies confirming the request was escalated, without performing the correction itself

#### Scenario: Taty never calls a write endpoint directly
- **WHEN** Taty's intent router resolves any intent
- **THEN** the resolved action SHALL be either a read call or an Approval Queue enqueue, never a direct write to Siigo or the Shadow GL
