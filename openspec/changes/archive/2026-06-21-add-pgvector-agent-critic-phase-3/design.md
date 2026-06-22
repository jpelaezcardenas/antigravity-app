## Context

**Current State (MVP):**
- Centinela detects DIAN ↔ Siigo mismatches ✅
- Resolution Agent drafts journal entries ✅
- Approval Queue awaits human review ✅
- No arithmetic validation before Approval Queue ❌
- Knowledge persisted in memory dict (fallback) ❌
- No compounding memory month-to-month ❌
- Unknown loop closure ❌

**Constraints:**
- Supabase pgvector extension available but not yet enabled
- FastAPI backend runs on Railway (production-175a)
- Entidad A (human contador) is approval bottleneck → must minimize false positives
- Decision embedding requires external API (OpenAI, Cerebras, or local)
- Client Cero (Contexia itself) is production test environment
- Stage 11 deployment mandatory before archiving

## Goals / Non-Goals

**Goals:**
- Implement deterministic Agent Critic that validates double-entry (SUM(débitos)=SUM(créditos)) before Approval Queue
- Activate real pgvector in Supabase, replacing memory fallback
- Vectorize approval decisions to build persistent knowledge base
- Enable similarity search: "we've seen this pattern before" → propose historical resolution
- Verify loop closure with E2E test (Centinela → Critic → Approval → Vectorization → Search)
- Deploy to production with Stage 11 report

**Non-Goals:**
- Hermes Workspace UI for Approval Queue (separate OpenSpec Slice 1)
- LLM model selection/optimization (use existing GROQ/OpenRouter keys)
- Multi-language embedding support (Spanish-only for now)
- Real-time streaming embeddings (batch vectorization on approval only)
- Advanced vector indexing optimization (use Supabase defaults)

## Decisions

### Decision 1: Agent Critic Placement (Before Approval Queue)
**Choice:** Validate journal entries deterministically (SUM débitos = SUM créditos) BEFORE human Approval Queue.

**Why:** 
- Resolution Agent sometimes drafts unbalanced entries (risk: sent to Approval Queue, entidad A wastes time rejecting)
- Deterministic validation catches errors early, forces regeneration
- No LLM uncertainty—pure arithmetic check

**Alternatives considered:**
- (A) Validate in Resolution Agent: couples validation to draft logic, harder to test independently
- (B) Validate at Siigo upload: too late, human already approved unbalanced entry
- (C) Validate client-side (Hermes UI): loses server-side enforcement guarantee

**Decision:** Implement as separate middleware endpoint `/critic/validate`. Returns (is_valid: bool, reason: str). Async call from Approval Queue enqueue handler.

---

### Decision 2: pgvector vs Alternatives
**Choice:** Activate Supabase native pgvector (vector type + embedding storage).

**Why:**
- pgvector is battle-tested, Supabase-native, zero operational overhead
- Supports similarity search (cosine distance) directly in SQL
- Metadata + embedding in same row (no separate embedding store)

**Alternatives considered:**
- (A) Milvus/Pinecone: overkill for scale (~100s of decisions/month), adds DevOps complexity
- (B) Redis embeddings: memory-bound, not persistent
- (C) Custom embedding table (TEXT field): no built-in similarity, slow

**Decision:** Use pgvector. Create RPC function `match_knowledge_chunks(embedding, threshold, count)` for similarity search from FastAPI.

---

### Decision 3: Embedding Provider (OpenAI vs Cerebras vs Local)
**Choice:** Require OPENAI_API_KEY in Railway env. Fallback to Cerebras embedding API if key missing.

**Why:**
- OpenAI embeddings (ada-002) are fast, cheap ($0.02/1M tokens), production-proven
- Cerebras embedding API is free alternative if we scale
- Local embeddings (Hugging Face) would require GPU, not available on Railway

**Alternatives considered:**
- (A) Cohere: $0.10/1K inputs (10x cost)
- (B) Voyage AI: specialized for semantic search, but $0.12/1K inputs
- (C) Local Hugging Face: requires GPU, Railway tier not available

**Decision:** Check OPENAI_API_KEY in env. If missing, attempt Cerebras. If both missing, skip vectorization (log warning) but don't block Approval Queue.

---

### Decision 4: Vectorization Trigger (On Approval Only)
**Choice:** Vectorize decision ONLY when Entidad A clicks "Approve". Draft-time vectorization wastes API calls.

