## MODIFIED Requirements

### Requirement: Detected persona state is persisted to the lead's tax profile
The system SHALL persist detected persona fields (`es_asalariado`, `topes`, `obligado_declarar`)
into the lead's `crm_tax_profiles` row via the existing, unmodified `CrmService.update_tax_profile`,
creating an empty tax-profile row first if none exists yet for that lead. `topes` entries SHALL be
merged with any existing `topes` on the profile, never overwritten wholesale. `obligado_declarar`
SHALL be recomputed as a preliminary signal (not a legally authoritative determination) whenever
`topes` changes, comparing the known `ingresos`/`consignaciones` amount against
`core.constants.UMBRAL_RENTA_COP`.

#### Scenario: Persona state is saved for a lead with no existing tax profile
- **WHEN** a message reveals `es_asalariado=true` for a lead with no `crm_tax_profiles` row yet
- **THEN** a `crm_tax_profiles` row is created for that lead with `es_asalariado=true`

#### Scenario: A topes amount mentioned in a message is merged, not overwritten
- **WHEN** a lead's tax profile already has `topes={"consignaciones": 50000000}` and a new message
  mentions ingresos of 20,000,000
- **THEN** the profile's `topes` becomes `{"consignaciones": 50000000, "ingresos": 20000000}` —
  the existing `consignaciones` entry is preserved

#### Scenario: obligado_declarar is set true when a known topes amount meets the renta threshold
- **WHEN** a lead's `topes` includes an `ingresos` or `consignaciones` value greater than or equal
  to `UMBRAL_RENTA_COP`
- **THEN** the profile's `obligado_declarar` becomes `true`

#### Scenario: obligado_declarar is set false when known topes amounts stay below the threshold
- **WHEN** a lead's `topes` includes only `ingresos`/`consignaciones` values below
  `UMBRAL_RENTA_COP`
- **THEN** the profile's `obligado_declarar` becomes `false`

#### Scenario: A message with no detectable topes amount leaves obligado_declarar unset
- **WHEN** a message contains no category keyword + peso-amount pair
- **THEN** `topes` and `obligado_declarar` are left unchanged on the profile
