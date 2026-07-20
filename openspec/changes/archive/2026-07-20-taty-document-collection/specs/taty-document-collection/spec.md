## ADDED Requirements

### Requirement: Payment approval triggers a proactive RUT request
The system SHALL, immediately upon `CrmService.approve_payment` transitioning a lead to
`LISTOS_CONTADORA`, set `rut_status='requested'` and send the lead a WhatsApp message asking for
their RUT.

#### Scenario: Approving a payment triggers the RUT request
- **WHEN** an admin approves a lead's payment via `POST /leads/{lead_id}/approve-payment`
- **THEN** the lead's `crm_tax_profiles.rut_status` becomes `requested` and an outbound WhatsApp
  message requesting the RUT is sent

### Requirement: Documents are collected sequentially — RUT first, then extractos
The system SHALL treat an incoming WhatsApp document/image message as the RUT if
`rut_status` is not yet `collected`, storing it and setting `rut_status='collected'`, then
immediately requesting extractos (`extractos_status='requested'`). Once `rut_status='collected'`,
the next incoming document SHALL be treated as extractos, stored, and marked
`extractos_status='collected'`.

#### Scenario: The first document received after a payment approval is treated as the RUT
- **WHEN** a document/image message arrives from a lead whose `rut_status` is `requested`
- **THEN** the document is stored, `rut_status` becomes `collected`, and the lead is asked for
  extractos (`extractos_status` becomes `requested`)

#### Scenario: A document received after the RUT is treated as extractos
- **WHEN** a document/image message arrives from a lead whose `rut_status='collected'` and
  `extractos_status='requested'`
- **THEN** the document is stored and `extractos_status` becomes `collected`

#### Scenario: A document arriving before payment approval is not processed as RUT/extractos
- **WHEN** a document/image message arrives from a lead whose `crm_leads.stage` is not
  `LISTOS_CONTADORA`
- **THEN** the document is acknowledged but not stored as RUT/extractos, and no status field
  changes

### Requirement: Documents are stored privately with signed, time-limited access
The system SHALL store received documents in a private Supabase Storage bucket
(`crm-tax-documents`), admin-only accessible, and SHALL generate only short-lived signed URLs for
viewing — never a public or permanent URL.

#### Scenario: A stored document is only accessible via a signed URL
- **WHEN** a document has been stored for a lead
- **THEN** it is not publicly readable, and a signed URL generated for it expires after a bounded
  time window
