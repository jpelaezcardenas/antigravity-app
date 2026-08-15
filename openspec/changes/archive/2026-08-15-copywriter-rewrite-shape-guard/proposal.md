## Why

Running real Manus-sourced hooks through the live evaluate/rewrite pipeline (2026-08-15) crashed
`run_creative_loop()`: `copywriter_service.py::rewrite_hook()` returns whatever
`_llm_rewrite_hook()` gets back from the LLM engine without validating its shape.
`_SYSTEM_PROMPT` (shared between `generate_hooks()` and `rewrite_hook()`'s call sites) explicitly
instructs "Responde en JSON como una lista de objetos" — correct for `generate_hooks()`, which
expects an array, but wrong for a single-hook rewrite. The LLM followed that instruction literally
and wrapped its rewritten hook in a JSON array; that raw `list` propagated into
`evaluate_hooks()` → `evaluate_hook(rewritten)` → `content_evaluator._hook_text()` →
`hook.get(...)` → `AttributeError: 'list' object has no attribute 'get'`, crashing the entire
evaluation loop (zero survivors, no graceful degradation) instead of gating just that one hook.

`rewrite_hook()`'s own docstring already promises "Falls back to returning the original hook
unchanged if the LLM engine is unavailable (never errors)." A malformed response is functionally
the same failure mode as an unavailable engine for this contract — it just currently isn't treated
that way.

## What Changes

- `rewrite_hook()` validates the shape of what `_llm_rewrite_hook()` returns before treating it as
  the rewritten hook:
  - A `list` → take its first well-shaped dict element (has `headline`/`body`/`cta`); if none
    qualify, fall back to the original hook.
  - A `dict` missing `headline`/`body`/`cta` (e.g. the LLM engine's own JSON-parse-failure fallback
    shape `{raw_response, parsing_error, status, message}`) → fall back to the original hook.
  - A well-shaped `dict` → returned as today, unchanged behavior.
- No change to `_SYSTEM_PROMPT`'s wording — fixing the prompt to be call-site-specific is a valid
  future improvement but doesn't close the gap alone (any LLM response shape drift should degrade
  safely, not just this one known trigger).

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `sell-machine-creative-swarm`: the rewrite step of the evaluate/rewrite loop gains a shape guard
  so a malformed LLM rewrite response degrades to "keep the original hook" instead of crashing the
  whole batch evaluation.

## Impact

- `apps/backend/services/copywriter_service.py` (modified: `rewrite_hook()`)
- `openspec/specs/sell-machine-creative-swarm/spec.md` (delta: rewrite-failure behavior)
- No API contract change, no migration, no new dependency.
