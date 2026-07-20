## Context

`get_ai_response_with_profile` (used by every agent that passes `profile_name`, e.g.
`copywriter_service.py`'s `"social-ops-v1"` profile) routes JSON-mode requests to
`_get_json_with_retry_custom_order` when a profile resolves to a custom provider order. That
function calls:
```python
parsed, is_valid = self._parse_llm_response(raw_response, synonyms, list_keys, required_keys)
```
but `_parse_llm_response`'s real signature is:
```python
def _parse_llm_response(self, response, synonyms=None, list_keys=None) -> Dict:
```
— 3 params after `self`, none named `required_keys`, and it returns a `Dict`, not a `(Dict, bool)`
tuple. Every real call raises `TypeError`. The sibling, non-custom-order function
`_get_json_with_retry` shows the pattern that was clearly intended: parse first (no
`required_keys`), then validate separately via the existing `_validate_required(parsed,
required_keys) -> (is_valid, missing_keys)` static method.

## Goals / Non-Goals

**Goals:**
- Make `_get_json_with_retry_custom_order` actually work for real JSON-mode calls, matching its
  sibling's already-correct, already-tested pattern.

**Non-Goals:**
- **Not touching `_parse_llm_response` or `_validate_required`** — both are correct as-is; the bug
  is entirely in how the custom-order function calls them.
- **Not touching `_get_json_with_retry`** (the non-custom-order sibling) — it already works
  correctly and is the reference implementation this change copies the pattern from.
- **Not adding a new test harness pattern** — reuses whatever mocking convention
  `test_llm_engine.py` (if it exists) or the nearest equivalent already uses for `_call_with_failover_custom_order`.

## Decisions

1. **Mirror `_get_json_with_retry`'s structure exactly, adapted only to call
   `_call_with_failover_custom_order` instead of `_call_with_failover`.** Alternative considered:
   change `_parse_llm_response` itself to accept `required_keys` and return a tuple, matching what
   the broken caller expects. Rejected — that would mean changing a function two other call sites
   (line 332, `_get_json_with_retry`, and presumably `_get_json_with_retry`'s own future callers)
   already use correctly with a `Dict`-only return; fixing the caller instead of breaking working
   callers is the smaller, safer change and produces byte-identical retry/error-message behavior
   between the two provider-order variants (arguably a correctness win — before this fix, custom-
   order retries had a completely different retry-prompt wording than the standard path).
2. **Keep the loop identical to `_get_json_with_retry`'s, including its `last_error` variable and
   retry-prompt phrasing** — no new behavior invented, just correctly wired to the custom-order
   failover call.

## Risks / Trade-offs

- **[Risk] Any caller that was silently relying on the always-triggered deterministic/fallback
  behavior might notice a behavior change** (real LLM JSON responses will now actually be used) →
  **Mitigation**: this is the intended fix, not a risk to guard against — every affected caller's
  own documented fallback-on-failure contract (`generate_hooks`, `content_evaluator`) is preserved;
  they just won't hit that fallback path anymore for reasons unrelated to the LLM's actual quality.

## Migration Plan

No migration — pure bugfix in one existing function. Stage 11: call a real endpoint that routes
through `get_ai_response_with_profile` in JSON mode with a custom provider order (e.g.
`POST /sell-machine/hooks/generate`) and confirm via Railway logs that no `TypeError` occurs and
the LLM's real JSON response is used (not the deterministic fallback) — the definitive proof this
bug is fixed, since both `copywriter-rag`'s and `activate-telemetry-loop`'s Stage 11s observed the
fallback engaging every time due to this exact bug.
