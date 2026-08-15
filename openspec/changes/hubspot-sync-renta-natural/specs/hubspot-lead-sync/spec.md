## ADDED Requirements

### Requirement: One-way lead sync from Supabase to HubSpot
The system SHALL sync `crm_leads` rows to HubSpot as Contacts and Deals in the account's single default pipeline (`pipeline: default`), with Supabase remaining the sole source of truth. HubSpot data SHALL NOT be written back to Supabase.

#### Scenario: New lead creates a HubSpot Contact and Deal
- **WHEN** a new row is inserted into `crm_leads` and has no `hubspot_contact_id`
- **THEN** the Hermes poller creates a corresponding HubSpot Contact and a Deal in the default pipeline, and stores the returned `hubspot_contact_id`, `hubspot_deal_id`, and `last_synced_at` back onto the `crm_leads` row

#### Scenario: Existing synced lead is updated, not duplicated
- **WHEN** a `crm_leads` row with a non-null `hubspot_contact_id`/`hubspot_deal_id` changes
- **THEN** the poller upserts the existing HubSpot Contact and Deal by their stored IDs instead of creating new records

### Requirement: Lead funnel stage maps to Renta Natural pipeline stages
The system SHALL map each `crm_leads.stage` value to the corresponding HubSpot stock `dealstage` value in the single default pipeline: `NUEVOS`→`appointmentscheduled`, `PROSPECTOS`→`qualifiedtobuy`, `POR_APROBAR`→`presentationscheduled`, `LISTOS_CONTADORA`→`decisionmakerboughtin`. When the lead has a related `crm_wompi_transactions` row, its `status` overrides this mapping: `APPROVED`→`closedwon`, `DECLINED`→`closedlost`.

#### Scenario: Lead reaches an approved payment
- **WHEN** a `crm_leads` row has a related `crm_wompi_transactions` row with `status = 'APPROVED'`
- **THEN** the synced HubSpot Deal's `dealstage` is set to `closedwon`, regardless of `crm_leads.stage`

#### Scenario: Lead's payment is declined
- **WHEN** a `crm_leads` row has a related `crm_wompi_transactions` row with `status = 'DECLINED'`
- **THEN** the synced HubSpot Deal's `dealstage` is set to `closedlost`, regardless of `crm_leads.stage`

#### Scenario: Lead with no payment transaction follows the stage mapping
- **WHEN** a `crm_leads` row has no related `crm_wompi_transactions` row
- **THEN** the synced HubSpot Deal's `dealstage` is derived solely from `crm_leads.stage` per the mapping table

### Requirement: Sync credentials never reach Railway or Vercel
The system SHALL store the HubSpot Private App Access Token only in the local Hermes environment. The token SHALL NOT be present in any Railway service's environment variables, Vercel environment variables, or committed repo files.

#### Scenario: Poller runs entirely from Hermes-local process
- **WHEN** the sync worker executes
- **THEN** it runs as a Hermes-local (WSL) process reading the token from local Hermes secrets, with no corresponding Railway or Vercel environment variable named for HubSpot credentials

### Requirement: Sync is idempotent and safe to re-run
The system SHALL be safe to re-run the poll cycle repeatedly without creating duplicate HubSpot Contacts or Deals for the same `crm_leads` row.

#### Scenario: Poller runs twice against an unchanged lead
- **WHEN** the poller executes two consecutive cycles and a given `crm_leads` row has not changed between them
- **THEN** no additional HubSpot Contact or Deal is created, and `last_synced_at` is not required to change if no fields differ