**Why:**
- Rejected decisions shouldn't pollute knowledge base (bad examples)
- Approved decisions represent validated human reasoning (good training signal)
- Reduces embedding API cost by 70%+ (only ~30% of drafts get approved)

**Alternatives considered:**
- (A) Vectorize every draft: wastes API quota, includes bad examples
- (B) Vectorize on user demand: manual, error-prone
- (C) Lazy vectorization (cron job): adds complexity, delays learning

**Decision:** Call `embeddings_service.vectorize_approval_decision(approval)` in approval_queue_approve handler. If embedding fails, log error but don't block approval.

---

### Decision 5: Similarity Threshold for "Similar Enough"
**Choice:** `PGVECTOR_SIMILARITY_THRESHOLD = 0.7` (cosine distance). Tunable via env var.

**Why:**
- 0.7 = "moderately similar" (avoids noise, captures real patterns)
- 0.9+ = too strict (misses legitimate patterns)
- 0.5 = too loose (noise overwhelms signal)

**Alternatives considered:**
- (A) Fixed threshold in code: can't tune without deploy
- (B) ML-learned threshold: overkill at this stage
- (C) Percentile-based (top-N): simpler, but inconsistent over time

**Decision:** Use 0.7. Expose as env var `PGVECTOR_SIMILARITY_THRESHOLD` for future tuning. Centinela returns match_confidence = (1 - cosine_distance) so Entidad A sees confidence % inline.

---

## Risks / Trade-offs

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| pgvector extension fails to enable | Low | Pre-verify in Supabase SQL: `CREATE EXTENSION vector;` before deploy |
| OpenAI API key not in Railway env | Medium | Add OPENAI_API_KEY to Railway shared vars before Stage 11. Test in staging. |
| Embedding API rate limit hits | Low | Batch vectorization (max 1 embedding per 200ms) + exponential backoff |
| "Similar" threshold too strict → no recommendations | Medium | Start at 0.7, monitor Centinela logs, tune down to 0.65 if needed |
| Unbalanced journal entry passes Critic (validation logic bug) | Low | Comprehensive unit tests (3 cases: balanced, unbalanced, empty). E2E test catches before production. |
| Knowledge base polluted with bad decisions | Medium | Only vectorize approved entries (not drafts, not rejected). Manual curation if needed (future work). |
| E2E test fails in production (test vs prod divergence) | Low | Use production Supabase project for test. Client Cero account as test fixture. Cleanup after. |

**Trade-off: API Cost vs Learning**
- Vectorizing every approved decision adds ~$0.01/decision (OpenAI embedding cost)
- At 100 approvals/month = $1/month (negligible)
- Value: month-to-month learning compounds
- **Accept trade-off:** Cost is worth the learning signal

---

## Migration Plan

**Deployment Stages:**

1. **Pre-Flight (Before commit):**
   - [ ] Verify OPENAI_API_KEY obtained (request from engineering ops)
   - [ ] Test pgvector enable in Supabase staging: `CREATE EXTENSION vector;`
   - [ ] Test knowledge_chunks table creation (DDL migration)
   - [ ] Run Agent Critic unit tests locally (3 cases)

2. **Stage 11 Execution:**
   - [ ] Git commit + push to main
   - [ ] Railway auto-rebuild (watch build logs)
   - [ ] POST /health endpoint returns 200 OK
   - [ ] Verify tables exist: `SELECT COUNT(*) FROM knowledge_chunks;`
   - [ ] Run E2E test against production Supabase (Cliente Cero)
   - [ ] Create deployment report: `openspec/changes/.../reports/YYYY-MM-DD-deployment.md`

3. **Rollback Strategy:**
   - If pgvector fails: Disable vectorization (comment out `vectorize_approval_decision` call). Agent Critic still works (deterministic).
   - If embeddings API fails: Approval Queue still works (vectorization is non-blocking with error logging).
   - If E2E test fails: Revert commit, fix issue, redeploy.

---

## Open Questions

1. **OPENAI_API_KEY access:** Who provisions API key? When? (Need answer before Supabase table creation)
2. **knowledge_chunks retention policy:** Keep indefinitely? Purge after 6 months? (Not blocking for FASE 3, but needed for long-term)
3. **Embedding model versioning:** If OpenAI changes ada-002 endpoint, how do we retrain vectors? (Future work, document assumption in code)
4. **Entidad A UX for similarity matches:** How to present "similar decision found" inline with Centinela alert? (Hermes UI, separate OpenSpec Slice 1)
