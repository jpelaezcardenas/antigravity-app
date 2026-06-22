# agent-critic Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: Agent Critic validates journal entry arithmetic
The system SHALL provide a deterministic validator that checks double-entry bookkeeping rules (SUM(débitos) = SUM(créditos)) before a journal entry reaches Approval Queue.

#### Scenario: Balanced journal entry passes validation
- **WHEN** Agent Critic receives a journal entry with débitos=[1,000,000] and créditos=[1,000,000]
- **THEN** validation returns `{is_valid: true, reason: "Entry balanced ✓"}`

#### Scenario: Unbalanced entry fails validation
- **WHEN** Agent Critic receives a journal entry with débitos=[1,000,000] and créditos=[900,000]
- **THEN** validation returns `{is_valid: false, reason: "Unbalanced: débitos=1000000, créditos=900000"}`

#### Scenario: Empty entry (no lines) fails validation
- **WHEN** Agent Critic receives an empty journal entry with no debit/credit lines
- **THEN** validation returns `{is_valid: false, reason: "Empty entry (no debits/credits)"}`

### Requirement: Agent Critic blocks unbalanced entries from Approval Queue
The system SHALL prevent unbalanced journal entries from being enqueued to Approval Queue. Failed validation SHALL return a clear reason for human review (typically prompts Resolution Agent to regenerate).

#### Scenario: Unbalanced draft blocked from queue
- **WHEN** Approval Queue enqueue handler calls `/critic/validate` and receives `is_valid: false`
- **THEN** enqueue operation fails with HTTP 400, returns reason to caller
- **AND** Centinela/Resolution Agent can read error and retry with corrected entry

#### Scenario: Validation error logged for debugging
- **WHEN** Agent Critic validates any entry
- **THEN** result (valid or invalid) is logged with entry_id, timestamp, and validation reason

### Requirement: Agent Critic exposes REST API endpoint
The system SHALL provide a `/api/v1/critic/validate` POST endpoint that accepts a journal entry object and returns validation result.

Request body:
```json
{
  "lines": [
    {"account": "1105", "debit": 1000000, "credit": 0},
    {"account": "2105", "debit": 0, "credit": 1000000}
  ],
  "memo": "DIAN correction"
}
```

Response body:
```json
{
  "is_valid": true,
  "reason": "Entry balanced ✓"
}
```

#### Scenario: Valid endpoint call returns 200 with result
- **WHEN** client POSTs a balanced journal entry to `/critic/validate`
- **THEN** response HTTP status is 200, body contains `is_valid: true` and `reason` string

#### Scenario: Invalid input returns 400
- **WHEN** client POSTs malformed JSON (missing lines array)
- **THEN** response HTTP status is 400, error message explains what's missing

### Requirement: Validation is synchronous and deterministic
Agent Critic SHALL complete validation in < 100ms. The result SHALL be deterministic (same input always produces same output). No external dependencies (no LLM calls, no database lookups).

#### Scenario: Validation completes quickly
- **WHEN** `/critic/validate` is called with a large journal entry (100+ lines)
- **THEN** response completes within 100ms

