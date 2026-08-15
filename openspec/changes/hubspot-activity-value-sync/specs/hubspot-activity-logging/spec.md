## ADDED Requirements

### Requirement: First-sync conversation note
The system SHALL create a HubSpot Note associated with a lead's Contact, containing `crm_leads.last_message`, the first time that lead is synced (previously null `last_synced_at`), when `last_message` is non-empty.

#### Scenario: New lead with a message is synced for the first time
- **WHEN** a `crm_leads` row with null `last_synced_at` and a non-empty `last_message` is synced
- **THEN** a HubSpot Note containing that message is created and associated with the synced Contact

#### Scenario: New lead with no message yet
- **WHEN** a `crm_leads` row with null `last_synced_at` and an empty/null `last_message` is synced
- **THEN** no Note is created

#### Scenario: Already-synced lead is not re-noted
- **WHEN** a `crm_leads` row with a non-null `last_synced_at` is re-synced
- **THEN** no additional Note is created for that tick
