## Why

Contexia's knowledge is fragmented across two isolated systems: Claude Code (CLAUDE.md + `ai-specs/skills/`) and Hermes Workspace (native Nous app). The existing `contexia-agents` MCP server only exposes 6 fixed **action** tools (invoke Pulso, Centinela, etc.) to Hermes — it has no search or knowledge retrieval. The existing pgvector pipeline (`knowledge_chunks`) only vectorizes **approved decisions** for Centinela's historical pattern-matching — it doesn't cover Contexia's general business knowledge (GLOSARIO-MAESTRO, AGENTES.md, ground-truth docs, Stage 11 deployment reports). AGENTES.md itself is a static table nobody can query. There is no discipline for capturing unstructured input (voice notes, meeting summaries, quick decisions) before it's lost, and no way for Claude Code, Codex, or Antigravity to query the same knowledge Hermes has. This is now blocking Contexia's plan to eventually offer a "local second brain" to client businesses via Hermes.

## What Changes

- Add a `raw/` inbox folder and a librarian loop (extending `CLAUDE.md`/`AGENTS.md`) so unstructured input has a home and Stage 11 deployment reports get harvested back into the knowledge base instead of sitting inert in archived changes.
- Adopt **GBrain** (`github.com/jpelaezcardenas/garrytan-gbrain` — Garry Tan's MIT-licensed, self-hosted TypeScript/Bun engine) as the automatic indexing/serving layer, with its **defining capabilities enabled — not just a static index**: three-way hybrid search (vector + keyword + Claude-Haiku multi-query, fused by RRF), the auto-wiring entity knowledge graph, the **Dream Cycle** (autonomous nightly enrichment via cron — the "always-on / compound interest" mechanism), `sync watch` continuous re-indexing, and GBrain's native skill modules (ingestion / query / maintenance / enrichment / briefing / migration), all exposed through its native MCP server and native Hermes Agent integration.
- Generate GBrain `skills/*.md` from `ai-specs/agents/AGENTES.md` (a projection, not a replacement — AGENTES.md stays canonical) so the 9 agents become queryable/resolvable instead of a static table.
- Wire GBrain's MCP server to Claude Code Desktop and Codex, and its native Hermes Agent integration to Hermes Workspace, so all three query the same brain.
- Update `ARCHITECTURE.md` (Containers table, C4 diagram, "Decisiones asentadas") to record GBrain as a new local-only container, consistent with the existing Hermes data-sovereignty decision.

**Explicitly does NOT touch:** `knowledge_chunks`, decision-vectorization, similarity-search, or the `contexia-agents` MCP server. GBrain gets its own dedicated tables in a separate schema — it does not extend or repurpose the approval-decisions-only pgvector pipeline that Centinela depends on. This is intentional isolation, not an oversight.

## Capabilities

### New Capabilities
- `second-brain-raw-loop`: A `raw/` inbox for unstructured captures, a librarian instruction set (CLAUDE.md/AGENTS.md) that proposes wiki updates from it without guessing, and a harvest mechanism that feeds completed Stage 11 reports back in — closing the loop Contexia already half-has.
- `gbrain-adoption`: Installing GBrain locally (Bun), pointing it at a new dedicated Postgres schema in the existing Supabase project (never `knowledge_chunks`), projecting the Contexia agent catalog from AGENTES.md into GBrain skills, and exposing it via MCP (Claude Code, Codex) and native Hermes Agent integration, so every tool queries one brain. Critically, this enables GBrain's **self-enriching** behavior — the scheduled Dream Cycle, continuous `sync watch`, functional three-way hybrid search + entity graph, and the native skill modules — so the brain compounds instead of sitting static. The Contexia agent projection (from AGENTES.md) is **additional to**, not a replacement for, GBrain's built-in skill modules.

### Modified Capabilities
_None._ This change is additive by design; see the isolation note above.

## Impact

- **New local dependency**: GBrain (Bun runtime) — runs alongside Hermes on-prem, never cloud-deployed (same constraint as the existing `contexia-agents` MCP server).
- **New Supabase schema**: dedicated to GBrain's entity/timeline/graph tables; does not alter `knowledge_chunks` or its RPC.
- **Docs updated in this change**: `ARCHITECTURE.md` (new container + settled decision), root `CLAUDE.md`/`AGENTS.md` (librarian loop), `ai-specs/agents/AGENTES.md` unchanged in content but now has a generated projection.
- **Non-goal (deferred to a future change)**: multi-tenant schema-per-tenant provisioning and the client-facing "local second brain per client" product. That depends on this change proving value internally (Cliente Cero) first, per HARNESS.md's one-change-at-a-time rule.
- **Risk carried forward**: Antigravity IDE/2.0 MCP support is unconfirmed; falls back to reading `raw/`/wiki markdown directly if unsupported.
