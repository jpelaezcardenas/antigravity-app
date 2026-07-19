## ADDED Requirements

### Requirement: B2C lead funnel is persisted with a fixed 4-stage pipeline
The system SHALL persist B2C ("Renta Natural") leads in `crm_leads`, scoped to the Cliente Cero
tenant, each with a `stage` constrained to exactly `NUEVOS`, `PROSPECTOS`, `POR_APROBAR`, or
`LISTOS_CONTADORA`. The pipeline SHALL be retrievable via `GET /api/v1/crm/b2c/pipeline` as a
board-shaped response (columns of leads).

#### Scenario: Listing the pipeline returns leads grouped by stage
- **WHEN** an admin calls `GET /api/v1/crm/b2c/pipeline` with `CRM_CANONICAL` enabled and Supabase
  reachable
- **THEN** the response includes `source: "supabase"` and a `columns` array with one entry per
  stage, each containing the leads currently in that stage

#### Scenario: Supabase unreachable falls back to demo data
- **WHEN** `GET /api/v1/crm/b2c/pipeline` is called and Supabase is not configured or the query
  fails
- **THEN** the response includes `source: "demo_fallback"` with a non-empty `columns` array, and
  the request does not error

### Requirement: A lead can advance to any valid stage
The system SHALL expose `POST /api/v1/crm/leads/{id}/advance` accepting a target `stage` (one of
the 4 valid values) and SHALL persist the new stage on the corresponding `crm_leads` row.

#### Scenario: Advancing a lead updates its stage
- **WHEN** an admin calls `POST /api/v1/crm/leads/{id}/advance` with `{"stage": "PROSPECTOS"}` for
  a lead currently in `NUEVOS`
- **THEN** the lead's `stage` is updated to `PROSPECTOS` and a subsequent
  `GET /api/v1/crm/b2c/pipeline` reflects it in the `PROSPECTOS` column

#### Scenario: Advancing to an invalid stage is rejected
- **WHEN** `POST /api/v1/crm/leads/{id}/advance` is called with a `stage` value outside the 4 valid
  values
- **THEN** the request fails with a 4xx error and the lead's stage is unchanged

### Requirement: Each lead has a persisted tax-profile memory
The system SHALL persist a 1:1 tax-profile record per lead in `crm_tax_profiles` (at least
`es_asalariado`, `topes`, `rut_status`, `extractos_status`, `obligado_declarar`), retrievable via
`GET /api/v1/crm/leads/{id}/tax-profile` and updatable via
`PATCH /api/v1/crm/leads/{id}/tax-profile`.

#### Scenario: Reading a lead's tax profile
- **WHEN** an admin calls `GET /api/v1/crm/leads/{id}/tax-profile` for a seeded lead
- **THEN** the response includes the seeded `es_asalariado`, `topes`, `rut_status`, and
  `extractos_status` values for that lead

#### Scenario: Updating a lead's tax profile
- **WHEN** an admin calls `PATCH /api/v1/crm/leads/{id}/tax-profile` with an updated `rut_status`
- **THEN** the stored tax-profile row reflects the new value on a subsequent read

### Requirement: Payment approval is a dedicated HITL gate that advances the lead
The system SHALL expose `POST /api/v1/crm/leads/{id}/approve-payment`, which SHALL only be valid
for a lead currently in the `POR_APROBAR` stage, and SHALL, on success: advance the lead's stage to
`LISTOS_CONTADORA`, mark the lead's associated `crm_wompi_transactions` row `status: "APPROVED"`,
and stamp `approved_by` and `approved_at` on that transaction row.

#### Scenario: Approving payment for a POR_APROBAR lead advances it and stamps the transaction
- **WHEN** an admin calls `POST /api/v1/crm/leads/{id}/approve-payment` for a lead in
  `POR_APROBAR` with an associated pending `crm_wompi_transactions` row
- **THEN** the lead's stage becomes `LISTOS_CONTADORA`, the transaction's `status` becomes
  `APPROVED`, and `approved_by`/`approved_at` are set

#### Scenario: Approving payment for a lead not in POR_APROBAR is rejected
- **WHEN** `POST /api/v1/crm/leads/{id}/approve-payment` is called for a lead whose stage is
  `NUEVOS`, `PROSPECTOS`, or `LISTOS_CONTADORA`
- **THEN** the request fails with a 4xx error and neither the lead's stage nor any transaction row
  is modified

### Requirement: B2C funnel data is admin-only
Access to `crm_leads`, `crm_tax_profiles`, and `crm_wompi_transactions` at the database layer SHALL
be restricted by Row Level Security to users with an admin-tier role on the owning tenant, matching
the `b2b_clients`/`b2b_payments` RLS pattern established in the `crm-b2b-retainers` capability.

#### Scenario: Non-admin database role cannot read B2C tables directly
- **WHEN** a Supabase query against `crm_leads`, `crm_tax_profiles`, or `crm_wompi_transactions` is
  executed as a user without an admin-tier `user_roles.role` entry for the tenant
- **THEN** Row Level Security denies the read (no rows returned)

### Requirement: CRM/Ventas Búnker section renders a live B2C Kanban board
The Búnker "CRM / Ventas" section's "B2C / Renta Natural" tab SHALL render a Kanban board with one
column per funnel stage, sourced from `GET /api/v1/crm/b2c/pipeline`, with a click-to-advance
control per lead card and an "Aprobar Pago" action visible only on cards in the `POR_APROBAR`
column. The tab SHALL NOT display the prior static "Próximamente" placeholder text.

#### Scenario: Admin opens the B2C tab and sees the live Kanban board
- **WHEN** an authenticated admin navigates to `/app/bunker` → "CRM / Ventas" → "B2C / Renta
  Natural"
- **THEN** four columns are visible (Nuevos, Prospectos, Por Aprobar, Listos Contadora), each
  populated with the leads currently in that stage, and no "Próximamente" placeholder text remains

#### Scenario: Advancing a lead from the UI updates its column
- **WHEN** an admin clicks the advance action on a lead card in "Nuevos"
- **THEN** the lead moves to the "Prospectos" column after the board reloads

#### Scenario: Approving payment from the UI moves the lead to the final column
- **WHEN** an admin clicks "Aprobar Pago" on a lead card in "Por Aprobar"
- **THEN** the lead moves to the "Listos Contadora" column after the board reloads
