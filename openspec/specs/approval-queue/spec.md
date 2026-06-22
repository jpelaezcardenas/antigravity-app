# approval-queue Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: Approval Queue requires Agent Critic validation before enqueue
The system SHALL validate all draft journal entries using Agent Critic BEFORE accepting them into Approval Queue. Only balanced entries (SUM(débitos)=SUM(créditos)) are enqueued.

#### Scenario: Balanced draft enqueued successfully
- **WHEN** client POSTs a balanced draft to `/api/v1/approval-queue/enqueue`
- **THEN** system calls Agent Critic validation
- **AND** validation returns `is_valid: true`
- **AND** draft is inserted into approval_queue table with status = 'pending_approval'

#### Scenario: Unbalanced draft rejected from queue
- **WHEN** client POSTs an unbalanced draft (débitos != créditos)
- **THEN** system calls Agent Critic validation
- **AND** validation returns `is_valid: false` with reason
- **AND** enqueue operation fails with HTTP 400
- **AND** response body includes validation reason (e.g., "Unbalanced: débitos=1000000, créditos=900000")

#### Scenario: Validation reason returned to caller
- **WHEN** enqueue fails due to Agent Critic validation
- **THEN** error response includes `{ validation_error: true, reason: "...", retry: true }`
- **AND** caller (Resolution Agent) can read reason and regenerate draft

### Requirement: Approval Queue approval triggers vectorization
When Entidad A approves a draft, the system SHALL asynchronously vectorize the decision (convert approval reason to embedding, store in knowledge_chunks).

#### Scenario: Approval triggers async vectorization
- **WHEN** Entidad A clicks "Approve" and hits POST `/api/v1/approval-queue/approve`
- **THEN** response returns immediately (status = 'approved')
- **AND** vectorization happens in background (non-blocking)

#### Scenario: Vectorization failure does not rollback approval
- **WHEN** vectorization service fails (e.g., OpenAI API timeout)
- **THEN** approval is already committed (not rolled back)
- **AND** error is logged, approval_decisions.vectorization_status = 'failed'
- **AND** Entidad A sees "Approved" (not aware of vectorization error)

### Requirement: Approval Queue tracks vectorization status
Each approved decision records whether it was successfully vectorized. Possible values: pending, in_progress, success, failed.

#### Scenario: Vectorization status tracked
- **WHEN** decision is approved
- **THEN** approval_decisions.vectorization_status = 'pending' (initially)
- **AND** after vectorization completes, status updated to 'success' or 'failed'
- **AND** failed decisions can be manually re-tried (future admin feature)

