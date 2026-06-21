## MODIFIED Requirements

### Requirement: Approval Queue requires Agent Critic validation before enqueue
The system SHALL validate all draft journal entries using Agent Critic BEFORE accepting them into Approval Queue. Only balanced entries (SUM(débitos)=SUM(créditos)) are enqueued. Enqueue accepts a `draft_type` beyond `tax_correction` (e.g. `risk_review`, `audit_report_signoff`, `taty_escalation`, `social_reply`); Agent Critic balance validation applies only when the draft represents a journal entry — non-journal draft types skip balance validation and are enqueued directly with their `payload`.

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

#### Scenario: Non-journal draft type bypasses balance validation
- **WHEN** client POSTs a draft with `draft_type` other than `tax_correction` (e.g. `risk_review`, `taty_escalation`)
- **THEN** system SHALL NOT run Agent Critic balance validation against `payload`
- **AND** the draft is inserted into approval_queue table with status = 'pending_approval'

#### Scenario: Existing tax_correction callers are unaffected
- **WHEN** a caller written against the FASE 3 contract POSTs `{ draft_type: "tax_correction", payload: {...} }`
- **THEN** behavior is identical to the pre-existing balance-validation flow with no change to response shape

### Requirement: Approval Queue exposes a list endpoint for pending drafts
The system SHALL expose `GET /api/v1/approval-queue` returning pending drafts across all `draft_type` values, scoped to the caller's tenant via RLS, so Hermes UI and Taty escalations can be reviewed without querying Supabase directly.

#### Scenario: List returns pending drafts across draft types
- **WHEN** a client calls `GET /api/v1/approval-queue?status=pending_approval`
- **THEN** system returns all matching rows regardless of `draft_type`, each including `id`, `draft_type`, `payload`, `rationale`, `created_at`, `status`

#### Scenario: List supports filtering by draft_type
- **WHEN** a client calls `GET /api/v1/approval-queue?draft_type=risk_review`
- **THEN** only rows with that `draft_type` are returned

#### Scenario: List is scoped by tenant via RLS
- **WHEN** a caller belonging to one tenant requests the list
- **THEN** rows belonging to other tenants SHALL NOT appear in the response, enforced at the database layer

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
