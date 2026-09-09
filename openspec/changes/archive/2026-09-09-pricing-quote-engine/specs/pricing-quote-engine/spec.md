## ADDED Requirements

### Requirement: UVT Values Are Stored, Versioned By Year, And Never Hardcoded
The system SHALL persist Colombian UVT values in a `uvt_values` table keyed by tax year, and
every calculation that depends on a UVT SHALL take the tax year as a parameter and read the
value from that table. The system SHALL NOT define a UVT amount as a code constant.

#### Scenario: A calculation resolves the UVT for the requested tax year
- **WHEN** a pre-quote is computed for tax year 2025
- **THEN** the system reads `uvt_values` for year 2025 and uses $49.799 (Resolución DIAN 000193
  de 2024) as the UVT for every threshold in that response

#### Scenario: Two UVT values coexist without interfering
- **WHEN** the table holds both year 2025 ($49.799) and year 2026 ($52.374, Resolución DIAN
  000238 del 15-dic-2025)
- **THEN** a calculation for tax year 2025 uses only the 2025 value, and a calculation for tax
  year 2026 uses only the 2026 value

#### Scenario: A missing UVT year is an explicit failure, not a fallback
- **WHEN** a pre-quote is requested for a tax year with no row in `uvt_values`
- **THEN** the system returns `estado: "uvt_no_disponible"` echoing the requested year, and does
  NOT substitute another year's UVT or any hardcoded default

### Requirement: Agreed Professional Fee And Service Band Are Recorded Per Client
The system SHALL record, for each B2B client, both the agreed monthly professional fee
(`monthly_fee_cents`, already present) and the service band it was quoted under
(`service_band`), constrained to `micro`, `estandar`, or `complejo`.

#### Scenario: A band is persisted alongside the fee
- **WHEN** an operator records a client's agreed fee and selects a service band
- **THEN** both `monthly_fee_cents` and `service_band` are stored on that client's `b2b_clients`
  row and returned by the roster listing

#### Scenario: An invalid band is rejected
- **WHEN** a write supplies a `service_band` outside `micro | estandar | complejo`
- **THEN** the request is rejected with a 400 naming the allowed values, not a raw database
  constraint violation

#### Scenario: Band and fee remain optional
- **WHEN** a client is created or edited without a band or a fee
- **THEN** both columns stay null and no default band is inferred from the fee amount

### Requirement: Pre-Quote Endpoint Is Scoped To The Authenticated Caller's Own Tenant
The system SHALL expose `GET /api/v1/pricing/pre-cotizacion`, resolving the tenant exclusively
via the shared `resolve_request_tenant_scope()` contract, and SHALL NOT accept a tenant
identifier as a query parameter.

#### Scenario: Authenticated caller with a resolved tenant gets a pre-quote
- **WHEN** an authenticated user whose tenant resolves successfully calls the endpoint
- **THEN** the system returns 200 with a payload computed exclusively from that tenant's own
  Shadow GL rows

#### Scenario: Authenticated caller without a resolvable tenant gets 404
- **WHEN** an authenticated user whose tenant cannot be resolved calls the endpoint
- **THEN** the system returns 404 and never falls back to Cliente Cero's data

#### Scenario: Unauthenticated request is rejected
- **WHEN** a request without a valid session token calls the endpoint
- **THEN** the system returns 401

### Requirement: Pre-Quote Reports Revenue And Movement Volume From The Shadow GL
The system SHALL derive annualised gross revenue and average monthly journal-line volume from
the caller's own `erp_journal_entries` / `erp_journal_lines` rows over a trailing twelve-month
window.

#### Scenario: Revenue is reported in whole COP and in UVT
- **WHEN** a pre-quote is computed
- **THEN** the response contains `ingresos_anualizados_cop` in whole Colombian pesos and
  `ingresos_anualizados_uvt` expressing the same figure in UVT of the requested tax year

#### Scenario: Partial history is annualised transparently
- **WHEN** a tenant has fewer than twelve months of history but at least the minimum required
- **THEN** the observed revenue is scaled to twelve months and `meses_observados` reports how
  many months were actually observed, so the extrapolation factor is visible

#### Scenario: Movement volume is a real count
- **WHEN** a pre-quote is computed
- **THEN** `movimientos_mes` is the average monthly count of that tenant's `erp_journal_lines`
  rows in the observed window

### Requirement: Declarant Threshold Reports Only The Criterion It Can Observe
The system SHALL evaluate the filing-obligation threshold using the 1.400 UVT gross-revenue
criterion only, and SHALL declare in the response which criteria it did not evaluate.

#### Scenario: Crossing the revenue threshold is reported
- **WHEN** a tenant's annualised revenue exceeds 1.400 UVT of the requested tax year
- **THEN** `supera_umbral_declarante` is `true` and `umbral_declarante_uvt` / 
  `umbral_declarante_cop` report the exact threshold applied

#### Scenario: Not crossing the threshold is never presented as "not obligated"
- **WHEN** a tenant's annualised revenue does not exceed 1.400 UVT
- **THEN** `supera_umbral_declarante` is `false`, `criterio_evaluado` is `"ingresos_brutos"`, and
  `criterios_no_evaluables` names the unevaluated criteria — compras y consumos, consignaciones
  y depósitos, consumos con tarjeta de crédito, patrimonio bruto, and responsabilidad de IVA

#### Scenario: The patrimony threshold is not fabricated
- **WHEN** any pre-quote is produced
- **THEN** no patrimony figure is computed or compared against the 4.500 UVT threshold, and
  patrimonio bruto appears in `criterios_no_evaluables`

### Requirement: Suggested Band Is Partial By Construction And Declares Its Missing Drivers
The system SHALL return a suggested service band together with a confidence level and an
explicit list of drivers it could not observe, and SHALL NOT estimate payroll or labour load.

#### Scenario: Payroll is always reported as a missing driver
- **WHEN** any pre-quote is produced
- **THEN** `drivers_faltantes` always contains the payroll/labour-load driver, and no field of
  the response contains an estimated, inferred, or defaulted payroll figure

#### Scenario: Confidence is never "alta"
- **WHEN** any pre-quote is produced with a suggested band
- **THEN** `confianza` is `"media"` or `"baja"`, never `"alta"`, because the payroll driver that
  forms half the fee criterion is structurally absent from the data model

#### Scenario: A micro suggestion is reported at low confidence
- **WHEN** the heuristic suggests the `micro` band
- **THEN** `confianza` is `"baja"`, because Micro is defined by the absence of labour load — the
  one driver the engine cannot observe

#### Scenario: Insufficient history yields an explicit state, not a band
- **WHEN** a tenant has fewer than three distinct months of journal activity in the trailing
  twelve months
- **THEN** the system returns `estado: "sin_historico_suficiente"` with `banda_sugerida: null`,
  and never an invented band

### Requirement: The Pre-Quote Engine Does Not Set Prices Or Change State
The system SHALL treat the suggested band as advisory input for a licensed accountant, and the
pre-quote endpoint SHALL NOT write any data.

#### Scenario: A successful pre-quote changes nothing
- **WHEN** the endpoint returns a pre-quote
- **THEN** no `b2b_clients` row is updated, no `approval_queue` entry is enqueued, and no
  telemetry or audit row is written

#### Scenario: The band never becomes the agreed band automatically
- **WHEN** a pre-quote suggests a band for a tenant that is also a B2B client
- **THEN** that client's stored `service_band` is unchanged until an operator records it
  explicitly
