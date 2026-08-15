## ADDED Requirements

### Requirement: Missed-payment risk is detected for active B2B clients
The system SHALL flag an `activo` B2B client as at-risk when `b2b_payments` has no row for that
client in the most recently *complete* calendar month.

#### Scenario: An active client with no payment in the last complete month is flagged
- **WHEN** the retention evaluator runs and an `activo` client has no `b2b_payments` row for the
  most recently complete calendar month
- **THEN** a `missed_payment` alert is generated for that client

#### Scenario: The current in-progress month is not evaluated
- **WHEN** the retention evaluator runs mid-month, before the current month's payment would
  typically land
- **THEN** the current (incomplete) month is not used to trigger a missed-payment alert

#### Scenario: An inactive client is never evaluated
- **WHEN** the retention evaluator runs and a client's status is `inactivo`
- **THEN** no missed-payment alert is generated for that client, regardless of payment history

### Requirement: Payment-drop risk is detected against a client's own trailing average
The system SHALL flag an `activo` client with at least 3 prior months of `b2b_payments` history
when their latest payment's `amount_cents` is materially below their own trailing 3-month average.

#### Scenario: A sharp drop from a client's own average is flagged
- **WHEN** a client's latest payment is materially lower than their trailing 3-month average
  payment amount
- **THEN** a `payment_drop` alert is generated for that client

#### Scenario: A client with fewer than 3 prior payments is not evaluated by this rule
- **WHEN** a client has fewer than 3 `b2b_payments` rows in their history
- **THEN** the payment-drop rule does not evaluate that client (no false "100% drop" from a first
  payment)

### Requirement: Retention alerts are persisted and tenant-scoped
The system SHALL persist triggered alerts to `retention_alerts` (mirroring `centinela_alerts`'
shape), scoped to the caller's resolved `tenant_id` — never defaulting to Cliente Cero implicitly.

#### Scenario: Triggered alerts are saved with the caller's tenant
- **WHEN** the retention evaluator triggers one or more alerts for a resolved `tenant_id`
- **THEN** each alert is persisted to `retention_alerts` with that `tenant_id`

### Requirement: Retention alerts are readable via the CRM API
The system SHALL expose `GET /api/v1/crm/b2b/retention-alerts`, which SHALL trigger evaluation and
return current alerts for the caller's B2B roster.

#### Scenario: An admin retrieves current retention alerts
- **WHEN** an admin calls `GET /api/v1/crm/b2b/retention-alerts`
- **THEN** the response includes any currently-triggered `missed_payment`/`payment_drop` alerts for
  the B2B roster
