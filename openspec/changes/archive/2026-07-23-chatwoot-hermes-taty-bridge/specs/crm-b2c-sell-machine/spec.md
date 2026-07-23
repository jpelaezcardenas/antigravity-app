## ADDED Requirements

### Requirement: A WhatsApp contact can be looked up or registered as a lead
The system SHALL expose `POST /api/v1/crm/leads/whatsapp-intake` accepting a `whatsapp_phone`,
tenant-scoped to the calling caller's tenant. It SHALL find an existing `crm_leads` row matching
the normalized phone number, or create a new one with `stage: "NUEVOS"` if none exists, and SHALL
return `{lead_id, is_new, stage}`.

#### Scenario: First contact from a new phone number creates a lead
- **WHEN** `POST /api/v1/crm/leads/whatsapp-intake` is called with a `whatsapp_phone` not present in
  `crm_leads` for the tenant
- **THEN** a new `crm_leads` row is created with `stage: "NUEVOS"` and the response includes
  `is_new: true`

#### Scenario: Repeat contact from a known phone number is found, not duplicated
- **WHEN** `POST /api/v1/crm/leads/whatsapp-intake` is called with a `whatsapp_phone` already present
  in `crm_leads` for the tenant
- **THEN** no new row is created, the existing lead's `lead_id` and current `stage` are returned,
  and the response includes `is_new: false`

#### Scenario: Call requires tenant-scoped authentication
- **WHEN** `POST /api/v1/crm/leads/whatsapp-intake` is called without a valid tenant-scoped bearer
  token
- **THEN** the request fails with a 4xx error and no `crm_leads` row is read or written
