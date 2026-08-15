# Unit Test + Deployment Verification Report — manus-gtm-patches-b3-b4-b5

- Date: 2026-08-15
- Change: manus-gtm-patches-b3-b4-b5
- Agent: Claude Code (Sonnet)

## The Bug (why this change exists beyond formalizing patches)

Manus AI applied the B3/B4/B5 diffs to `apps/hermes-manus-poller/` directly via a desktop
filesystem mount, without a Python/pytest environment to verify (Manus's own note: "pytest no está
instalado"). The B3 edit to `poller.py::_dispatch_pending()` mis-indented the
`created = manus_client.create_task(...)` call **inside** the
`if not backend_client.mark_dispatched(...): ... continue` block, after the `continue`:

```python
        if not backend_client.mark_dispatched(operator_task_id):
            logger.warning(...)
            continue

            created = manus_client.create_task(   # <-- dead code, never reached
        content=prompt,                            # <-- also mis-indented args
        ...
    )
        if created is None:                        # <-- created never assigned on the success path
```

On the success path (`mark_dispatched` returns True — the normal case), `created` was never
assigned, so `if created is None:` would raise `UnboundLocalError` on **every** real dispatch. The
poller would have crashed on its next real task, silently breaking the GTM circuit. `ast.parse()`
passed (it's syntactically valid Python), which is exactly why Manus's syntax-only check missed it.

## Fix

Moved the `create_task()` call out of the dead branch to its correct position (sibling to the
claim guard, matching the pre-existing structure), and fixed the argument indentation.

## Commands Executed

- `python -c "import ast; ast.parse(...)"` on all 3 modified files → all valid
- `python -m pytest tests/test_poller.py -v` → **45 passed** (43 pre-existing + 2 new)

## New Test Coverage (the gap that let the bug ship)

- `test_research_task_dispatch_passes_the_native_hooks_schema`: a `research` dispatch calls
  `create_task()` with `structured_output_schema=RESEARCH_HOOKS_SCHEMA`
- `test_non_research_task_dispatch_omits_the_schema`: a non-research dispatch passes `None`

Both exercise the exact successful-claim→dispatch code path that had zero coverage before.

## Applied Patch Confirmation (B3/B4/B5, verified correct)

- **B3** (`manus_client.py`): `RESEARCH_HOOKS_SCHEMA` present, valid JSON-schema shape (root object,
  `additionalProperties:false`, full `required`, ≤5 levels); `create_task()` accepts optional
  `structured_output_schema`, passed only for `research` dispatches. ✔ tested.
- **B4** (`prompts.py`): `_APPROVED_BANNER` includes the `{post_url, post_id, published_at, status}`
  evidence contract, 24h `duplicate_detected` idempotency rule, and fail-closed PII rule. ✔ present.
- **B5** (`prompts.py`): creative-brief research prompt instructs public-URL-only asset references
  (`file.upload`), never local/private paths. ✔ present.

## Database

- Not applicable — local scheduled-task service, no DB.

## Stage 11 (Local Service)

- Committed + pushed to `main`.
- **Founder action required**: `git pull` on the local checkout + restart the
  `ContexiaHermesManusPoller` scheduled task so the next tick runs the fixed code. **This is
  urgent** — the pre-fix code (if the founder's local copy already has Manus's un-fixed version)
  would crash on the next real dispatch; the pull replaces it with the tested fix.

## Outcome

- Status: **PASS**. Bug fixed, tested, and the fix is what reaches production.
