## ADDED Requirements

### Requirement: Tenant model with Cliente Cero seed
The system SHALL maintain a `tenants` table keyed by Colombian NIT, with exactly one tenant flagged `is_cliente_cero = true` representing Contexia SAS. All Shadow GL tables SHALL reference `tenant_id` and be protected by RLS scoped to that tenant.

#### Scenario: Cliente Cero tenant exists before any agent runs
- **WHEN** any Shadow GL migration is applied
- **THEN** a `tenants` row exists with `is_cliente_cero = true` and `legal_name` matching Contexia SAS

#### Scenario: Second tenant cannot also be Cliente Cero
- **WHEN** an INSERT or UPDATE attempts to set `is_cliente_cero = true` on a second row
- **THEN** the operation SHALL fail (enforced via unique partial index)

### Requirement: DIAN UBL 2.1 XML ingestion preserves the legal artifact
The system SHALL parse DIAN electronic invoice/credit-note/debit-note XML (UBL 2.1) and store the parsed fields alongside the raw XML, keyed by CUFE, without mutating the original document.

#### Scenario: Valid DIAN invoice ingested
- **WHEN** a well-formed UBL 2.1 invoice XML is received via the DIAN webhook
- **THEN** system extracts CUFE, issuer NIT, receiver NIT, issue date, total_amount_minor, tax_amount_minor, withholding_amount_minor
- **AND** stores the complete raw XML in `dian_xml_documents.raw_xml`
- **AND** the row is unique per `(tenant_id, cufe)`

#### Scenario: Duplicate CUFE is idempotent
- **WHEN** the same CUFE is received twice (DIAN retry)
- **THEN** the second ingestion SHALL NOT create a duplicate row
- **AND** SHALL NOT raise an unhandled error

#### Scenario: Malformed XML is rejected without corrupting state
- **WHEN** the received XML fails UBL 2.1 schema validation
- **THEN** the document is NOT inserted into `dian_xml_documents`
- **AND** the failure is logged with the raw payload for manual review

### Requirement: Siigo journal mirror reflects ERP truth without polymorphic associations
The system SHALL mirror Siigo journal entries and lines into `erp_journal_entries` and `erp_journal_lines` using strict foreign keys (no polymorphic document_type/document_id column), enforcing double-entry per entry.

#### Scenario: Journal entry synced from Siigo
- **WHEN** the Siigo sync job calls `GET /v1/journals` and finds a new voucher
- **THEN** system creates one `erp_journal_entries` row and N `erp_journal_lines` rows
- **AND** each line has either `debit_minor > 0` or `credit_minor > 0`, never both

#### Scenario: Unbalanced entry is rejected at the database layer
- **WHEN** an INSERT/UPDATE to `erp_journal_lines` would leave `SUM(debit_minor) <> SUM(credit_minor)` for an entry
- **THEN** the deferred constraint trigger SHALL raise an exception and the transaction SHALL roll back

#### Scenario: Journal entry links back to its DIAN source when known
- **WHEN** a Siigo voucher references an invoice with a recognizable CUFE
- **THEN** `erp_journal_entries.source_cufe` is populated with that CUFE

### Requirement: Reconciliation view surfaces DIAN-ERP discrepancies
The system SHALL provide a materialized view comparing DIAN totals against mirrored ERP totals per CUFE, refreshed on a schedule and on demand.

#### Scenario: Missing ERP entry flagged
- **WHEN** a `dian_xml_documents` row has no matching `erp_journal_entries.source_cufe`
- **THEN** `shadow_gl_discrepancies.status = 'missing_in_erp'` for that CUFE

#### Scenario: Amount mismatch flagged
- **WHEN** DIAN total and ERP total for the same CUFE differ
- **THEN** `shadow_gl_discrepancies.status = 'amount_mismatch'` with `variance_minor` populated

#### Scenario: View refreshes without blocking reads
- **WHEN** the scheduled refresh runs every 15 minutes
- **THEN** it SHALL use `REFRESH MATERIALIZED VIEW CONCURRENTLY` so concurrent Centinela reads are not blocked

#### Scenario: On-demand refresh available to Centinela
- **WHEN** Centinela requests a fresh scan
- **THEN** system can trigger an immediate concurrent refresh rather than waiting for the next scheduled cycle
