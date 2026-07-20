## MODIFIED Requirements

### Requirement: Payment-related tools are real, backed by the live Wompi integration
The system SHALL expose `generate_wompi_link` and `verify_wompi_transaction` as real functions
(no longer stubs). `generate_wompi_link(lead_id)` SHALL return a valid Wompi Web Checkout URL built
from `CrmService.checkout_lead_payment`'s signed payload, reusing an existing `PENDING`
transaction for that lead if one exists rather than creating a duplicate. `verify_wompi_transaction
(lead_id)` SHALL report the lead's current `crm_wompi_transactions` status by reading it directly,
making no new outbound call to Wompi's API. A detected payment-confirmation intent SHALL check the
real status: `APPROVED` advances the lead to `POR_APROBAR` (still HITL-gated at
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
