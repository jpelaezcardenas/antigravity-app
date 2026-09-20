## ADDED Requirements

### Requirement: Three-step express flow at a new route
The system SHALL serve a 3-step diagnostic flow at `contexia.online/wizard/iva-ecom`, separate from and non-interfering with the existing 8-step flow at `contexia.online/wizard`.

#### Scenario: Visitor loads the express diagnostic route
- **WHEN** a visitor navigates to `/wizard/iva-ecom`
- **THEN** the page renders Step 1 ("Números") without affecting the state of the existing 8-step flow's store

#### Scenario: Existing 8-step flow is unaffected
- **WHEN** a visitor separately navigates to `/wizard` (the existing flow)
- **THEN** it behaves exactly as before this change, with no new fields, steps, or store keys

### Requirement: Step 1 — Números
The system SHALL collect ventas mensuales, gasto mensual en Meta Ads, and margen bruto aproximado.

#### Scenario: Visitor enters valid numeric inputs
- **WHEN** the visitor enters positive numeric values for all three fields
- **THEN** the "Siguiente" control becomes enabled and advances to Step 2

### Requirement: Step 2 — Formalización
The system SHALL collect whether the visitor operates as Persona Natural or SAS, and whether they issue electronic invoices.

#### Scenario: Visitor selects formalization status
- **WHEN** the visitor selects a persona type and an invoicing answer
- **THEN** the "Siguiente" control becomes enabled and advances to Step 3

### Requirement: Step 3 — Instant result and WhatsApp handoff
The system SHALL compute and display, entirely client-side with no backend round-trip, an estimated monthly IVA amount and a red/green verdict, then offer a WhatsApp CTA.

#### Scenario: Result computed instantly
- **WHEN** Step 3 renders
- **THEN** it displays `ivaPerdidoMensual = gastoMetaAdsMensual * 0.19` and a verdict color based on whether `ventasMensuales * 12` exceeds 3,500 UVT (the IVA-responsibility threshold, using the existing `UVT_2026` constant), computed without calling any API for the calculation itself

#### Scenario: Estimate is disclosed, not stated as unconditional fact
- **WHEN** the result is displayed
- **THEN** the copy frames the figure as an estimate conditional on IVA-responsibility status, never as an unconditional "estás perdiendo $X" claim

#### Scenario: WhatsApp CTA reflects the finding
- **WHEN** the visitor clicks the WhatsApp button
- **THEN** it opens `wa.me` with the existing production Contexia number and a pre-filled message referencing their estimated IVA finding and the "primeros 50 cupos" community offer

### Requirement: WhatsApp CTA is the primary, ungated conversion action
The system SHALL NOT require an email or any additional field before the visitor can click the WhatsApp CTA on Step 3 — the WhatsApp click, not a form submission, is this flow's real conversion event (design.md D6).

#### Scenario: Visitor clicks WhatsApp without entering an email
- **WHEN** Step 3 renders and the visitor has not filled the optional email field
- **THEN** the WhatsApp button is still enabled and opens `wa.me` normally

### Requirement: Optional best-effort lead capture, reusing the existing endpoint
The system MAY capture the lead's contact info and the three steps' inputs via the existing `POST /api/leads/save` endpoint, only if the visitor voluntarily fills an optional email field on Step 3, tagged `source=iva_ecom_express`, without modifying that endpoint's contract.

#### Scenario: Visitor provides an email
- **WHEN** the visitor fills the optional "envíame el resultado por email" field on Step 3
- **THEN** a single call to the existing lead-save endpoint fires with `source: "iva_ecom_express"` and the three steps' inputs nested under a `metadata.iva_ecom_inputs` key

#### Scenario: Visitor does not provide an email
- **WHEN** the visitor leaves the optional email field blank
- **THEN** no call to the lead-save endpoint fires, and no error is shown

#### Scenario: No new backend endpoint or schema
- **WHEN** this flow is implemented
- **THEN** no new API route, database table, or migration is introduced — the existing `leads` table and its `source`/`metadata` columns are reused unmodified

### Requirement: This flow's leads are not synced to the CRM pipeline
The system SHALL NOT claim or imply that leads captured via this flow's optional email field appear in `crm_leads`, HubSpot, or the Búnker CRM Kanban. As of this change, `POST /api/leads/save` fails for everyone (pre-existing, unrelated schema bug — design.md D7), so this scenario holds regardless.

#### Scenario: Operator checks the CRM Kanban for an ecom-flow lead
- **WHEN** a lead completes this flow via the optional email field only (no WhatsApp message sent)
- **THEN** that lead does NOT appear in the Búnker's B2C/B2B CRM Kanban — only leads who message WhatsApp reach Taty/Chatwoot and, from there, the CRM pipeline

### Requirement: Optional lead-save endpoint failure never breaks the page
The system SHALL show a graceful, non-blocking message if the optional email save fails, and SHALL NOT let that failure affect the WhatsApp CTA, the displayed result, or any other part of the page.

#### Scenario: Lead-save endpoint returns an error
- **WHEN** the visitor submits the optional email field and the underlying call fails (e.g. HTTP 500)
- **THEN** the page shows a short message pointing back to the WhatsApp CTA, with no uncaught error, no blank page, and no effect on any other visible state
