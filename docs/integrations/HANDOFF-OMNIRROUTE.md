# HANDOFF: OmniRoute Integration for Contexia
# Target: Claude Code Desktop (spec-driven development)
# Framework: lidr-specboot + OpenSpec
# Date: 2026-08-29

## Context

Contexia needs to reduce LLM costs while maintaining quality for 16 freemium clients.
OmniRoute v3.8.50 has been installed locally as an AI gateway with 476+ free models.

**Current state**: Infrastructure is running but NOT yet integrated into the spec-driven workflow.
**Your job**: Complete the integration following specboot patterns, verify functionality, and document properly.

## What's Already Done

1. OmniRoute running at http://localhost:20128 (dashboard: CHANGEME)
2. 6 task-specific combos created in OmniRoute:
   - contexia-fast-free (classification, FAQ)
   - contexia-docs-free (extraction, JSON)
   - contexia-tools-free (tool calling)
   - contexia-dev-free (code, tests)
   - contexia-private-local (confidential data)
   - contexia-critical-review (supervised review)
3. 4 API keys separated by service (hermes-prod, backend-prod, n8n-prod, claude-code-dev)
4. Hermes fallback configured (mimo → OmniRoute auto)
5. MCP server added to Claude Code Desktop (.claude/.mcp.json)

## What You Need to Do

### Phase 1: Create OpenSpec Spec (REQUIRED FIRST)

Follow the specboot workflow:

```bash
cd /mnt/c/Users/contexia/antigravity-app
openspec propose omniroute-integration
```

Create spec with:
- Purpose: Integrate OmniRoute as LLM gateway for cost reduction
- Requirements: Task-specific routing, fallback, observability, data classification
- Scenarios: Each combo usage, fallback behavior, error handling, pilot metrics

### Phase 2: Verify Infrastructure

```bash
# Test OmniRoute is running
curl http://localhost:20128/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"contexia-fast-free","messages":[{"role":"user","content":"test"}]}'

# Test each combo
for combo in contexia-fast-free contexia-docs-free contexia-tools-free contexia-dev-free; do
  echo "Testing $combo..."
  curl -s http://localhost:20128/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$combo\",\"messages\":[{\"role\":\"user\",\"content\":\"test\"}]}" | grep -o '"model":"[^"]*"'
done

# Verify Hermes fallback
hermes fallback list
```

### Phase 3: Integrate with Backend (FastAPI)

Check if backend config.py can use OmniRoute:
- File: apps/backend/config.py
- Look for: LLM cascade, provider configuration
- Add: OmniRoute as provider with combo routing

### Phase 4: Analyze Taty (WhatsApp Bot) Compatibility

**CRITICAL QUESTION**: Can Taty use OmniRoute for vectors/embeddings?

Taty uses:
- WhatsApp via Chatwoot Bridge (local)
- pgvector for similarity search in Supabase
- Embeddings for knowledge base queries

Check:
1. Does OmniRoute support embedding models? (14 embedding providers listed)
2. Can Taty's embedding calls go through OmniRoute?
3. What's the latency impact for real-time WhatsApp responses?

Run this analysis:
```bash
# Check available embedding models in OmniRoute
curl -s http://localhost:20128/api/models -b /tmp/or-cookies.txt | grep -i embed

# Test embedding endpoint
curl http://localhost:20128/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","input":"test embedding"}'
```

### Phase 5: Create Pilot Framework

Document in OpenSpec:
- Shadow-mode pilot (7-14 days)
- Metrics: availability ≥95%, JSON valid ≥98%, classification ≥90%
- Mimo renewal decision criteria
- Fallback strategy if free models fail

### Phase 6: Update Documentation

Following specboot patterns:
1. Update openspec/specs/ with OmniRoute spec
2. Create openspec/changes/omniroute-integration/tasks.md
3. Update AGENTS.md, CLAUDE.md with OmniRoute references
4. Ensure symlinks work for all copilots

## Key Files to Check

- antigravity-app/docs/OMNIRROUTE_SETUP.md (current docs)
- antigravity-app/CLAUDE.md (engineering standards)
- antigravity-app/openspec/config.yaml (OpenSpec config)
- antigravity-app/apps/backend/config.py (LLM cascade)
- ~/.hermes/profiles/contexia/config.yaml (Hermes config)
- /mnt/c/Users/contexia/.claude/.mcp.json (Claude Code MCP)

## Taty Analysis Template

```markdown
## Taty + OmniRoute Compatibility Assessment

### Current Architecture
- WhatsApp → Chatwoot Bridge → Hermes → TatyAgentService
- Embeddings: pgvector in Supabase
- Similarity search: /api/v1/kb/search-similar

### OmniRoute Capabilities
- Embedding models: [LIST FROM OMNIROUTE]
- Latency: [MEASURED]
- Cost: [FREE vs PAID]

### Recommendation
[CAN/CANNOT use OmniRoute for Taty]
[IF CAN: which combo, what changes needed]
[IF CANNOT: why, alternatives]
```

## Success Criteria

1. OpenSpec spec created and approved
2. All 6 combos tested and working
3. Backend can route through OmniRoute
4. Taty analysis complete with recommendation
5. Pilot framework documented
6. All agents (Claude Code, Hermes, Codex) aware of OmniRoute
7. Documentation follows specboot patterns

## Important Notes

- Follow specboot: small tasks, TDD, English only, incremental changes
- Use OpenSpec for all changes (propose → apply → archive)
- Don't modify production without HITL approval
- Test with shadow-mode before real traffic
- Keep Mimo as fallback until pilot confirms metrics
