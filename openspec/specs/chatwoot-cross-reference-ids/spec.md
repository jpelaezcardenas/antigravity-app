# chatwoot-cross-reference-ids Specification

## Purpose
TBD - created by archiving change chatwoot-hubspot-supabase-cross-ids. Update Purpose after archive.
## Requirements
### Requirement: Cross-reference attributes pushed after HubSpot sync
The system SHALL, after successfully syncing a `crm_leads` row's Contact and Deal to HubSpot, find the matching Chatwoot contact by phone number and set its `supabase_customer_id` and `hubspot_contact_id` custom attributes.

#### Scenario: Lead's phone matches an existing Chatwoot contact
- **WHEN** a `crm_leads` row is successfully synced to HubSpot and a Chatwoot contact exists with the same phone number
- **THEN** that Chatwoot contact's custom attributes are updated with `supabase_customer_id` (the lead's Supabase id) and `hubspot_contact_id` (the synced HubSpot Contact id)

#### Scenario: No matching Chatwoot contact exists
- **WHEN** a `crm_leads` row is successfully synced to HubSpot and no Chatwoot contact exists with that phone number
- **THEN** no Chatwoot contact is created and no attributes are set

### Requirement: Chatwoot failure does not block the HubSpot sync
The system SHALL NOT let a Chatwoot API failure prevent `crm_leads.hubspot_contact_id`/`hubspot_deal_id`/`last_synced_at` from being persisted.

#### Scenario: Chatwoot is unreachable
- **WHEN** the Chatwoot contact-attribute call fails (network error, non-2xx response)
- **THEN** the lead's HubSpot sync still completes and `last_synced_at` is still updated in Supabase

