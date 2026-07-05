# gbrain-adoption Specification

## Purpose
Adopts GBrain (github.com/jpelaezcardenas/garrytan-gbrain — Garry Tan's MIT-licensed, self-hosted TypeScript/Bun knowledge engine) as Contexia's Level-5 second-brain knowledge layer, isolated from the existing `knowledge_chunks`/`decision-vectorization`/`similarity-search` pipeline, running locally in WSL alongside Hermes, and reachable from Claude Code, Codex, and Hermes via MCP. Established by `adopt-gbrain-second-brain` (2026-07-05).

## Requirements

### Requirement: GBrain Runs Isolated From Existing pgvector Pipeline
The system SHALL install and run GBrain (Bun runtime, cloned per its documented `git clone` + `bun link` path) against a Postgres schema dedicated to GBrain, separate from `knowledge_chunks` and any table used by the `decision-vectorization` or `similarity-search` capabilities. GBrain SHALL NOT read from or write to `knowledge_chunks`. GBrain's `sync`/import target SHALL be the `contexia-brain` repository only — it SHALL NOT index `antigravity-app`.

#### Scenario: GBrain schema does not overlap existing tables
- **WHEN** GBrain is installed and initialized against Supabase
- **THEN** it creates its entity/timeline/graph tables in a schema distinct from the one containing `knowledge_chunks`

#### Scenario: Dev validation before any shared schema use
- **WHEN** GBrain is first installed
- **THEN** it is validated against a dev Supabase schema before being pointed at any schema Centinela's tables depend on

#### Scenario: Centinela pipeline unaffected
- **WHEN** GBrain ingests `contexia-brain` content and builds its knowledge graph
- **THEN** `/api/v1/kb/search-similar` and Centinela's historical-decision matching continue to return identical results to before this change

#### Scenario: GBrain sync target is the brain repo, not antigravity-app
- **WHEN** `gbrain sync` (or the autopilot daemon) runs
- **THEN** its configured `--repo` path points at `contexia-brain`
- **AND** `antigravity-app` never appears as a sync/import target

### Requirement: GBrain Skill Catalog Generated From AGENTES.md
The system SHALL generate GBrain `skills/*.md` files (one per Contexia agent: Taty, Centinela, Pulso, Radar, Auditoría Sombra, Social Ops, KB, Orchestrator, Approval Queue) as a projection of `ai-specs/agents/AGENTES.md`. `AGENTES.md` SHALL remain the canonical source; the generated skill files SHALL NOT be hand-edited independently of it.

#### Scenario: Skill file reflects AGENTES.md entry
- **WHEN** `AGENTES.md` describes an agent's endpoint, purpose, and HITL requirement
- **THEN** the corresponding generated `skills/<agent>.md` file contains a SKILL.md contract with a matching resolver trigger

#### Scenario: AGENTES.md change requires regenerating skills
- **WHEN** `AGENTES.md` is updated (new agent, changed endpoint, etc.)
- **THEN** the corresponding `skills/*.md` file is regenerated, not manually patched out of sync

### Requirement: Embedding Provider Is Configured and Documented; Multi-Query Expansion Is Optional
The system SHALL configure GBrain with an explicit embedding provider (GBrain's default: OpenAI `text-embedding-3-large`), backed by an API key available to the **local** GBrain process only, managed via Bitwarden per Contexia's secrets convention, and independent of the `EMBEDDING_PROVIDER` convention used by `decision-vectorization` (which governs a separate, untouched table). Multi-query expansion (GBrain's default: Claude Haiku) is a genuinely optional enhancement, per GBrain's own documented behavior ("without Anthropic, search works but skips query expansion") — the system MAY run without an `ANTHROPIC_API_KEY` configured, and doing so is not a defect. If a key is later configured, it SHALL be sourced from Bitwarden, never a mismatched or placeholder value.

#### Scenario: Embedding provider explicit and working
- **WHEN** GBrain generates an embedding for ingested content
- **THEN** it uses the configured provider (OpenAI by default) with its key sourced from Bitwarden-managed local environment, not committed to git

#### Scenario: Multi-query expansion works when configured
- **WHEN** a real Anthropic API key (`sk-ant-...` format) is configured
- **THEN** GBrain calls Claude Haiku for query expansion using its own local key, separate from the FastAPI backend's own LLM provider keys/rate limits

#### Scenario: System remains functional without multi-query expansion
- **WHEN** no `ANTHROPIC_API_KEY` is configured (e.g., only a valid `OPENAI_API_KEY` is present)
- **THEN** GBrain's vector and keyword search still function fully; only the query-expansion widening step is skipped
- **AND** this SHALL NOT be treated as an installation failure

#### Scenario: A mismatched key is rejected, not silently accepted
- **WHEN** a candidate key for `ANTHROPIC_API_KEY` does not match Anthropic's key format (`sk-ant-...`)
- **THEN** it is not written to GBrain's configuration; the system proceeds without multi-query expansion rather than configuring a key that will fail at call time

#### Scenario: Provider choice does not affect decision-vectorization
- **WHEN** GBrain's embedding/expansion providers are configured
- **THEN** the `EMBEDDING_PROVIDER` setting and behavior of `decision-vectorization`/`knowledge_chunks` remain unchanged

### Requirement: Three-Way Hybrid Search and Entity Graph Are Functional
The system SHALL verify that GBrain's three-way hybrid search (vector via embeddings + keyword + multi-query expansion, fused by reciprocal rank fusion with deduplication) and its auto-wired entity knowledge graph are operational against ingested Contexia content — not merely installed. These are validated requirements, not spot checks.

#### Scenario: Semantic query outperforms keyword-only
- **WHEN** a natural-language query is issued whose wording does not exactly match the source text (e.g., "monitoreo de vencimientos DIAN" against a page titled "Centinela Fiscal")
- **THEN** GBrain returns the relevant page via vector/multi-query expansion, not only exact keyword matches

#### Scenario: Entity relationships are traversable
- **WHEN** GBrain has ingested Contexia's canon docs and raw notes
- **THEN** querying an entity (e.g., Centinela) surfaces its typed relationships (e.g., links to DIAN, Stage 11, Approval Queue) via graph traversal

#### Scenario: Duplicate content collapsed across search paths
- **WHEN** the same content is reachable via both vector and keyword search
- **THEN** the fused result set returns it once, not duplicated per path

### Requirement: Autonomous Maintenance Cycle Scheduled (gbrain dream / autopilot)
The system SHALL enable and schedule GBrain's maintenance cycle (`gbrain dream`, composing lint → backlinks → sync → extract → embed → orphans) via `gbrain autopilot --install` or an equivalent cron entry, so the brain enriches itself autonomously: scanning recent captures for new entities, detecting and fixing missing cross-references/broken citations, consolidating scattered notes into compiled pages, and enriching existing entries. This runs on a recurring schedule without manual invocation. This capability — not manual curation — is the intended enrichment path once GBrain is live. (Referred to as "Dream Cycle" in Contexia's own docs/marketing framing; the underlying CLI command is `gbrain dream`.)

#### Scenario: Maintenance cycle runs on schedule
- **WHEN** the configured schedule fires (e.g., nightly)
- **THEN** `gbrain dream` processes recent `contexia-brain/raw/` captures and updates compiled pages without a human triggering it

#### Scenario: New entity captured overnight becomes searchable
- **WHEN** a raw note mentioning a new entity is added, and the maintenance cycle subsequently runs
- **THEN** that entity is detected, linked, and returned by a hybrid-search query the next day

#### Scenario: Maintenance cycle failure is non-destructive
- **WHEN** a `gbrain dream` run fails or is interrupted
- **THEN** no source markdown is lost or corrupted (git remains the system of record) and the next run resumes safely, per `CycleReport`'s resumable phase design

### Requirement: Periodic Re-Sync on Repo Change
The system SHALL run `gbrain sync --repo contexia-brain` so that brain markdown changes are re-indexed without manual re-import, via one of two mechanisms GBrain natively supports: `gbrain sync --watch [--interval N]` (a continuous, long-running watch process) or `gbrain sync --install-cron` (a periodic daemon, e.g. every 10-15 minutes). Either satisfies this requirement; in practice, `gbrain autopilot`'s own internal cycle (which includes a sync phase) may also satisfy it without a separate dedicated process.

#### Scenario: Edited page re-indexed on the next scheduled sync
- **WHEN** a brain markdown file is edited and saved, and the next scheduled `gbrain sync` runs
- **THEN** GBrain's index reflects the change so subsequent queries return updated content

#### Scenario: Git remains the source of truth
- **WHEN** GBrain's index and the markdown files disagree (e.g., index stale)
- **THEN** a re-sync rebuilds the index from the markdown files, never the reverse

### Requirement: GBrain Native Skill Modules Exposed via MCP
The system SHALL confirm GBrain's built-in skill modules (ingestion, query, maintenance, enrichment, briefing, migration) are available through its MCP server, distinct from and additional to the Contexia agent projection generated from `AGENTES.md`.

#### Scenario: Native modules present alongside Contexia projection
- **WHEN** an MCP client introspects GBrain's server
- **THEN** both GBrain's native skill modules AND the Contexia agent skills (projected from AGENTES.md) are discoverable
- **AND** the Contexia projection is confirmed to supplement, not overwrite, the native modules

#### Scenario: Query module returns synthesized answer
- **WHEN** the query skill module is invoked with a natural-language question
- **THEN** it returns ranked, deduplicated results with synthesis (not raw row dumps)

### Requirement: Full MCP Tool Surface Verified by Count and Category Coverage
The system SHALL verify, by direct MCP introspection, that GBrain exposes at least 30 tools, and that at least one tool from each native skill-module category (ingestion, query, maintenance, enrichment, briefing, migration) is present and successfully callable. This verification SHALL NOT be inferred from "skill modules present" alone — the tool count and per-category coverage are checked explicitly.

#### Scenario: Tool count meets the documented minimum
- **WHEN** an MCP client (e.g., Claude Code) calls GBrain's tool-listing endpoint
- **THEN** the returned tool count is at least 30

#### Scenario: Every skill-module category has at least one callable tool
- **WHEN** the tool list is grouped by originating skill module
- **THEN** ingestion, query, maintenance, enrichment, briefing, and migration each have at least one tool present
- **AND** one representative tool per category is invoked successfully in a smoke test

### Requirement: GBrain Reachable From Claude Code, Codex, and Hermes
The system SHALL expose GBrain's native MCP server to Claude Code Desktop and Codex, and SHALL wire GBrain's native Hermes Agent integration into Hermes Workspace, such that an equivalent knowledge query returns consistent results regardless of which tool issues it.

#### Scenario: Same query, same answer across tools
- **WHEN** a query such as "¿dónde está Centinela?" is issued from Claude Code via GBrain's MCP server
- **AND** the same query is issued from Hermes Workspace via GBrain's native Hermes Agent integration
- **THEN** both resolve to the same skill/endpoint reference

#### Scenario: GBrain MCP server coexists with contexia-agents MCP server
- **WHEN** both the existing `contexia-agents` MCP server (action invocation) and GBrain's MCP server (knowledge retrieval) are registered with the same MCP client
- **THEN** both are independently discoverable and callable without conflict

### Requirement: Local-Only Execution (Data Sovereignty)
GBrain SHALL run exclusively on-prem/local (alongside Hermes), consistent with the existing constraint on the `contexia-agents` MCP server. It SHALL NOT be deployed to cloud compute, even though its Postgres storage lives in the shared Supabase project.

#### Scenario: GBrain process bound to local execution
- **WHEN** GBrain is running
- **THEN** its process executes on the local/on-prem machine (not a cloud VPS or Railway container)

#### Scenario: Only the Postgres connection is remote
- **WHEN** GBrain needs durable storage
- **THEN** it connects outbound to the existing Supabase project's Postgres instance
- **AND** no GBrain compute is ever deployed to that cloud environment

### Requirement: Antigravity MCP Compatibility Documented
The system SHALL document, via a time-boxed spike, whether Antigravity IDE and Antigravity 2.0 support MCP clients capable of reaching GBrain's MCP server. If unsupported, the fallback (direct markdown read of `raw/`/wiki docs) SHALL be recorded as the interim access path for those tools.

#### Scenario: MCP supported
- **WHEN** the spike confirms Antigravity supports an MCP client
- **THEN** GBrain's MCP server is wired to it the same way as Claude Code/Codex

#### Scenario: MCP unsupported
- **WHEN** the spike finds no MCP client support in Antigravity
- **THEN** the fallback path (reading `raw/` and wiki markdown directly) is documented as the interim solution for that tool
