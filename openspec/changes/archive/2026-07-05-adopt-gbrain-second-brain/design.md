## Context

Contexia's knowledge is split across systems that don't talk to each other: Claude Code (`CLAUDE.md` + `ai-specs/skills/`), Hermes Workspace (native Nous app), and static docs (`AGENTES.md`, GLOSARIO-MAESTRO, ground-truth) that nothing queries programmatically. Two narrow pieces already exist and must be left alone:

- **`mcp-agents-invocation`** (archived, live): a local-only (127.0.0.1, WSL) MCP server, `contexia-agents`, exposing 6 fixed **action** tools (pulso_status, centinela_alerts, radar_risk, auditoria_report, shadow_gl_ingest_dian, approval_queue_list) to Hermes Swarm. It's a tool-invocation bridge, not a knowledge/search layer.
- **`pgvector-persistence` / `decision-vectorization` / `similarity-search`** (archived, live): a `knowledge_chunks` table that vectorizes **only approved decisions**, feeding Centinela's historical pattern-matching via `/api/v1/kb/search-similar`. Narrow by design — it is not, and should not become, a general knowledge base.

Two YouTube-sourced reference patterns for a markdown "second brain" (raw→wiki loop) were evaluated; both are Level 1–2 only (Gary Tan's 5-level framework — plain routing + curated wiki, no semantic/graph search). Neither is GBrain. The actual `garrytan-gbrain` repo (MIT, TypeScript/Bun) is a mature, real tool providing hybrid vector+keyword+graph search, an auto-wiring knowledge graph, a deterministic background job queue ("Minions"), native MCP servers, and native Hermes Agent integration (same Nous Research lineage as Hermes Workspace).

## Goals / Non-Goals

**Goals:**
- Give Contexia's general business knowledge (GLOSARIO-MAESTRO, AGENTES.md, ground-truth, Stage 11 reports) a queryable home, reachable identically from Claude Code, Codex, and Hermes.
- Adopt GBrain rather than reimplement its capabilities in Python.
- Keep the existing decision-memory pipeline (`knowledge_chunks`, Centinela's similarity search) completely untouched.
- Preserve the existing local-only, data-sovereignty constraint that already governs `contexia-agents` and Hermes.

**Non-Goals:**
- Multi-tenant client provisioning (schema-per-tenant, connection broker) — deferred to a future change once this proves value internally (Cliente Cero).
- Replacing or modifying the `contexia-agents` MCP server — it handles actions; GBrain handles knowledge. Two servers, two concerns.
- Confirming Antigravity IDE/2.0 MCP support beyond a time-boxed spike — if unsupported, it falls back to reading `raw/`/wiki markdown directly (no MCP required for that layer).

## Decisions

**1. Adopt real GBrain instead of building a custom Python registry/dispatcher.**
Alternative considered: build `gbrain_registry.py` / `gbrain_dispatcher.py` / `gbrain_sync_manager.py` inside the FastAPI backend (~1500 lines, ~8 weeks). Rejected — GBrain already provides hybrid search (94.6% recall benchmarked), an auto-wiring knowledge graph, and a background job queue (Minions, 753ms vs. >10s spawn timeouts), MIT-licensed and actively maintained. Rebuilding it would duplicate ~70% of a tested tool and create long-term maintenance burden Contexia doesn't need to own.

**2. GBrain gets its own dedicated Postgres schema — never `knowledge_chunks`.**
Alternative considered: extend `knowledge_chunks` with new columns (`source_type`, broader content) to serve both decision-memory and general knowledge. Rejected — `decision-vectorization`'s spec is explicit that only `status = 'approved'` rows get vectorized, and `similarity-search` is explicitly scoped to Centinela's historical-decision use case. Mixing GBrain's broader raw/wiki content into that table would violate an existing, deployed contract and risk polluting Centinela's signal. A separate schema keeps both systems independently correct and avoids any migration risk to a live production table.

**3. GBrain's process runs locally, its storage lives in shared Supabase.**
This resolves an apparent tension with the settled decision "Hermes runs local/on-prem, never cloud VPS." The constraint is about **where compute executes** (financial-data sovereignty), not where durable storage lives. GBrain (the Bun process) runs alongside Hermes on-prem — same posture as the existing `contexia-agents` MCP server, which also binds to `127.0.0.1` only. It simply makes an outbound Postgres connection to Contexia's existing Supabase project for its own tables. Compute stays sovereign; storage is shared infrastructure Contexia already operates and secures.

**4. AGENTES.md remains canonical; GBrain `skills/*.md` are a generated projection.**
Alternative considered: let GBrain's skill files become the new source of truth for agent definitions. Rejected — per CLAUDE.md §6 (symlink integrity), canonical artifacts belong in one place (`ai-specs/agents/AGENTES.md`) with other representations generated/symlinked from it. This avoids the exact fragmentation this change is meant to fix (two competing agent catalogs).

**5. Two separate MCP servers, not one merged server.**
`contexia-agents` (existing) handles **actions** (invoke an agent endpoint). GBrain's MCP server handles **knowledge retrieval** (search, resolve, graph-traverse). Merging them into one surface would conflate two different contracts (typed RPC-style tool calls vs. open-ended semantic queries) and risk destabilizing the already-deployed, JWT-authenticated `contexia-agents` server. Both register independently with any MCP-capable client (Claude Code, Codex, Hermes).

**6. Enable GBrain's self-enriching capabilities from day one — do not ship a static index.**
Alternative considered: adopt GBrain purely as a search index over existing docs and rely on the hand-written librarian loop for enrichment. Rejected — that would deliver a Level-3 static index, not the Level-5 "always-on" brain that was the original goal, and it would duplicate (worse, manually) what GBrain's **Dream Cycle** already does autonomously. Decision: enable the Dream Cycle (scheduled cron enrichment), `sync watch` (continuous re-indexing), and validate the three-way hybrid search + entity graph as **requirements**, not spot checks. The `raw/` inbox remains the human/agent capture surface; the manual librarian loop is demoted to an explicit interim/fallback path so there is no ambiguous, competing enrichment authority. New brain pages adopt GBrain's compiled-truth + timeline two-section model; legacy canon docs (GLOSARIO-MAESTRO, AGENTES.md, ground-truth) are indexed as-is without retrofitting.

**7. GBrain's native skill modules and the AGENTES.md projection are distinct and additive.**
Clarification decision (an earlier draft conflated them): GBrain ships its own skill modules (ingestion, query, maintenance, enrichment, briefing, migration). The generated `skills/*.md` projected from `AGENTES.md` (Contexia's 9 agents) is a **separate, additional** layer that must supplement — never overwrite — the native modules. Both are verified present via the MCP server.

**8. Embedding provider and multi-query-expansion model: adopt GBrain's defaults, do not reuse `decision-vectorization`'s provider choice.**
Alternative considered: reuse Contexia's existing `EMBEDDING_PROVIDER` convention (OpenAI ada-002 primary, Cerebras fallback) from `decision-vectorization` for GBrain too, for consistency. Rejected as the default — GBrain's schema is intentionally isolated from `knowledge_chunks` (Decision #2), so there is no correctness requirement to match providers; matching GBrain's own documented default (OpenAI `text-embedding-3-large` for embeddings, Claude Haiku for multi-query expansion) is lower-risk than reconfiguring an upstream tool's internals. Both require their own API keys available to the **local** GBrain process (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`), managed via Bitwarden per Contexia's secrets convention (never committed, never routed through the FastAPI backend's own key/rate limits — GBrain's usage is a separate cost line). This must be **verified as configured**, not assumed, before Group 3 (hybrid search validation) can meaningfully pass.

**9. The "30+ MCP tools" claim is verified by count and coverage, not assumed.**
Adopting GBrain instead of rebuilding it means Contexia inherits its full tool surface "for free" — but "for free" must still be checked, not assumed. Decision: add an explicit tool-inventory verification (introspect the MCP server, confirm tool count ≥30, spot-check at least one tool per native skill-module category) as its own task, rather than folding it into the general "skill modules present" check.

**10. Brain content lives in a separate `contexia-brain` repo, never inside `antigravity-app` — corrected mid-implementation.**
Discovered while reading GBrain's own `docs/guides/repo-architecture.md` (a hard rule: "Never write knowledge to the agent repo... GBrain indexes the brain repo only") and cross-checking against `ARCHITECTURE.md`: `antigravity-app`'s `main` branch auto-deploys to Vercel/Railway on every push. GBrain's autonomous Dream Cycle/autopilot commits to its brain repo on a schedule. The original plan (Layer 0 folders `raw/`/`brain/` inside `antigravity-app`) would have made every autonomous brain-maintenance run trigger an unintended production deployment. Corrected to: a sibling repo `contexia-brain` holds all brain content (`raw/` + MECE compiled directories); `antigravity-app` keeps only the librarian instructions (pointing at the sibling repo) and the canon docs GBrain indexes alongside it. This is a structural fix, not a policy reminder — the two repos genuinely cannot cross-contaminate a deploy pipeline.

Alternative considered: keep one repo, but exclude the brain paths from Vercel/Railway's build triggers (e.g., ignored paths in deploy config). Rejected — fragile (one config change away from silently re-coupling brain commits to deploys), and still violates GBrain's own agent-repo/brain-repo boundary rule, which exists for reasons beyond deploy safety (privacy/access-control separation, independent brain-vs-agent lifecycle).

**11. GBrain's default 20-directory MECE schema is adapted, not adopted wholesale.**
GBrain ships a VC/personal-relationship-oriented schema (`people/`, `companies/`, `deals/`,
`civic/`, `household/`, `hiring/`, `diligence/`, ...). Contexia is a B2B AI automation agency, so
`contexia-brain`'s schema keeps the domains that map cleanly (`people/`, `companies/`, `deals/`,
`meetings/`, `concepts/`, `ideas/`, `media/`, `sources/`, `archive/`) and deliberately excludes
`projects/` and `prompts/` (already filled by `openspec/changes/` and `ai-specs/skills/` per
Decision 4/the proposal's non-goals) and personal-life domains (`civic/`, `household/`,
`personal/`, `hiring/`, `diligence/`) not relevant to Contexia's scope. Documented in
`contexia-brain/README.md` and `RESOLVER.md` so the adaptation rationale isn't lost.

**12. GBrain runs in WSL (Ubuntu, colocated with Hermes), not natively on Windows.**
Discovered mid-implementation: `gbrain autopilot --install` has no Windows support at all — its source only special-cases macOS (`launchd`); everything else falls through to Unix `crontab`, which doesn't exist on native Windows. Alternative considered: replicate the scheduling manually via Windows Task Scheduler (`schtasks`), keeping GBrain on native Windows. Rejected in favor of moving GBrain into the same WSL Ubuntu environment Hermes already runs in (per the existing "Hermes runs local/on-prem" decision) — this colocates the two local-only processes (useful for the native Hermes Agent integration in a later task), and lets GBrain's own tooling (crontab/systemd, its install docs, its Unix assumptions throughout) work exactly as designed rather than being fought. WSL Ubuntu here has systemd available, so `gbrain autopilot --install` used a proper systemd user service instead of crontab — cleaner than even the Unix fallback path. The native Windows GBrain install (`gbrain-contexia/`, its local PGLite backup at `~/.gbrain/brain.pglite`) is left in place as an already-verified rollback artifact, not actively used going forward.

## Risks / Trade-offs

- **[Risk]** GBrain's internal schema could accidentally collide with existing Supabase objects (naming, extensions) → **[Mitigation]** Install and validate against a **dev** Supabase schema first; only point at the schema Centinela's tables live in after confirming zero overlap in a review step.
- **[Risk]** Antigravity IDE/2.0 may not support MCP, leaving one governance tool (per HARNESS.md's multi-tool list) without direct GBrain access → **[Mitigation]** Time-boxed spike; Layer 0 markdown (`raw/`, wiki docs) remains readable by any tool with file access regardless of MCP support, so no tool is fully blocked.
- **[Risk]** GBrain is an actively developed upstream project; unpinned updates could break the integration → **[Mitigation]** Pin a specific version at adoption time; document the upgrade process as a separate, deliberate task rather than auto-updating.
- **[Trade-off]** Running two MCP servers (`contexia-agents` + GBrain) instead of one adds a small amount of operational surface (two processes to keep running locally) in exchange for keeping the already-deployed action bridge stable and unmodified.

## Migration Plan

1. Add `raw/` inbox + librarian loop instructions (`CLAUDE.md`/`AGENTS.md`) — no infrastructure change, reversible by deleting the folder/edits.
2. Install GBrain locally (Bun) against a **dev** Supabase schema; validate hybrid search and graph-wiring on Layer 0 content before touching anything shared.
3. Generate `skills/*.md` from `AGENTES.md`; verify GBrain's resolver correctly routes representative queries (e.g., "¿dónde está Centinela?").
4. Wire GBrain's MCP server to Claude Code Desktop + Codex; wire native Hermes Agent integration to Hermes Workspace. Verify both surfaces return identical results for the same query (proves single-brain, multi-tool access).
5. Time-boxed Antigravity IDE/2.0 MCP spike; document outcome either way.
6. Update `ARCHITECTURE.md` (Containers table, C4 diagram, new settled decision) in this same change, per the repo's own update rule.
7. Stage 11: deploy, verify, write the deployment report — required before archiving.

**Rollback:** GBrain runs as an isolated local sidecar with its own schema — stopping the process and dropping its schema fully reverts this change with zero impact on `knowledge_chunks`, `contexia-agents`, or any production Centinela/Pulso/Radar flow.

## Open Questions

- Does GBrain's MCP server support being added alongside `contexia-agents` in the same Hermes `~/.hermes/config.yaml` without conflict? To confirm during step 4.
- Should the dev Supabase schema used for initial validation become the permanent GBrain schema, or should a distinct one be provisioned before this reaches Contexia's own production (Cliente Cero) usage? To decide after step 2's validation.
