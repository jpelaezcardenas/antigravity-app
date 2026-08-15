# hubspot-company-registry Specification

## Purpose
TBD - created by archiving change hubspot-sync-renta-natural. Update Purpose after archive.
## Requirements
### Requirement: One-way B2B client sync to HubSpot Companies
The system SHALL sync `b2b_clients` rows to HubSpot as Companies only, for cross-reference purposes. B2B clients SHALL NOT be represented as HubSpot Deals or placed in any pipeline.

#### Scenario: New B2B client creates a HubSpot Company
- **WHEN** a new row is inserted into `b2b_clients` and has no `hubspot_company_id`
- **THEN** the Hermes poller creates a corresponding HubSpot Company and stores the returned `hubspot_company_id` and `last_synced_at` back onto the `b2b_clients` row

#### Scenario: B2B client sync never creates a Deal
- **WHEN** any `b2b_clients` row is synced, created, or updated
- **THEN** no HubSpot Deal is created or modified as a result

### Requirement: Read-only sync status visible in the Búnker
The system SHALL expose a read-only sync-status indicator in the Búnker for synced `crm_leads` and `b2b_clients` records, linking to the corresponding HubSpot record. The Búnker SHALL NOT offer any action that writes to HubSpot.

#### Scenario: Synced record shows confirmation badge
- **WHEN** a `crm_leads` or `b2b_clients` row has a non-null `last_synced_at`
- **THEN** the Búnker displays a "Sincronizado ✓" badge with a link to the corresponding HubSpot record

#### Scenario: Unsynced record shows neutral state
- **WHEN** a `crm_leads` or `b2b_clients` row has a null `last_synced_at`
- **THEN** the Búnker displays a neutral "sin sincronizar" state instead of the confirmation badge, and never shows a false-positive "Sincronizado ✓"

