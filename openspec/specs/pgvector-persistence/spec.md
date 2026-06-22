# pgvector-persistence Specification

## Purpose
TBD - created by archiving change add-pgvector-agent-critic-phase-3. Update Purpose after archive.
## Requirements
### Requirement: pgvector extension enabled in Supabase
The system SHALL enable PostgreSQL pgvector extension in the Supabase database. This enables vector data type and similarity search operations.

#### Scenario: pgvector extension installed
- **WHEN** database schema is initialized
- **THEN** query `SELECT * FROM pg_extension WHERE extname='vector';` returns 1 row with version >= 0.7.0

### Requirement: knowledge_chunks table exists with embedding column
The system SHALL provide a `knowledge_chunks` table that stores decision embeddings and metadata.

Table schema:
- `id` (uuid, primary key)
- `content` (text): semantic summary of the decision (what was decided, why)
- `embedding` (vector(1536)): 1536-dim vector (OpenAI ada-002 output size)
- `content_hash` (text, unique): SHA-256 hash of content (deduplication)
- `metadata` (jsonb): `{ approval_id, decided_by, timestamp, confidence }`
- `created_at` (timestamp with time zone)

#### Scenario: Table created on migration
- **WHEN** Supabase migration runs at deploy time
- **THEN** `knowledge_chunks` table exists with all columns and constraints

#### Scenario: Columns have correct types
- **WHEN** query `\d knowledge_chunks` is run
- **THEN** embedding column is type `vector(1536)`, content_hash is UNIQUE, created_at has default CURRENT_TIMESTAMP

### Requirement: RPC function match_knowledge_chunks available
The system SHALL expose a PostgreSQL RPC function `match_knowledge_chunks(query_embedding, match_threshold, match_count)` that performs similarity search.

Function signature:
```sql
match_knowledge_chunks(
  query_embedding vector(1536),
  match_threshold float4 DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE(id uuid, content text, similarity float4, metadata jsonb)
```

#### Scenario: Similarity search returns ordered results
- **WHEN** `match_knowledge_chunks([0.1, 0.2, ...], 0.7, 5)` is called
- **THEN** returns up to 5 rows where similarity >= 0.7, ordered by similarity DESC
- **AND** each row includes id, content, similarity score (1.0 = identical, 0.0 = opposite)

#### Scenario: Threshold filters results
- **WHEN** threshold is 0.9 (strict) vs 0.5 (loose)
- **THEN** strict threshold returns fewer results (higher quality), loose threshold returns more (broader matching)

#### Scenario: Empty results when no matches
- **WHEN** query_embedding has no similar vectors in table
- **THEN** returns empty result set (zero rows)

### Requirement: knowledge_chunks persists approved decision embeddings
The system SHALL store embeddings in knowledge_chunks only when a decision is explicitly approved by Entidad A. Each embedding includes semantic content and decision metadata.

#### Scenario: Embedding persisted on approval
- **WHEN** Entidad A approves a draft via `/api/v1/approval-queue/approve`
- **THEN** a new row is inserted into knowledge_chunks with embedding generated from approval reason

#### Scenario: Metadata captures decision context
- **WHEN** embedding is persisted
- **THEN** metadata includes: approval_id (draft UUID), decided_by (contador email), timestamp (ISO 8601), confidence (decimal 0-1)

