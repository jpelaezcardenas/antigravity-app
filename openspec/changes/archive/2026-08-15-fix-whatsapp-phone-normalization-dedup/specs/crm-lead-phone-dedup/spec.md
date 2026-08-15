## ADDED Requirements

### Requirement: Phone normalization collapses +/no-+ formats to one canonical value
The system SHALL normalize a WhatsApp phone number to a single canonical form (digits only, no `+`) before using it to look up or create a `crm_leads` row, regardless of whether the input included a leading `+`.

#### Scenario: Same number with and without leading plus
- **WHEN** `_normalize_whatsapp_phone` is called once with `"+573001234567"` and once with `"573001234567"`
- **THEN** both calls return the identical normalized string

### Requirement: WhatsApp intake deduplicates by normalized phone
The system SHALL find an existing `crm_leads` row by normalized phone before creating a new one, regardless of the `+`-prefix format the caller supplied.

#### Scenario: Lead already exists with the other phone format
- **WHEN** `whatsapp_intake` is called with `"573001234567"` and a `crm_leads` row already exists with `whatsapp_phone` originally created from `"+573001234567"`
- **THEN** the existing row is returned (`is_new: False`) and no new row is created

### Requirement: Landing-quiz lead capture reuses the same deduped intake path
The system SHALL create/find `crm_leads` rows from the Renta diagnóstico quiz through the same normalized, tenant-scoped, deduped path the WhatsApp channel uses — not a separate, unvalidated insert.

#### Scenario: Quiz submission with a phone already known from WhatsApp
- **WHEN** `run_renta_diagnostico` is called with a phone number that already has a `crm_leads` row from the WhatsApp channel
- **THEN** no duplicate `crm_leads` row is created for that phone

#### Scenario: Quiz submission with a new phone
- **WHEN** `run_renta_diagnostico` is called with a phone number that has no existing `crm_leads` row
- **THEN** a new `crm_leads` row is created with the correct schema columns (`whatsapp_phone`, `full_name`, `stage`, `tenant_id` resolved to the real Cliente Cero tenant)
