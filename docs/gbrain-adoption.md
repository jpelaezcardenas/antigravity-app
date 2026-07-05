# GBrain Adoption — Architecture Reference

Canonical design lives in the OpenSpec change
[`openspec/changes/adopt-gbrain-second-brain/`](../openspec/changes/adopt-gbrain-second-brain/)
(`proposal.md`, `design.md`, `specs/`, `tasks.md`). This doc is the durable summary that
survives archival of that change.

## What GBrain is

[GBrain](https://github.com/jpelaezcardenas/garrytan-gbrain) is Garry Tan's MIT-licensed,
self-hosted knowledge engine (TypeScript / Bun, PostgreSQL + pgvector, PGLite embedded option).
Contexia **adopts** it (`git clone` + `bun link`, per its own documented install path — NOT
`bun install -g github:...`, which is a known-broken path per the tool's own issue #218) rather
than building a custom Python equivalent. It provides:

- **Three-way hybrid search** — vector (OpenAI `text-embedding-3-large`) + keyword + Claude-Haiku
  multi-query expansion, fused by reciprocal rank fusion with deduplication.
- **Auto-wiring entity knowledge graph** — typed relationships (`attended`, `works_at`,
  `invested_in`, `founded`, `advises`, ...) inferred from markdown links/wikilinks.
- **`gbrain dream` (Dream Cycle)** — a maintenance cycle (lint → backlinks → sync → extract →
  embed → orphans) runnable on a schedule via `gbrain autopilot --install` or cron. This is the
  "always-on / compound interest" mechanism — not a separately-named subsystem, but the real
  CLI command backing that behavior.
- **`gbrain sync --repo <path>`** — re-index on markdown change, via either `--watch [--interval N]`
  (continuous, long-running — confirmed present in `gbrain --help`) or `--install-cron` (periodic
  daemon). Both are real, native options.
- **Native MCP server + native Hermes Agent integration** — one brain, many tools.
- **26 skills** organized under `skills/RESOLVER.md` (the skill dispatcher): 8 "original"
  (ingest, query, enrich, maintain, briefing, migrate, setup, publish) + brain skills
  (signal-detector, brain-ops, idea-ingest, media-ingest, meeting-ingestion, citation-fixer,
  repo-architecture, skill-creator, daily-task-manager) + operational/identity skills.

## Two-repo architecture (hard rule, not a preference)

GBrain's own docs (`docs/guides/repo-architecture.md`) mandate separating **agent behavior**
(replaceable) from **world knowledge** (permanent) into two repos. Contexia follows this exactly:

- **`antigravity-app`** (this repo) — the agent-config/product role. Holds `CLAUDE.md`/`AGENTS.md`
  librarian instructions (§10), `ai-specs/skills/`, `openspec/changes/`, and the canon docs
  (GLOSARIO-MAESTRO, `AGENTES.md`, `.antigravity/GROUND_TRUTH.md`). **Never holds brain content.**
- **`contexia-brain`** (sibling repo) — the brain repo GBrain indexes. Holds `raw/` (capture
  inbox) and the MECE compiled directories (`people/`, `companies/`, `deals/`, `meetings/`,
  `concepts/`, `ideas/`, `media/`, `sources/`, `archive/` — adapted from GBrain's default
  20-directory VC-oriented schema to Contexia's B2B agency domains; see its `README.md` and
  `RESOLVER.md` for the adaptation and what was deliberately excluded).

**Why this had to be a hard split:** `antigravity-app`'s `main` branch auto-deploys to
Vercel/Railway on every push (see `ARCHITECTURE.md`). GBrain's autonomous Dream Cycle/autopilot
commits to the brain repo on a schedule. If brain content lived in `antigravity-app`, every
autonomous brain-maintenance run would trigger an unintended production deployment. Splitting
repos makes this structurally impossible, not just a policy to remember.

## How it fits Contexia (three layers)

- **Layer 0 — markdown foundation:** `contexia-brain/raw/` (unstructured inbox) + the MECE
  compiled directories, plus librarian instructions in `antigravity-app`'s `CLAUDE.md`/`AGENTS.md`
  (§10). The canon docs in `antigravity-app` (GLOSARIO-MAESTRO, `AGENTES.md`, ground-truth) are
  indexed as-is by GBrain; `contexia-brain/concepts/` pages cross-reference rather than duplicate
  them. `antigravity-app/scripts/harvest_stage11_reports.py` feeds completed Stage 11
  deployment-report learnings into `contexia-brain/raw/` so they compound.
- **Layer 1 — GBrain engine:** runs locally (Bun sidecar) alongside Hermes, indexing
  `contexia-brain` only. Storage: a **dedicated Supabase schema** — never `knowledge_chunks`.
  Exposed via MCP to Claude Code / Codex and via native integration to Hermes.
- **Layer 2 — multi-tenant client product (future, separate change):** one Supabase project,
  one Postgres schema per client, a small connection broker (`user → tenant → schema/DSN`).

## Hard isolation boundary

GBrain **does not touch** the existing decision-memory pipeline: `knowledge_chunks`,
`decision-vectorization`, `similarity-search`, and the `contexia-agents` MCP server all remain
unchanged. GBrain uses its own schema and its own MCP server. Two systems, two concerns —
Centinela's historical-decision matching is unaffected.

## Data sovereignty

GBrain's **process** runs local/on-prem alongside Hermes (satisfies the settled decision
"Hermes never runs on cloud VPS"). Only its **durable storage** (Postgres) lives in the shared
Supabase project. Compute stays sovereign; only storage is shared infrastructure. GBrain is
never deployed to Railway or any cloud compute.

## Portability

Brain content is plain markdown in git (`contexia-brain` repo). If GBrain is ever dropped,
`raw/` + the MECE compiled directories + the canon docs in `antigravity-app` remain fully
usable — no vendor lock-in, no proprietary format.
