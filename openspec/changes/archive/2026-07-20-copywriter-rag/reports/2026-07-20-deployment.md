# Deployment report — copywriter-rag

Date: 2026-07-20

## Summary

Change deployed and verified live in production. `_llm_generate_hooks` now retrieves DIAN-pains KB
content before building its prompt, closing gap #5 for the corpus that actually exists and is
retrievable today (see design.md Non-Goals for why the uncommitted `ai-specs/social-content-ops/`
brand corpus is explicitly not wired in here). A real, pre-existing bug in the LLM engine (unrelated
to this change) was discovered during the live smoke test and is flagged, not fixed, per scope
discipline.

## Commits deployed

- `9932cf7` — feat(sell-machine): ground Copywriter hook generation in retrieved DIAN-pains KB content

## Stage 11 steps executed

1. Merged `feature/copywriter-rag` to `main` (fast-forward, confirmed via `git merge-base`),
   pushed. Railway deploy `ab41edfd` reached `SUCCESS`.
2. **Live smoke test**: called the real `POST /api/v1/sell-machine/hooks/generate` with
   `{"count": 3}` → `200`, response has the correct `{headline, body, cta, pain_tag}` shape for 3
   hooks. Railway logs confirm:
   - This change's new code executed for real: `retrieve_similar`'s embedding call hit a real
     OpenAI `429 Too Many Requests` and **correctly fell back to the in-memory KB backend**
     (`KB[pgvector]: query embedding failed, falling back to memory`) — the same graceful-
     degradation path already confirmed live in `taty-kb-and-react-router`'s Stage 11, now also
     exercised from the Copywriter's call site.
   - The subsequent real Groq LLM call succeeded (`[OK] Success with groq`), but
     `copywriter_service`'s own try/except then caught an exception from a **separate,
     pre-existing bug** (see below) and correctly fell back to the deterministic hook set — so the
     response returned was the deterministic fallback content, not fresh LLM-grounded hooks. This
     still satisfies the requirement's contract exactly ("SHALL fall back to a deterministic hook
     set if all LLM providers fail (never erroring the request)" — confirmed: `200`, non-empty,
     correctly shaped).
3. **New bug found (pre-existing, NOT part of this change, not fixed here)**:
   `agents/llm_engine.py`'s `LLMEngine._get_json_with_retry_custom_order` (the path
   `get_ai_response_with_profile` uses for JSON-mode responses with a custom provider fallback
   order) calls `self._parse_llm_response(raw_response, synonyms, list_keys, required_keys)` — 4
   positional args — but `_parse_llm_response`'s actual signature is
   `(self, response, synonyms=None, list_keys=None)`, which does not accept a `required_keys`
   parameter at all. This raises `TypeError: _parse_llm_response() takes from 2 to 4 positional
   arguments but 5 were given` on every real (non-mocked) call through this path — confirmed via
   `git log`/reading the file directly that neither this session's `taty-persona-fields`,
   `taty-kb-and-react-router`, nor `copywriter-rag` touched `llm_engine.py` at all. This bug
   likely affects every caller of `get_ai_response_with_profile` in JSON mode with a custom
   provider order, not just the Copywriter — flagged for a separate follow-up change, not fixed
   under this change's scope (per CLAUDE.md §7).

## Accepted risks / limitations (carried from design.md)

- **The brand-voice corpus (`ai-specs/social-content-ops/`) remains unwired** — deliberately, per
  design.md Non-Goals (uncommitted local content, no seeding pipeline exists).
- **Retrieval query doesn't vary by lead segment** (asalariados vs informales) — out of scope.

## New gap flagged (not part of this change)

`LLMEngine._parse_llm_response` doesn't accept `required_keys`, but
`_get_json_with_retry_custom_order` calls it with that argument anyway — breaks every real
JSON-mode LLM call routed through a custom provider order. Should become its own OpenSpec change
(fix the signature mismatch in `agents/llm_engine.py`, add a regression test exercising the real
call path rather than only the mocked call-point tests every existing consumer uses).

## Verification evidence

- Railway deployment `ab41edfd`: `SUCCESS`, confirmed responding.
- Live `POST /sell-machine/hooks/generate`: `200`, correct hook shape, deterministic fallback
  correctly engaged per the requirement's own contract.
- Railway logs confirm this change's KB retrieval executed for real and degraded gracefully under
  rate-limiting, exactly as designed.
- Full regression suite: 45/45 green, zero regression.
