## MODIFIED Requirements

### Requirement: Inbound sales-intent messages create or update a lead and advance NUEVOS to PROSPECTOS
The system SHALL route a normalized inbound WhatsApp message to `route_lead_message(lead_id,
message)`, which SHALL find-or-create a `crm_leads` row keyed by `tenant_id` AND `whatsapp_phone`
(never by `whatsapp_phone` alone), classify the message's intent — now one of `sales_interest`,
`payment_confirmation`, `business_interest`, or `unknown` — and SHALL advance the lead from
`NUEVOS` to `PROSPECTOS` (via the existing, unmodified `CrmService.advance_lead`) when
`sales_interest` is detected. A `business_interest` classification SHALL NOT advance or regress the
lead's `stage` — it only sets `crm_leads.lead_type` (see `whatsapp-b2b-lead-signal`) — since a B2B
signal is not itself a Renta Natural sale. A lead already past `NUEVOS` SHALL NOT be advanced or
regressed by this routing, regardless of which intent is detected.

When a message matches both `business_interest` and `sales_interest`/`payment_confirmation`
keyword sets, `payment_confirmation` SHALL take precedence, then `business_interest`, then
`sales_interest` — a payment-related message must never be reclassified as a business inquiry.

The find-or-create step SHALL delegate to `CrmService.whatsapp_intake` (the same tenant-scoped
implementation the Chatwoot-Hermes bridge uses) rather than running an independent, duplicate
Supabase query — this is the single implementation of "find-or-create a lead by WhatsApp phone" in
the codebase.

#### Scenario: A first-time WhatsApp sender becomes a new NUEVOS lead
- **WHEN** a WhatsApp message arrives from a phone number with no existing `crm_leads` row for the
  resolved tenant
- **THEN** a new `crm_leads` row is created with `stage="NUEVOS"`, that tenant's `tenant_id`, and
  that `whatsapp_phone`

#### Scenario: Sales intent advances a NUEVOS lead to PROSPECTOS
- **WHEN** a message expressing interest in Renta Natural arrives from a lead currently
  `stage="NUEVOS"`
- **THEN** the lead's stage becomes `PROSPECTOS`

#### Scenario: Business interest does not advance the lead's stage
- **WHEN** a message expressing business/persona-jurídica interest (e.g. "somos una SAS,
  necesitamos contabilidad") arrives from a lead currently `stage="NUEVOS"`
- **THEN** the lead's `stage` remains `NUEVOS` — only `crm_leads.lead_type` is set

#### Scenario: A message matching both payment and business keywords classifies as payment
- **WHEN** a message contains both a payment-confirmation keyword and a business keyword
- **THEN** the message classifies as `payment_confirmation`, not `business_interest`

#### Scenario: A lead past NUEVOS is not re-advanced or regressed
- **WHEN** a message arrives from a lead whose stage is already `PROSPECTOS`, `POR_APROBAR`, or
  `LISTOS_CONTADORA`
- **THEN** the lead's stage is left unchanged by this routing, regardless of detected intent

#### Scenario: The lookup never matches a lead belonging to a different tenant
- **WHEN** a `crm_leads` row exists with a matching `whatsapp_phone` but a different `tenant_id`
  than the one resolved for this inbound message
- **THEN** that row is NOT returned or reused; a new row is created for the correct tenant instead
