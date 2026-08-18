## Requirements

### Requirement: Shadow GL rows carry an explicit real-vs-synthetic flag
Every row in `erp_journal_entries` and `dian_xml_documents` SHALL carry an `is_verified_real`
boolean column, `NOT NULL DEFAULT false`. A row's flag SHALL only become `true` when the ingesting
endpoint receives an explicit `is_verified_real=true` query parameter on upload; it SHALL never
default to `true`.

#### Scenario: New table rows default to unverified
- **WHEN** the `is_verified_real` column is added to `erp_journal_entries` and `dian_xml_documents`
- **THEN** every pre-existing row in both tables has `is_verified_real = false`

#### Scenario: Upload without the flag stays unverified
- **WHEN** an admin uploads a DIAN XML or Siigo CSV file to any of the three ingestion endpoints
  without passing `is_verified_real`
- **THEN** the inserted row(s) have `is_verified_real = false`

#### Scenario: Upload with the flag is marked verified
- **WHEN** an admin uploads a DIAN XML or Siigo CSV file with `?is_verified_real=true` on the
  request
- **THEN** the inserted row(s) have `is_verified_real = true`

### Requirement: HITL-recovered entries stay unverified by default
Entries persisted via the Hermes approval-queue replay path (`_persist_approved_entry`, triggered
after a parse-error is approved for retry) SHALL be inserted with `is_verified_real = false`
regardless of the original upload's intent, since that path does not carry the flag through the
approval-queue payload.

#### Scenario: Approved parse-error entry lands unverified
- **WHEN** a malformed upload is routed to `approval_queue`, approved via the Hermes WebSocket
  callback, and persisted by `_persist_approved_entry`
- **THEN** the resulting row(s) in `erp_journal_entries`/`dian_xml_documents` have
  `is_verified_real = false`
