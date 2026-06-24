## ADDED Requirements

### Requirement: Pulso Diario produces a read-only daily flux summary
The system SHALL expose an endpoint that aggregates the tenant's Shadow GL activity for a given day into a flux-analysis summary, performing no writes and requiring no HITL.

#### Scenario: Daily summary requested for a day with activity
- **WHEN** a client calls `GET /api/v1/agents/pulso-diario/summary?date=YYYY-MM-DD`
- **THEN** system returns total inflow_minor, total outflow_minor, net_flux_minor, and discrepancy_count for that date, scoped to the caller's tenant
- **AND** the response is read-only and triggers no Approval Queue entry

#### Scenario: Daily summary requested for a day with no activity
- **WHEN** the requested date has no `erp_journal_entries` rows for the tenant
- **THEN** system returns zeroed totals rather than an error

#### Scenario: Summary is scoped to the caller's tenant via RLS
- **WHEN** a request is made for `tenant_id` the caller does not belong to
- **THEN** RLS SHALL prevent any rows from that tenant being returned, independent of application-layer filtering
