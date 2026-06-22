# decision-vectorization Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: Approval decisions are vectorized automatically
The system SHALL convert approved journal entry decisions into vector embeddings. Vectorization happens asynchronously after approval is recorded. Vectorization failure does NOT block approval (non-blocking).

#### Scenario: Decision vectorized on approval
- **WHEN** Entidad A approves a draft and hits POST `/api/v1/approval-queue/approve`
- **THEN** system asynchronously calls vectorization service
- **AND** approval response returns immediately (< 200ms), vectorization happens in background

#### Scenario: Vectorization failure logged but non-blocking
- **WHEN** embedding API (OpenAI) fails or times out
- **THEN** error is logged with approval_id and reason
- **AND** approval is NOT rolled back (decision remains in system)
- **AND** approval_decisions table marks vectorization_status = 'failed'

#### Scenario: Semantic summary extracted from approval reason
- **WHEN** Entidad A provides approval reason text (e.g., "Contexia's own invoice, matches DIAN")
- **THEN** vectorization service extracts semantic meaning (not just full text)
- **AND** semantic summary is stored in knowledge_chunks.content for human readability

### Requirement: Only approved decisions are vectorized
The system SHALL vectorize ONLY decision rows with status = 'approved'. Rejected, pending, or draft decisions are NOT vectorized.

#### Scenario: Approved decision vectorized
- **WHEN** decision.status = 'approved'
- **THEN** vectorization service processes this decision

#### Scenario: Rejected decision skipped
- **WHEN** decision.status = 'rejected'
- **THEN** vectorization service does NOT create embedding for this decision

#### Scenario: Draft decision not vectorized
- **WHEN** decision.status = 'pending_approval' (still in draft)
- **THEN** vectorization service skips this (will vectorize only if later approved)

### Requirement: Embedding provider configured via environment
The system SHALL use embedding provider specified by `EMBEDDING_PROVIDER` environment variable. Supported: `openai` (default), `cerebras`.

#### Scenario: OpenAI embedding used when OPENAI_API_KEY present
- **WHEN** `OPENAI_API_KEY` is set in Railway env vars
- **THEN** vectorization uses OpenAI ada-002 model, returns 1536-dim vector

#### Scenario: Cerebras fallback when OpenAI key missing
- **WHEN** `OPENAI_API_KEY` is not set but `CEREBRAS_API_KEY` is present
- **THEN** vectorization uses Cerebras embedding API

#### Scenario: Vectorization skipped if no provider configured
- **WHEN** neither `OPENAI_API_KEY` nor `CEREBRAS_API_KEY` set
- **THEN** system logs warning and skips vectorization (approval still succeeds)

### Requirement: Vectorization metadata includes confidence score
Each embedding SHALL include a confidence score (0-1) reflecting how representative the embedding is of the decision.

#### Scenario: High-confidence embedding stored
- **WHEN** semantic extraction and embedding succeed
- **THEN** metadata.confidence = 1.0 (full confidence)

#### Scenario: Degraded confidence for short or ambiguous reasons
- **WHEN** approval reason is very short (< 10 words) or generic ("correct this")
- **THEN** metadata.confidence = 0.7-0.9 (partial confidence)

### Requirement: Content hash prevents duplicate embeddings
The system SHALL compute SHA-256 hash of semantic content. If hash already exists in knowledge_chunks, skip re-embedding (deduplication).

#### Scenario: Duplicate decision not re-embedded
- **WHEN** Entidad A approves two nearly identical decisions (same content_hash)
- **THEN** system creates only ONE embedding, second approval links to existing embedding

