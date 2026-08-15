## ADDED Requirements

### Requirement: Deal amount reflects the latest payment transaction
The system SHALL set the HubSpot Deal's `amount` property from the lead's latest `crm_wompi_transactions.amount_cents` (converted from COP minor units to whole COP), when such a transaction exists.

#### Scenario: Lead has a payment transaction
- **WHEN** a `crm_leads` row has a related `crm_wompi_transactions` row
- **THEN** the synced Deal's `amount` is set to that transaction's `amount_cents / 100`

#### Scenario: Lead has no payment transaction
- **WHEN** a `crm_leads` row has no related `crm_wompi_transactions` row
- **THEN** the synced Deal's `amount` is left unset

### Requirement: Follow-up task on pending approval
The system SHALL create a HubSpot Task associated with the Deal when a lead's `stage` is `POR_APROBAR`, unless an incomplete Task is already associated with that Deal.

#### Scenario: Lead newly reaches POR_APROBAR
- **WHEN** a `crm_leads` row with `stage = 'POR_APROBAR'` is synced and its Deal has no existing incomplete Task
- **THEN** a HubSpot Task is created and associated with the Deal

#### Scenario: Lead already has an open task
- **WHEN** a `crm_leads` row with `stage = 'POR_APROBAR'` is synced and its Deal already has an incomplete Task
- **THEN** no additional Task is created
