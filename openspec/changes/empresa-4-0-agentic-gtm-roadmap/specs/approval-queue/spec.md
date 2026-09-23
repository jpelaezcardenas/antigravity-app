## ADDED Requirements

### Requirement: Enqueued drafts are classified into a risk tier at enqueue time
The system SHALL compute a risk tier (confidence × irreversibility) for every draft accepted into
`approval_queue`, independent of and in addition to Agent Critic's existing balance validation.
Risk tier SHALL affect review routing/SLA only — it SHALL NEVER affect whether Agent Critic accepts
or rejects a draft for balance.

#### Scenario: Risk tier is computed alongside existing Agent Critic validation
- **WHEN** a balanced draft passes Agent Critic validation and is inserted into `approval_queue`
- **THEN** the inserted row also carries a computed risk tier, and Agent Critic's `is_valid`
  outcome is unaffected by that computation

### Requirement: DIAN, tax-figure, and Wompi-payment actions always escalate to the highest risk tier
Any draft whose content or task type touches a DIAN filing, a client-facing tax figure, or a Wompi
payment link SHALL be assigned the highest risk tier regardless of the classifier's computed
confidence score. This is a fail-closed floor, not a suggestion the classifier can override.

#### Scenario: A Wompi-payment-related draft is always highest tier
- **WHEN** a draft's task type or content references a Wompi payment link
- **THEN** its risk tier is the highest tier, even if the classifier would otherwise compute a
  lower-risk score

#### Scenario: A DIAN-filing-related draft is always highest tier
- **WHEN** a draft's content references a DIAN filing or declaration
- **THEN** its risk tier is the highest tier, regardless of computed confidence

### Requirement: Low-risk, high-confidence drafts can be marked for expedited review
A draft whose computed risk tier is low (not DIAN/tax/Wompi, and high classifier confidence) MAY be
marked for expedited review. This marking SHALL NOT auto-approve the draft — HITL approval remains
mandatory for every draft regardless of risk tier.

#### Scenario: Low-risk draft is marked expedited but still requires approval
- **WHEN** a draft (e.g. an ad-copy variant) is classified as low risk with high confidence
- **THEN** it is marked for expedited review in the queue, but it still requires an explicit
  `POST /approve` call before its status changes from `pending_approval`

### Requirement: Risk tier is visible to queue readers
`GET /api/v1/approval-queue` responses SHALL include each draft's computed risk tier, so a reviewer
(operator or tenant client) can see and prioritize by tier without a separate lookup.

#### Scenario: Queue listing includes risk tier per draft
- **WHEN** a caller lists the approval queue
- **THEN** each returned draft includes its risk tier alongside its existing fields
