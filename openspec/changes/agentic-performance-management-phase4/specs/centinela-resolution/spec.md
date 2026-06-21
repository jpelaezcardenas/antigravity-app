## ADDED Requirements

### Requirement: Centinela detects discrepancies from the Shadow GL reconciliation view
The system SHALL poll `shadow_gl_discrepancies` for new or unresolved rows for the Cliente Cero tenant and create a `centinela_alerts` row for each, reusing the existing similarity-enrichment behavior.

#### Scenario: New discrepancy produces an alert
- **WHEN** `shadow_gl_discrepancies` contains a row with `status IN ('missing_in_erp', 'amount_mismatch')` not yet linked to an alert
- **THEN** Centinela creates a `centinela_alerts` row referencing the discrepancy
- **AND** the existing similarity-enrichment requirement (`centinela-alerts`) applies unchanged to that alert

#### Scenario: Already-alerted discrepancy is not duplicated
- **WHEN** a discrepancy already has a linked, unresolved `centinela_alerts` row
- **THEN** the next poll cycle SHALL NOT create a second alert for the same discrepancy

### Requirement: Resolution Agent drafts a correcting journal entry
For each unresolved alert, the system SHALL generate a proposed correcting journal entry via the LLM cascade (Groq → Cerebras → OpenRouter → Mistral), informed by similar past decisions when available.

#### Scenario: Draft generated for amount mismatch
- **WHEN** an alert has `status = 'amount_mismatch'` and `variance_minor != 0`
- **THEN** Resolution Agent produces a draft with balanced debit/credit lines covering `variance_minor`
- **AND** the draft includes a human-readable `rationale` string

#### Scenario: Draft reuses historical treatment when similarity is high
- **WHEN** the alert's `similar_decisions[0].similarity > 0.8`
- **THEN** the draft's account codes and rationale SHALL be informed by that historical decision rather than generated from scratch

#### Scenario: All LLM providers unavailable
- **WHEN** Groq, Cerebras, OpenRouter, and Mistral all fail or time out
- **THEN** the alert remains in `pending_draft` state
- **AND** no partial or malformed draft is created

### Requirement: Draft must pass Agent Critic before reaching Approval Queue
The system SHALL reject any Resolution Agent draft that Agent Critic marks unbalanced, and SHALL regenerate rather than enqueue it.

#### Scenario: Critic rejects unbalanced draft
- **WHEN** Agent Critic validation returns `is_valid: false` for a Resolution Agent draft
- **THEN** the draft is NOT enqueued to Approval Queue
- **AND** Resolution Agent retries generation up to 2 times before marking the alert `needs_human_review`

#### Scenario: Critic approves balanced draft
- **WHEN** Agent Critic validation returns `is_valid: true`
- **THEN** the draft is enqueued to `approval_queue` with `draft_type = 'tax_correction'`

### Requirement: Approved correction is written back to Siigo via outbox
Once Entidad A approves a `tax_correction` draft, the system SHALL enqueue a write-back job in `executor_outbox` rather than calling the Siigo API synchronously from the approval request.

#### Scenario: Approval enqueues write-back job
- **WHEN** Entidad A approves a `tax_correction` draft
- **THEN** a row is inserted into `executor_outbox` with `status = 'pending'` and the journal entry payload
- **AND** the approval HTTP response returns immediately without waiting on Siigo

#### Scenario: Write-back job posts to Siigo and marks resolved
- **WHEN** the outbox poller picks up a `pending` job
- **THEN** it calls the Siigo write API
- **AND** on success sets `executor_outbox.status = 'completed'` and the source `centinela_alerts.status = 'resolved'`

#### Scenario: Write-back failure retries with backoff
- **WHEN** the Siigo write API call fails (timeout, 5xx)
- **THEN** `executor_outbox.attempts` increments and the job is retried with exponential backoff
- **AND** after 5 failed attempts the job is marked `status = 'failed'` for manual review

### Requirement: Resolved correction is vectorized into the knowledge base
After a successful write-back, the system SHALL vectorize the approval rationale into `knowledge_chunks`, reusing the existing approval-queue vectorization behavior.

#### Scenario: Vectorization triggered after write-back success
- **WHEN** `executor_outbox.status` transitions to `completed` for a `tax_correction` job
- **THEN** the linked approval's vectorization follows the existing `approval-queue` vectorization-status requirement unchanged
