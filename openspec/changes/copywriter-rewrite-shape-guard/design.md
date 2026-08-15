## Context

```python
def rewrite_hook(hook, reason):
    try:
        rewritten = _llm_rewrite_hook(hook, reason)
        if rewritten:
            return rewritten
    except Exception as exc:
        logger.warning(...)
    return hook
```

`_llm_rewrite_hook()` calls `llm_engine.get_ai_response_with_profile(..., response_format="json")`
and returns whatever it gets — a dict on the happy path, but the LLM engine's JSON parsing can
legitimately produce a `list` (if the model wrapped its answer in an array, which `_SYSTEM_PROMPT`
explicitly asks for) or a dict lacking `headline`/`body`/`cta` (the engine's own parse-failure
fallback shape). Neither is an exception — `rewritten` is truthy either way — so the `if rewritten:
return rewritten` branch returns it as-is, and the caller (`evaluate_hooks()`) crashes trying to
treat it like a hook.

## Goals / Non-Goals

**Goals:** malformed rewrite responses degrade to the original hook, matching the function's
existing documented contract; the fix is a validation guard, not a rewrite of the LLM call itself.

**Non-Goals:** not changing `_SYSTEM_PROMPT`'s array-vs-object wording (a separate, valid future
improvement — see proposal.md's rationale for treating this as defense-in-depth instead); not
touching `generate_hooks()`/`_llm_generate_hooks()`, which already correctly expects (and handles)
a list response.

## Decisions

**Validate in `rewrite_hook()`, not `_llm_rewrite_hook()`.** `_llm_rewrite_hook()` is documented as
"isolated so tests can patch this single call point" — its contract is "return whatever the LLM
engine gave back," which is fine. The shape guarantee belongs at the boundary where the code starts
assuming a specific shape, i.e. right where `rewrite_hook()` decides whether to use `rewritten` or
fall back — same place the existing `if rewritten:` truthiness check already lives.

**List handling: take the first well-shaped element, not just "reject if not a dict."** The LLM's
literal-array-wrapping behavior (confirmed live) is a single hook wrapped in a 1-element list in
the observed case; unwrapping it is more useful than discarding a response that actually contains
the correct rewrite. If the list is empty or its first element isn't well-shaped, fall back to the
original hook — same safety floor either way.

## Risks / Trade-offs

- **[Risk] A list with multiple elements silently picks only the first**, discarding the rest.
  Accepted — `rewrite_hook()`'s contract is "one hook in, one hook out"; a multi-element response
  is itself a shape mismatch with the function's job, and taking the first well-shaped one is a
  reasonable interpretation, not data loss of anything the caller expected structurally.

## Migration Plan

1. Failing tests first: `_llm_rewrite_hook` mocked to return a list → `rewrite_hook()` returns the
   first well-shaped element; mocked to return an empty list → returns the original hook; mocked to
   return a dict missing required keys → returns the original hook; existing well-shaped-dict path
   unchanged.
2. Implement the guard.
3. Re-run the earlier crashing scenario (real Manus hooks through `run_creative_loop`) to confirm
   the fix resolves it in practice, not just in isolated unit tests.
4. Sync the spec delta.
5. Stage 11: deploy, verify via a Railway log check that no new errors appear.

## Open Questions

None blocking.
