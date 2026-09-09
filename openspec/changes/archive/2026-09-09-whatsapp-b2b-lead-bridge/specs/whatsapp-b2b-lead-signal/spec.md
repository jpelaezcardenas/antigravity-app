## ADDED Requirements

### Requirement: A business-shaped WhatsApp message is detected as business_interest
The system SHALL detect business/persona-jurídica-shaped language (e.g. "empresa", "SAS",
"sociedad", "compañía", "negocio", "contabilidad de mi empresa") in an inbound WhatsApp message via
a new `business_interest` category in `classify_lead_intent()`, separate from the existing
`sales_interest`/`payment_confirmation`/`unknown` categories, without altering how any existing
fixture message already classified under those three categories.

#### Scenario: A message about starting/running a company classifies as business_interest
- **WHEN** a message reads "Somos una SAS y necesitamos ayuda con la contabilidad del negocio"
- **THEN** `classify_lead_intent()` returns `business_interest`

#### Scenario: Existing sales/payment/unknown classifications are unaffected
- **WHEN** any message previously fixture-tested as `sales_interest`, `payment_confirmation`, or
  `unknown` is classified again
- **THEN** it returns the same category as before this change

### Requirement: A business_interest lead is tagged with lead_type on crm_leads
The system SHALL, when `route_lead_message` classifies a message as `business_interest`, set
`crm_leads.lead_type` to a value identifying it as a B2B signal (distinct from the default/NULL
Renta Natural funnel) via `CrmService.whatsapp_intake`/`advance_lead`'s existing tenant-scoped
write path — not a new, independent Supabase query. Once set, `lead_type` SHALL NOT be cleared by
a later message that classifies differently (a lead can be both interested in Renta Natural and
flagged as a business signal — this is a visibility flag, not a stage).

#### Scenario: A business_interest message sets lead_type on a new lead
- **WHEN** a first-time WhatsApp sender's message classifies as `business_interest`
- **THEN** the newly created `crm_leads` row has `lead_type` set to the B2B signal value

#### Scenario: A business_interest message sets lead_type on an existing lead
- **WHEN** an existing `crm_leads` row (created by an earlier, non-business message) receives a
  later message that classifies as `business_interest`
- **THEN** that same row's `lead_type` is updated to the B2B signal value, without creating a
  duplicate row

#### Scenario: lead_type is not cleared by a subsequent non-business message
- **WHEN** a lead whose `lead_type` is already set to the B2B signal value sends a later message
  that classifies as `sales_interest` or `unknown`
- **THEN** `lead_type` remains set to the B2B signal value

### Requirement: A business_interest signal is written to Chatwoot's existing contact attributes
The system SHALL, when `_auto_tag_chatwoot()` runs for a message classified as `business_interest`,
set the contact's `servicio_interes` and `tipo_contribuyente` custom attributes to values
identifying a business/persona-jurídica inquiry, reusing the existing dropdown option values
already provisioned in Chatwoot (confirmed against the live instance at implementation time, not
invented) — extending the existing `_INTENT_TO_SERVICIO_INTERES` mapping and
`tipo_contribuyente`-derivation branch rather than building a new tagging mechanism. This SHALL
remain fire-and-forget: a Chatwoot API failure SHALL NOT raise or block the WhatsApp reply.

#### Scenario: A business_interest message sets the business-related Chatwoot attributes
- **WHEN** `_auto_tag_chatwoot()` runs for a message classified as `business_interest`
- **THEN** the contact's `servicio_interes` and `tipo_contribuyente` attributes are set to the
  business-signal dropdown values, not the existing persona_natural/regimen_simple values

#### Scenario: A Chatwoot API failure while tagging a business lead does not block the reply
- **WHEN** the Chatwoot API call to set business-related attributes fails or times out
- **THEN** the WhatsApp reply is still delivered normally, and no exception propagates

### Requirement: This change does not provision a tenant or sync to HubSpot Deals
The system SHALL NOT create a `tenants`/`b2b_clients` row, and SHALL NOT alter
`hermes-hubspot-poller`'s Deal-stage mapping, as a result of detecting `business_interest`. The
signal exists only to make a `crm_leads` row and its Chatwoot attributes visible to a human
operator, who provisions via the existing `crm-alta-tiered-provisioning` flow if they choose to.

#### Scenario: Detecting business_interest never creates a tenant
- **WHEN** a message classifies as `business_interest`
- **THEN** no `tenants` or `b2b_clients` row is created as a direct result of that classification

#### Scenario: A business_interest lead is never synced to HubSpot as a Deal
- **WHEN** `hermes-hubspot-poller` runs its next tick after a `crm_leads` row has `lead_type` set
- **THEN** that row is synced (if at all) under the same Company-only rule that already applies to
  B2B clients (Decisión #20) — never as a Deal
