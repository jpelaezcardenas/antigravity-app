## ADDED Requirements

### Requirement: Auditoría Sombra generates a continuous audit report
The system SHALL generate a PDF audit report summarizing Shadow GL coverage, open discrepancies, and resolution history for a tenant over a given period.

#### Scenario: Report generated for a period with resolved and open items
- **WHEN** a client calls `POST /api/v1/agents/auditoria-sombra/report` with a date range
- **THEN** system produces a PDF including: total transactions reviewed, discrepancies found, discrepancies resolved, discrepancies still open, and average resolution time
- **AND** the PDF is stored and a download URL is returned

#### Scenario: Report generation is read-only with respect to Shadow GL
- **WHEN** the report is generated
- **THEN** no `erp_journal_entries`, `dian_xml_documents`, or `centinela_alerts` rows are modified

### Requirement: Auditoría Sombra requires HITL sign-off before external delivery
The system SHALL require Entidad A approval before a generated report is marked deliverable to anyone outside Contexia, since the report could be construed as professional audit output.

#### Scenario: Internal report does not require sign-off
- **WHEN** a report is generated with `audience = 'internal'`
- **THEN** it is immediately available for download with no Approval Queue entry

#### Scenario: External-audience report requires sign-off
- **WHEN** a report is generated with `audience = 'external'`
- **THEN** system enqueues an `approval_queue` row with `draft_type = 'audit_report_signoff'`
- **AND** the download URL is withheld until Entidad A approves it

#### Scenario: Rejected report is not deliverable
- **WHEN** Entidad A rejects an `audit_report_signoff` entry
- **THEN** the report's download URL SHALL remain inaccessible and the report is marked `status = 'rejected'`
