## Context

`_llm_generate_hooks(count, report=None)` in `copywriter_service.py` builds a prompt from a fixed
`_SYSTEM_PROMPT` string plus, optionally, a rendered telemetry report (`_format_telemetry_report`,
Change G). It has no retrieval step at all — hooks are generated purely from the LLM's general
knowledge of "DIAN fear" framing, not grounded in this repo's actual curated fiscal content.
`services/kb_seeding_service.py`'s `retrieve_similar(query, client_id, top_k)` already exists,
already backs a seeded DIAN normograma corpus under the shared `"__global__"` client_id pool, and
was just wired into Taty's lead router in `taty-kb-and-react-router` (this same session) for
exactly this kind of grounding.

Separately, `ai-specs/social-content-ops/` contains brand-voice planning docs (`Base de
conocimientos-Contexia.md`, `content_ops_rules.md`, `OUTPUT_FORMAT.md`, etc.) — but these are
**uncommitted, local files**, not seeded into the KB (`seed_knowledge_base` has never been called
against them), and not part of this repo's tracked state. Treating them as ground truth here would
mean silently depending on content that isn't actually part of the shipped system.

## Goals / Non-Goals

**Goals:**
- Ground hook generation in the same real, already-seeded DIAN-pains KB content Taty's router now
  uses, closing gap #5 for the corpus that actually exists and is retrievable today.
- Preserve `generate_hooks`'s existing deterministic-fallback guarantee exactly — grounding is
  additive, never a new failure mode.

**Non-Goals:**
- **Seeding the `ai-specs/social-content-ops/` brand corpus into the KB.** That corpus is
  uncommitted local content the founder hasn't confirmed as canonical, and ingesting it would be a
  new seeding pipeline (chunking, embedding, a `seed_knowledge_base` call) — a separate, larger
  scope decision, not a natural extension of "wire retrieval into an existing prompt." Flagged as
  an Open Question below rather than assumed.
- **Changing the hook JSON shape** (`{headline, body, cta, pain_tag}`) — unchanged.
- **Changing `rewrite_hook`** — the single-rewrite-pass function is unaffected; RAG grounding only
  applies to initial generation, where the pain-tag framing originates. A rewrite already has a
  concrete hook + rejection reason to work from, which is a narrower, already-grounded task.

## Decisions

1. **Reuse `retrieve_similar` against `"__global__"`, not a new Copywriter-specific KB pool.**
   Alternative considered: seed a separate `client_id` for marketing content. Rejected for now —
   adds a second corpus to maintain with no clear content to seed into it yet (see Non-Goals); the
   existing DIAN-pains pool is exactly the "real fiscal fears" grounding hooks need, and reusing it
   avoids a duplicate KB surface.
2. **Retrieval query is derived from the count/report context, not a fixed string.** When a
   telemetry report is present (Change G), the query favors whatever `pain_tag`s the report shows
   underperforming/overperforming (`hook_performance` keys), giving the grounding a feedback-loop
   flavor consistent with Change G's intent. When no report is present, a generic query ("declarar
   renta, multas DIAN, obligación tributaria") is used — good enough grounding for a cold-start
   generation with no prior signal.
3. **Retrieved chunks are rendered the same way `_format_telemetry_report` renders its section** —
   a labeled block appended to the prompt, keeping `_llm_generate_hooks`'s prompt-construction
   style consistent rather than introducing a different templating approach.
4. **Retrieval failure or an empty result set never blocks generation.** `retrieve_similar` is
   already resilient (falls back to the in-memory KB backend on embedding failure, confirmed live
   in `taty-kb-and-react-router`'s Stage 11) — but this call site additionally wraps it in a
   try/except and proceeds with no grounding section if it raises for any reason, since hook
   generation must never regress to "no hooks at all" over a KB hiccup.

## Risks / Trade-offs

- **[Risk] KB content skews hooks toward DIAN-specific language that may not match all lead
  segments** (e.g. `asalariados` vs `informales`, per the original plan's segment split) →
  **Mitigation**: out of scope for this change — the retrieval query doesn't yet vary by segment;
  a future change could parametrize `generate_hooks(target_segment=...)` if this proves too
  generic in practice.
- **[Trade-off] The brand-voice corpus (tone, specific phrasing rules) remains unwired** — hooks
  are grounded in fiscal *content* (what DIAN pains are real) but not brand *voice* (how Contexia
  specifically phrases things beyond the existing static system prompt). Accepted as a smaller,
  well-scoped win now over a larger, unconfirmed seeding project.

## Migration Plan

No migration — pure logic addition to one existing function. Stage 11: since hook content is LLM
output (not string-matchable), the live smoke test calls `generate_hooks` for real and inspects
that: (a) it doesn't error, (b) Railway logs show a real `retrieve_similar` call happened, (c) the
returned hooks still match the expected `{headline, body, cta, pain_tag}` shape.

## Open Questions

- Should the `ai-specs/social-content-ops/` brand corpus eventually be seeded into the KB (a new
  `client_id`, e.g. `"brand_voice"`) so hooks can be grounded in phrasing rules too, not just DIAN
  fiscal content? Recommend **yes, as a future change**, but only after the founder confirms that
  corpus is meant to be canonical/committed — it's currently untracked local state.
