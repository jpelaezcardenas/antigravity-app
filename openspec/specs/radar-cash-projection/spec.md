# radar-cash-projection Specification

## Purpose
TBD - created by archiving change radar-cash-projection-13w. Update Purpose after archive.
## Requirements
### Requirement: 13-Week Cash Projection Endpoint
The system SHALL expose `GET /api/v1/radar/proyeccion-caja`, resolving the tenant from the
authenticated caller via the shared tenant-resolution contract
(`resolve_request_tenant_scope`), and SHALL NOT accept a tenant identifier as a query
parameter.

#### Scenario: Authenticated caller with a resolved tenant gets a projection
- **WHEN** an authenticated user whose tenant resolves successfully calls
  `GET /api/v1/radar/proyeccion-caja`
- **THEN** the system returns a 200 response containing `client_tenant_id`, `generado_en`,
  `metodologia`, and either a 13-item `semanas` array or an `estado` field explaining why
  none was produced

#### Scenario: Authenticated caller without a resolvable tenant gets a graceful empty response
- **WHEN** an authenticated user's tenant cannot be resolved calls
  `GET /api/v1/radar/proyeccion-caja`
- **THEN** the system returns 200 with `estado: "tenant_no_resuelto"` and no `semanas`,
  matching the read-only-endpoint pattern already used by `GET /centinela/alerts` (the 404
  anti-enumeration policy from Decision #17 applies only to write/ownership-check routes
  like Approval Queue, not to read-only projection endpoints), and never falls back to
  Cliente Cero data

#### Scenario: Unauthenticated request is rejected
- **WHEN** a request without a valid session token calls `GET /api/v1/radar/proyeccion-caja`
- **THEN** the system returns 401

### Requirement: Tenant Isolation
The system SHALL ensure that a tenant's 13-week projection is computed exclusively from
that tenant's own `erp_journal_entries`/`erp_journal_lines`/`dian_xml_documents` rows.

#### Scenario: Tenant A never sees Tenant B's projection data
- **WHEN** Tenant A and Tenant B both have Shadow GL history and Tenant A calls the
  endpoint
- **THEN** every value in Tenant A's response is derived solely from rows scoped to
  Tenant A's `tenant_id`, verified by an automated test asserting no cross-tenant leakage

### Requirement: Honest Methodology Disclosure
The system SHALL declare its projection methodology explicitly in the response and SHALL
NOT claim a methodology it does not implement.

#### Scenario: Methodology reflects the absence of CxC/CxP data
- **WHEN** the projection is computed for any tenant
- **THEN** the response's `metodologia` field is `"solo_historico"`, since no
  accounts-receivable/payable table with due dates exists in the data model

#### Scenario: Estimated future tax is never fabricated
- **WHEN** the projection response is built
- **THEN** the `impuesto_futuro_estimado` field is `null`, since no real tax-forecast
  calculation exists in the backend, and the field is never populated with a mocked or
  invented number

### Requirement: Decreasing Confidence by Week
The system SHALL assign each of the 13 weeks a confidence level that reflects how far the
week is from the present and SHALL NOT assign a confidence level implying grounding the
methodology does not have.

#### Scenario: Near-term weeks get medium confidence
- **WHEN** the projection is computed with sufficient history
- **THEN** weeks 1 through 4 are marked `confianza: "media"`

#### Scenario: Far-term weeks get low confidence
- **WHEN** the projection is computed with sufficient history
- **THEN** weeks 5 through 13 are marked `confianza: "baja"`

#### Scenario: No week is ever marked high confidence
- **WHEN** the projection is computed under the `solo_historico` methodology
- **THEN** no week in the `semanas` array is marked `confianza: "alta"`

### Requirement: Honest Insufficient-History State
The system SHALL detect when a tenant lacks enough Shadow GL history to support a
trend-based projection and SHALL return an explicit empty state instead of a fabricated
projection.

#### Scenario: New tenant with fewer than 4 weeks of history
- **WHEN** a tenant has fewer than 4 distinct weeks of `erp_journal_entries` activity
- **THEN** the response sets `estado: "sin_historico_suficiente"`, omits the `semanas`
  array, and includes a plain-language explanation of when to check back

### Requirement: Performance Budget
The system SHALL respond to `GET /api/v1/radar/proyeccion-caja` within 2 seconds under
normal load.

#### Scenario: Response time within budget
- **WHEN** the endpoint is called for a tenant with up to 12 weeks of Shadow GL history
- **THEN** the response completes in under 2 seconds, verified by an automated timing
  assertion in the test suite

### Requirement: Radar Screen Cash Projection Section
The `/app/radar` screen SHALL render the 13-week projection as a line chart with a
plain-language narrative alert, and SHALL NOT display invented or hardcoded data.

#### Scenario: Tenant with a projection sees a chart and narrative
- **WHEN** a user with sufficient Shadow GL history opens `/app/radar`
- **THEN** the screen renders a 13-point line chart plus an `alerta_narrativa` in
  Colombian-Spanish, plain-language copy (no technical jargon), formatted as
  `$X.XXX.XXX COP`, sourced from the live endpoint response

#### Scenario: Tenant without sufficient history sees an honest empty state
- **WHEN** a user whose tenant returns `estado: "sin_historico_suficiente"` opens
  `/app/radar`
- **THEN** the screen shows a plain-language message explaining that not enough history
  exists yet, with no chart and no invented numbers

#### Scenario: Screen is usable on mobile
- **WHEN** the cash projection section is viewed on a mobile-width viewport
- **THEN** the chart and narrative remain fully readable and usable without horizontal
  scrolling

