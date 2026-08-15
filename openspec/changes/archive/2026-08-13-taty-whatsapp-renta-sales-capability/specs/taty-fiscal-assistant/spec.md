## ADDED Requirements

### Requirement: Taty accepts a WhatsApp sales-lead calling convention
`TatyAgentService` SHALL accept a WhatsApp-channel call shape carrying: recent conversation
history (bridge-supplied, up to `MAX_HISTORY` messages), the lead's known persona fields
(`es_asalariado`/`topes`/`obligado_declarar` from `crm_tax_profiles`), the lead's current CRM
stage, and the renta-persona-natural offer context (price, included scope, required documents).
This is an additive internal calling convention — it does not add a new public HTTP route; the
existing "exactly one authenticated Q&A entry point" invariant (`/api/v1/agents/ask`) is
unaffected, since WhatsApp reaches this service through the existing internal webhook →
`taty_lead_router` → service call path, not through a new public endpoint.

#### Scenario: A WhatsApp lead's persona context shapes the reply
- **WHEN** a WhatsApp lead with `es_asalariado=true` and `obligado_declarar=true` already on file
  asks a follow-up question
- **THEN** Taty's reply is built using that known persona context, not re-asked from scratch

#### Scenario: A WhatsApp lead's turn resolves to Cliente Cero's tenant
- **WHEN** `TatyAgentService` is called from the WhatsApp channel for a `crm_leads` row
- **THEN** the call resolves to Cliente Cero's tenant profile — the same resolution path already
  used for the unauthenticated staging identity — never an unrelated provisioned client's tenant

#### Scenario: No public route is added
- **WHEN** the backend's route table is inspected after this change
- **THEN** `/api/v1/agents/ask` remains the sole public Q&A entry point; no new public route exists
  for the WhatsApp sales-funnel calling convention

### Requirement: Taty can answer from the renta-persona-natural offer without inventing figures
When answering a WhatsApp sales lead, `TatyAgentService` SHALL ground any fiscal figure (thresholds,
deadlines, pricing) in retrieved knowledge-base content or explicitly-provided offer context, and
SHALL NOT state a fiscal figure it cannot trace to one of those sources.

#### Scenario: A confirmed figure is used
- **WHEN** the knowledge base or offer context contains a confirmed threshold or price
- **THEN** Taty's reply may state that figure

#### Scenario: An unconfirmed figure is never invented
- **WHEN** no retrieved content or offer context confirms a specific fiscal figure the lead asked
  about
- **THEN** Taty's reply does not state a specific number for it, and instead offers to connect the
  lead with a human advisor
