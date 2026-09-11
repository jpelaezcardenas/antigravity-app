## ADDED Requirements

### Requirement: A Renta Natural sale is only "done" once verified end to end with a real sale
Completing this change SHALL require one real Renta Natural lead to move through WhatsApp intake,
Taty triage, Tatiana's human quote, an in-person cash or direct-transfer (key/QR) payment received
by Tatiana, and recorded service delivery — code deployed without this observed sale SHALL NOT be
reported as complete. A Wompi transaction is NOT required for this verification (revised
2026-09-10, founder decision — see design.md Decision 3b): the Wompi/Entidad A remittance rail is
deferred and out of scope for this change's closing criterion.

#### Scenario: All code is deployed but no real sale has been observed
- **WHEN** the channel consolidation and durable inbox tasks are all deployed to production and
  passing their own tests
- **THEN** this change's Stage 11 report SHALL state the change is incomplete pending the
  end-to-end verification sale

#### Scenario: One real sale completes the path
- **WHEN** a real lead's WhatsApp conversation results in a Tatiana-approved quote and a confirmed
  cash or direct-transfer payment received by Tatiana in person
- **THEN** the change's Stage 11 report SHALL record the lead id, Tatiana's payment confirmation,
  and delivery confirmation as evidence of completion

### Requirement: Founder-dependent blockers are tracked, never defaulted
Any precondition that requires a founder action (obtaining the Meta App Secret, resolving the
`phone_number_id` conflict, confirming Wompi Pagos a Terceros applicability, supplying Entidad A's
payout beneficiary details) SHALL be recorded as an explicitly blocked task owned by the founder,
and SHALL NOT be worked around with an assumed or default value.

#### Scenario: A founder-only input is missing
- **WHEN** implementation reaches a task that needs the Meta App Secret or Entidad A's payout
  beneficiary details and neither has been supplied
- **THEN** the task SHALL remain marked blocked with the founder as owner
- **AND** no code path SHALL substitute a guessed or placeholder value for that input in a
  production configuration

### Requirement: Absorbed changes remain individually traceable
Work absorbed from `taty-channel-consolidation`, `whatsapp-durable-inbox`, and
`taty-wompi-entidad-a-remittance` SHALL retain a back-reference to their original task numbering,
so progress against each source change remains auditable independently of this change's own task
list.

#### Scenario: A reviewer checks progress on one absorbed change
- **WHEN** someone inspects this change's `tasks.md` for work absorbed from
  `taty-channel-consolidation`
- **THEN** each such task SHALL cite its originating task id (e.g. "absorbs
  taty-channel-consolidation task 4.1")
