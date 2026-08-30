## ADDED Requirements

### Requirement: A sales-interest message never sends a real payment link automatically
When `route_lead_message` classifies a message as `sales_interest`, the system SHALL NOT call
`generate_wompi_link` or send any message to the customer containing a checkout URL, an amount, or
a merchant name as part of that same request.

#### Scenario: A sales-interest reply contains no link
- **WHEN** a lead's message is classified as `sales_interest`
- **THEN** the reply text SHALL NOT contain "checkout.wompi.co" or any payment amount
- **AND** `generate_wompi_link` SHALL NOT be called

#### Scenario: A sales-interest message enqueues a pending approval instead
- **WHEN** a lead's message is classified as `sales_interest`
- **THEN** a row SHALL be inserted into `approval_queue` with `draft_type="wompi_payment_link"`,
  `status="pending_approval"`, and `payload` containing the lead's id

### Requirement: A human approval is required before the real link is delivered
The Wompi checkout link SHALL be generated and sent to the customer's WhatsApp only as a direct
result of an explicit approval action on the corresponding `approval_queue` draft.

#### Scenario: Approving the draft generates and sends the real link
- **WHEN** an operator approves a `wompi_payment_link` draft
- **THEN** the system SHALL generate a real Wompi checkout link for the draft's lead
- **AND** SHALL send it to that lead's WhatsApp number via the existing Meta send path

#### Scenario: Rejecting the draft sends nothing
- **WHEN** an operator rejects a `wompi_payment_link` draft
- **THEN** no Wompi link SHALL be generated and no WhatsApp message SHALL be sent as a result

#### Scenario: A delivery failure does not undo the approval
- **WHEN** sending the generated link to WhatsApp fails
- **THEN** the draft's status SHALL remain `approved`
- **AND** the failure SHALL be logged for manual follow-up
