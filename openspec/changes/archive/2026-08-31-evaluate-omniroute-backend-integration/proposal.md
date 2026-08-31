# Proposal: evaluate-omniroute-backend-integration

## Why

Hermes' OmniRoute handoff (`docs/integrations/HANDOFF-OMNIRROUTE.md`, Phase 3) proposes adding
OmniRoute as a provider in the backend's LLM cascade (`apps/backend/agents/llm_engine.py`,
today Groq → Cerebras → OpenRouter free → NVIDIA NIM). The founder approved investigating this
as a formal evaluation, explicitly **not** as a direct code change — OmniRoute is currently
scoped as Hermes-only local infrastructure (ARCHITECTURE.md Decision #21), and the backend's
existing exclusion of MiMo/paid Hermes tooling (Decision #7, ToS restriction on "application
backends") means any new third-party gateway in the backend's request path needs the same level
of scrutiny that cascade already received.

## Why this is investigation-only (no code yet)

Before any code touches `llm_engine.py`, three real unknowns need answers:

1. **Reliability of the specific free providers OmniRoute would route through** for backend
   traffic (client-facing, unlike Hermes' own reasoning) — OmniRoute's own project marks some of
   its 16+ providers as "avoid" in risk; which ones would actually be used for Contexia backend
   traffic needs to be pinned down, not assumed.
2. **ToS review** — same category of risk that excluded MiMo from the backend (Decision #7):
   does routing backend traffic through a self-hosted gateway that itself proxies dozens of
   third-party free-tier APIs violate any of those APIs' ToS for "application backend" use?
   Unknown until checked per-provider actually in play.
3. **Latency and failure-mode impact** on customer-facing endpoints (`/financials`, Taty, etc.)
   — the existing cascade already has 4 hops before failing; adding a 5th (itself potentially
   fanning out to more providers) needs a latency/availability budget, not an assumption that
   "more free options = better."

## What Changes (once evaluation completes — NOT started here)

Nothing yet. This proposal's own tasks.md is a **research plan**, not an implementation plan.
Whether `llm_engine.py` gains an OmniRoute provider, and where in the cascade order, depends
entirely on what the research finds.

## Capabilities

### New Capabilities
None yet — pending evaluation outcome.

### Modified Capabilities
None yet — pending evaluation outcome. If the evaluation recommends adoption, a follow-up
change will define the actual `pulso-financials-api`/agent-endpoint impact.

## Impact

- No code touched by this proposal itself.
- `docs/integrations/HANDOFF-OMNIRROUTE.md`/`OMNIRROUTE_SETUP.md` are the source material for
  this evaluation (already persisted, verified, and secret-scanned).
- Output of this change: a design.md documenting the research findings and an explicit
  go/no-go recommendation for the founder — archived either way (a "no-go" is a valid, complete
  outcome of this change, not a failure to close it).
