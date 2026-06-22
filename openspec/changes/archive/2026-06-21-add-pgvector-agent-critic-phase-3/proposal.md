## Why

MVP has three critical fallbacks that prevent APM scalability. (1) No arithmetic validation: draft journal entries bypass double-entry verification before reaching Approval Queue, risking unbalanced transactions. (2) pgvector fallback to memory dict: no persistent compounding memory means zero month-to-month learning—each Centinela alert repeats the same reasoning. (3) No E2E closure verification: loop completion unknown—can't confirm that Centinela → Resolution → Critic → Approval → Knowledge Store actually closes.

FASE 3 closes these gaps. We implement deterministic Agent Critic (validates SUM(débitos)=SUM(créditos)), activate real pgvector search (replace memory fallback), vectorize approval decisions (human reasoning → embeddings → reusable knowledge), and verify with E2E test (Cliente Cero loop).

## What Changes

- **Agent Critic**: New FastAPI service validates journal entry arithmetic before Approval Queue. Blocks unbalanced entries, forces regeneration.
- **pgvector activation**: Enable pgvector extension in Supabase. Create `knowledge_chunks` table with embedding column (vector type).
- **Decision vectorization**: Approval decisions automatically convert to embeddings. Persist semantic summary + confidence metadata.
- **Similarity search**: Centinela's next anomaly detection leverages past approvals. "Found similar pattern before → propose historical resolution → confidence %" reduces alert fatigue.
- **E2E closure test**: End-to-end verification with Cliente Cero (Contexia). Centinela detects anomaly → Resolution drafts → Critic validates → Approval Queue → vectorization → similarity search confirmed.
- **Stage 11 deployment**: Mandatory production deployment. Git commit+push → Railway rebuild → /health verify → deployment report.

## Capabilities

### New Capabilities

- `agent-critic`: Deterministic double-entry validator. Checks SUM(débitos)=SUM(créditos). Blocks unbalanced entries. Returns validation result + reason.
- `pgvector-persistence`: Real Supabase pgvector integration. Replaces memory fallback. Stores decision embeddings with metadata (decision_id, approved_by, timestamp).
- `decision-vectorization`: Approval decision semantic extraction + embedding generation. Converts human reasoning (approval reason field) to vector representation.
- `similarity-search`: Vector similarity search for past decisions. Returns N most similar approvals + confidence scores. Enables "we've seen this before" patterns.

### Modified Capabilities

- `approval-queue`: Approval Queue now requires Agent Critic validation BEFORE human review. Unbalanced entries blocked → Resolution Agent forced to regenerate.
- `centinela-alerts`: Centinela now queries similarity search after detecting anomaly. Proposes historical resolution (if confidence > threshold) + highlights delta from past approval.

## Impact

**Backend (FastAPI):**
- New endpoint: `/api/v1/critic/validate` (POST journal entry → returns validation result)
- New service: `services/embeddings_service.py` (vectorization pipeline)
- New service: `services/kb_service.py` (similarity search wrapper)
- Modified endpoint: `/api/v1/approval-queue/enqueue` (adds critic validation step)

**Database (Supabase):**
- Enable pgvector extension
- Create `knowledge_chunks` table (id, content, embedding:vector, content_hash, metadata:jsonb, created_at)
- Create `approval_decisions` table (draft_id, draft_type, decision, reason, approved_by, vectorized_at)
- Create matching function: `match_knowledge_chunks(query_embedding, threshold, count)`

**Infrastructure (Railway):**
- New env var: `OPENAI_API_KEY` (or alternative embedding provider key)
- New env var: `EMBEDDING_PROVIDER` (default: openai)
- New env var: `PGVECTOR_SIMILARITY_THRESHOLD` (default: 0.7)

**Testing:**
- New E2E test: `tests/test_fase3_e2e.py` (Cliente Cero full loop)
- 3 unit tests: agent_critic validation cases

**Deployment:**
- Stage 11 report: `openspec/changes/add-pgvector-agent-critic-phase-3/reports/YYYY-MM-DD-deployment.md`
