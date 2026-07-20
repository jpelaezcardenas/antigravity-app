## Why

`agents/llm_engine.py`'s `_get_json_with_retry_custom_order` (used by
`get_ai_response_with_profile`'s JSON-mode path, the one every profile-based agent call uses) calls
`self._parse_llm_response(raw_response, synonyms, list_keys, required_keys)` expecting a
`(parsed, is_valid)` tuple back. The actual `_parse_llm_response` signature is
`(self, response, synonyms=None, list_keys=None) -> Dict` — it accepts no `required_keys` argument
and returns a plain `Dict`, not a tuple. Every real (non-mocked) call through this path raises
`TypeError: _parse_llm_response() takes from 2 to 4 positional arguments but 5 were given`.

This was discovered live, twice, during this session's Stage 11 verifications for
`copywriter-rag` and `activate-telemetry-loop`: both `copywriter_service.generate_hooks` and
`agents/content_evaluator.py`'s hook tone-check silently fall back to their documented
degradation behavior (deterministic hooks; hard-ban-only evaluation) on every real call, never
actually using the LLM's JSON response. The bug has been silently eating the real functionality of
every consumer of this code path — it just never crashed the caller because each caller already
has its own try/except around the LLM call for unrelated resilience reasons.

## What Changes

- `_get_json_with_retry_custom_order` is rewritten to mirror the already-correct sibling function
  `_get_json_with_retry`'s pattern exactly: call `_parse_llm_response` for parsing only (no
  `required_keys` argument), then separately call the existing `_validate_required(parsed,
  required_keys)` to determine validity, and use `_validate_required`'s `(is_valid, missing)`
  tuple to decide whether to retry or return — replacing the broken tuple-unpacking of
  `_parse_llm_response`'s return value.
- `_parse_llm_response`'s own signature and behavior are unchanged — the bug is entirely in its
  caller, not in the parsing logic itself.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
(none — this is an internal bugfix in a shared utility, not a change to any documented capability's
requirements/behavior contract. No `openspec/specs/` capability documents this internal method.)

## Impact

- `apps/backend/agents/llm_engine.py` — the only file touched.
- Every consumer of `get_ai_response_with_profile` in JSON mode with a custom provider order
  (confirmed affected: `copywriter_service.py`, `agents/content_evaluator.py`) starts actually
  using real LLM JSON responses instead of always silently falling back.
- No migration, no new endpoint, no frontend change.
