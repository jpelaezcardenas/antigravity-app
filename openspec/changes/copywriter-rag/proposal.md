## Why

Gap #5 from the plan-vs-build audit: the Copywriter agent (`services/copywriter_service.py`,
Change E) generates marketing hooks from a single static system prompt with no retrieval —
`_llm_generate_hooks` builds a prompt from a fixed instruction string plus an optional telemetry
report (Change G), but never grounds hook content in the real DIAN fiscal-pain content this repo
already has seeded and retrievable (`services/kb_seeding_service.py`'s `retrieve_similar`, wired
into Taty's lead router in `taty-kb-and-react-router`, this same session). Hooks today are
generated from the LLM's own general knowledge of "fiscal fear" framing, not grounded in Contexia's
actual curated DIAN normograma content — the same retrieval capability now used elsewhere in this
repo for exactly this kind of grounding.

## What Changes

- `_llm_generate_hooks` retrieves a handful of DIAN-pain KB chunks (via the existing, unmodified
  `retrieve_similar` against the shared `"__global__"` pool) and weaves them into the hook-
  generation prompt as grounding context, the same way `_format_telemetry_report` already weaves
  in prior-performance data.
- If KB retrieval returns nothing (empty corpus, backend down), hook generation proceeds exactly
  as before this change — this is additive grounding, not a hard dependency.
- The `ai-specs/social-content-ops/` brand-voice corpus (uncommitted local content, not seeded into
  any KB backend) is explicitly **not** wired in here — see design.md Open Questions. Seeding it
  would be a separate, larger decision (a new ingestion step) that the founder hasn't confirmed.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `sell-machine-creative-swarm`: "Copywriter generates a bounded batch of marketing hooks" gains a
  KB-grounding behavior; the request/response shape and deterministic-fallback guarantee are
  unchanged.

## Impact

- `apps/backend/services/copywriter_service.py` — the only file touched.
- `services/kb_seeding_service.py` — reused as-is (`retrieve_similar`), not modified.
- No migration, no new endpoint, no frontend change.
