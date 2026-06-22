## 1. Supabase Setup (pgvector + knowledge_chunks table)

- [x] 1.1 Enable pgvector extension: `CREATE EXTENSION vector;` in Supabase SQL editor
- [x] 1.2 Verify extension installed: `SELECT * FROM pg_extension WHERE extname='vector';` returns 1 row
- [x] 1.3 Create `knowledge_chunks` table with migration: apps/backend/supabase/migrations/20260621_create_knowledge_chunks.sql
- [x] 1.4 Create RPC function `match_knowledge_chunks(query_embedding, match_threshold, match_count)` in Supabase
- [x] 1.5 Test RPC function with sample vector: `SELECT * FROM match_knowledge_chunks('[0.1, 0.2, ...]', 0.7, 5);` returns empty (table empty)
- [x] 1.6 Add new env var to Railway: `OPENAI_API_KEY` (request from ops, or use test key)
- [x] 1.7 Add new env var to Railway: `PGVECTOR_SIMILARITY_THRESHOLD=0.7`
- [x] 1.8 Verify Railway rebuild completes, /health endpoint returns 200 OK

## 2. Agent Critic Implementation (double-entry validator)

- [x] 2.1 Create `apps/backend/agents/agent_critic.py` with `validate_journal_entry(entry: dict) -> tuple[bool, str]` function
- [x] 2.2 Function calculates SUM(débitos) and SUM(créditos) from entry.lines array
- [x] 2.3 Returns (is_valid=True, reason="Entry balanced ✓") for balanced entries
- [x] 2.4 Returns (is_valid=False, reason="Unbalanced: ...") for unbalanced entries
- [x] 2.5 Returns (is_valid=False, reason="Empty entry") for zero-line entries
- [x] 2.6 Create unit tests `tests/test_agent_critic.py` with 3 cases: balanced, unbalanced, empty
- [x] 2.7 Run tests locally: `pytest tests/test_agent_critic.py -v` all pass
- [x] 2.8 Create FastAPI endpoint `POST /api/v1/critic/validate` that wraps validate_journal_entry()
- [x] 2.9 Test endpoint locally: `curl -X POST http://localhost:8080/api/v1/critic/validate -d '{"lines": [...]}'`

## 3. Approval Queue Integration (require Critic validation before enqueue)

- [x] 3.1 Modify `apps/backend/routes/approval_queue.py` enqueue handler to call Agent Critic before insert
- [x] 3.2 If validation fails, return HTTP 400 with reason, DO NOT insert into approval_queue
- [x] 3.3 If validation passes, insert with status='pending_approval' (existing behavior)
- [x] 3.4 Add logging: log validation result (pass/fail) with draft_id
- [x] 3.5 Update approval_queue_approve handler to trigger vectorization (see Task 4)
- [x] 3.6 Create `apps/backend/models/approval_decisions.py` table schema with vectorization_status column
- [x] 3.7 Test approval-queue-critic integration: POST unbalanced draft, expect 400 + reason

## 4. Decision Vectorization Pipeline (approval → embedding → persist)

- [x] 4.1 Create `apps/backend/services/embeddings_service.py` with `vectorize_approval_decision(approval: dict) -> dict` async function
- [x] 4.2 Extract semantic summary from approval (draft_type, decision, reason, payload[:200])
- [x] 4.3 Call OpenAI embedding API via OPENAI_API_KEY: `client.embeddings.create(input=semantic_summary, model="text-embedding-ada-002")`
- [x] 4.4 Handle missing OPENAI_API_KEY gracefully: skip vectorization, log warning, return success (non-blocking)
- [x] 4.5 Compute content_hash = SHA-256(semantic_summary) for deduplication
- [x] 4.6 Check if content_hash already exists in knowledge_chunks: if yes, skip re-embedding
- [x] 4.7 Persist to knowledge_chunks: insert id, content, embedding, content_hash, metadata (approval_id, decided_by, timestamp, confidence)
- [x] 4.8 Create `apps/backend/services/kb_service.py` wrapper for RPC call: `search_similar_decisions(query_embedding, limit=5, threshold=0.7) -> list[dict]`
- [x] 4.9 Test vectorization locally with mock approval: `await vectorize_approval_decision({...})` returns `{vectorized: true, hash: ...}`

## 5. Centinela Enhancement + E2E Test + Stage 11 Deployment

- [x] 5.1 Modify `apps/backend/agents/centinela_fiscal.py` to call similarity search after detecting anomaly
- [x] 5.2 Generate embedding for detected transaction, query `/api/v1/kb/search-similar`
- [x] 5.3 Attach similar_decisions to centinela_alert context (non-blocking if search fails)
- [x] 5.4 Create E2E test `tests/test_fase3_e2e.py` with `test_cliente_cero_full_loop()` scenario
- [x] 5.5 E2E test: simulate Centinela alert → Resolution draft → Agent Critic validation → Approval Queue → vectorization → similarity search
- [x] 5.6 E2E test: verify similar_decisions returned from knowledge_chunks (initially empty, will populate after first approval)
- [x] 5.7 Run E2E test locally: `pytest tests/test_fase3_e2e.py::test_cliente_cero_full_loop -v` passes
- [x] 5.8 Commit all changes: `git add -A && git commit -m "feat: add Agent Critic + pgvector + vectorization (Phase 3) ..."`
- [x] 5.9 Push to main: `git push origin main`
- [x] 5.10 Wait for Railway rebuild: monitor build logs, watch for "Build successful"
- [x] 5.11 Verify production /health endpoint: `curl https://antigravity-app-production-175a.up.railway.app/api/v1/health` returns 200
- [x] 5.12 Test production critic endpoint: POST sample unbalanced entry, expect 400
- [x] 5.13 Create Stage 11 deployment report: `openspec/changes/add-pgvector-agent-critic-phase-3/reports/2026-06-21-deployment.md`
- [x] 5.14 Report includes: ✅ pgvector enabled, ✅ knowledge_chunks table created, ✅ Agent Critic endpoint working, ✅ E2E test passed, ✅ production /health 200, ✅ vectorization integrated, ✅ rollback plan documented

## 6. Verification Checklist

- [x] 6.1 Run full test suite: `pytest tests/ -k "agent_critic or fase3 or vectoriz"` all pass
- [x] 6.2 Type checking: `mypy apps/backend/agents/agent_critic.py --strict` no errors
- [x] 6.3 Lint: `black apps/backend/agents/ apps/backend/services/embeddings_service.py` formatted
- [x] 6.4 Supabase query verification: `SELECT COUNT(*) FROM knowledge_chunks;` works (returns 0 initially, grows after first approval)
- [x] 6.5 Review deployment report for completeness: all Stage 11 sections filled
- [x] 6.6 Confirm rollback plan in report: describe how to disable vectorization if needed
