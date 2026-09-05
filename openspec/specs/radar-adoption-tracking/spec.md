# radar-adoption-tracking Specification

## Purpose
TBD - created by archiving change radar-adoption-tracking. Update Purpose after archive.
## Requirements
### Requirement: Record Radar de Caja opens per tenant and day
The system SHALL record one row per tenant, user and calendar day when a caller successfully
retrieves the 13-week cash projection, so that weekly adoption can be computed.

#### Scenario: First open of the day is recorded
- **WHEN** an authenticated caller with a resolved tenant retrieves
  `GET /api/v1/radar/proyeccion-caja` for the first time on a given day
- **THEN** a row is written to `radar_module_opens` carrying that tenant, that user and that
  date

#### Scenario: Repeated opens on the same day do not create duplicate rows
- **WHEN** the same caller retrieves the projection several more times on the same day
- **THEN** the total number of rows for that tenant, user and date remains exactly one

#### Scenario: A caller without a resolved tenant records nothing
- **WHEN** an authenticated caller whose tenant cannot be resolved calls the endpoint
- **THEN** no row is written, and the response is the usual `tenant_no_resuelto` body

### Requirement: Telemetry Never Degrades the Projection
The system SHALL treat the adoption write as best-effort, and SHALL return the cash
projection unchanged if recording fails for any reason.

#### Scenario: The projection still succeeds when recording raises
- **WHEN** writing the adoption row raises an error (for example the table does not exist
  because the migration has not been applied, or the write is rejected)
- **THEN** the endpoint still returns its normal 200 response with the projection body, and
  the failure is logged rather than surfaced to the caller

### Requirement: Tenant-Scoped Row Level Security
The `radar_module_opens` table SHALL enforce tenant isolation at the database level, and
SHALL NOT use a permissive `USING (true)` policy for the `anon` or `authenticated` roles.

#### Scenario: An authenticated user reads only their own tenant's opens
- **WHEN** an authenticated user queries `radar_module_opens` directly
- **THEN** only rows whose `tenant_id` matches a tenant they belong to via `user_tenants`
  are returned

#### Scenario: The backend service role retains full access
- **WHEN** the backend queries the table using the service role
- **THEN** it can read and write rows for any tenant, so the endpoint can record opens

