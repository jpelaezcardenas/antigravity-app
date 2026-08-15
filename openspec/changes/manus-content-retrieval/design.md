## Context

`poller.py::_resolve_dispatched()` today, on a terminal Manus task, builds:

```python
result = {
    "manus_task_id": manus_task.task_id,
    "manus_status": manus_task.status,
    "task_url": manus_task.task_url,
    "credit_usage": manus_task.credit_usage,
}
```

and reports that via `backend_client.report_result()`. Nothing here carries what Manus actually
wrote. `GET /v2/task.listMessages?task_id=<id>` (confirmed contract, 2026-08-15) returns:

```json
{
  "ok": true, "task_id": "...",
  "messages": [
    {"type": "assistant_message", "assistant_message": {"content": "..."}},
    {"type": "structured_output_result",
     "structured_output_result": {"success": true, "value": {...}, "error": null}},
    ...
  ],
  "has_more": false
}
```

`create_task()`'s prompt (`build_manus_prompt`) is the only lever that controls whether Manus
produces a `structured_output_result` at all — Manus decides on its own whether/how to structure
output based on what the prompt asks for.

## Goals / Non-Goals

**Goals:**
- Retrieve Manus's actual task output via polling, no new public infrastructure.
- When Manus was asked for and returned structured hook JSON, land it in `result["hooks"]`
  automatically, so `get_latest_manus_draft()` (already shipped, unchanged) finds it.
- Never fabricate a `hooks` list from unstructured text — same fail-closed posture as
  `get_latest_manus_draft()` itself.

**Non-Goals:**
- Not implementing Manus webhooks (`task_stopped` events) — that needs a persistent public callback
  URL (the still-open Cloudflare tunnel work), a materially bigger and separately-scoped effort.
  Polling `task.listMessages` once per terminal task is cheap (one extra HTTP call, only on
  transition to terminal, not every tick) and sufficient for the current task volume.
- Not building a generic "structured output" system for every task_type — only `research` with a
  `creative_brief` payload signal gets the new instruction; `metrics_pull`/`generate_doc`/etc. are
  untouched.
- Not parsing/validating the `hooks` shape beyond what `get_latest_manus_draft()` already does on
  the backend side — the poller writes what Manus returned verbatim under `result["hooks"]`;
  shape validation stays a single source of truth in `get_latest_manus_draft()` (don't duplicate
  the `_REQUIRED_HOOK_KEYS` check in two languages/services).

## Decisions

**1. Poll `task.listMessages` once, right after detecting `is_terminal`, not on every tick.**
`_resolve_dispatched()` already only reaches this code path once per task (state is `forget()`-ed
immediately after reporting), so this is naturally a single extra call per completed task — no
extra load, no rate-limit concern.

**2. Prefer the last `structured_output_result` with `success: true`; ignore earlier ones.**
Manus's message history is chronological; a task can retry structured output internally before
succeeding. Taking the *last* successful one avoids picking up an early failed attempt.

**3. Only write `result["hooks"]` when `structured_output_result.value` itself contains a `hooks`
key shaped as a list — otherwise omit it entirely, don't write a malformed placeholder.**
This means the poller's extraction logic and `get_latest_manus_draft()`'s validation logic overlap
in *intent* (both want "well-shaped hooks or nothing") but are deliberately not shared code across
the two independently-deployed services (poller is local-only Python, backend is Railway Python —
sharing a module would need a package, disproportionate for one small check). Each fails closed
independently; that's a feature (defense in depth), not duplication to fix.

**4. Unstructured content goes to `result["manus_message"]`, not `result["hooks"]`.**
When there's no `structured_output_result` (Manus just wrote prose — e.g. because the payload
didn't signal `creative_brief`, or Manus's task genuinely was e.g. a fiscal lookup), the poller
still surfaces the actual text for a human to read in the Búnker/Supabase, closing the "founder had
to open `task_url` manually" gap even for non-structured tasks — but never promotes free text into
the `hooks` contract.

**5. The structured-output prompt instruction is gated on a `creative_brief` payload key, not on
`task_type == "research"` alone.** Keeps every other existing `research` use (e.g. fiscal
normograma lookups) prompted exactly as before — this is additive, not a behavior change for
non-creative research tasks.

## Risks / Trade-offs

- **[Risk] Manus doesn't reliably honor the structured-output instruction** (it's prompt-based
  compliance, not an enforced API parameter). **Mitigation**: this is exactly why
  `get_latest_manus_draft()` already fails closed to `None` on a missing/malformed `hooks` key —
  worst case, a real Manus run degrades to "no draft found, `run_creative_loop()` falls back to
  internal generation," never a crash or a bad publish.
- **[Trade-off] Polling instead of webhooks means output isn't available until the next 1-minute
  tick after Manus finishes**, not instantly. Accepted — same latency profile the poller already
  has for status resolution; not a regression.

## Migration Plan

1. Failing tests first: `manus_client.list_messages()` fail-soft cases; `poller.py` extraction
   logic (structured success → `hooks` in result; structured failure/absent → `manus_message` in
   result, no `hooks` key; existing terminal-task test still passes with the new call mocked).
2. Implement `list_messages()`.
3. Implement the extraction logic in `_resolve_dispatched()`.
4. Implement the `creative_brief`-gated prompt instruction in `prompts.py`.
5. Sync the `hermes-manus-poller` spec delta.
6. Stage 11 (local service): commit + push to `main`. **Founder action required**: `git pull` on
   the machine running the Windows Scheduled Task — the next tick picks up the new code
   automatically (each tick is a fresh `python main.py` invocation, no daemon to restart).

No data migration, no API contract change on the backend side, no rollback complexity beyond a
normal revert + `git pull` on the local node.

## Open Questions

None blocking.
