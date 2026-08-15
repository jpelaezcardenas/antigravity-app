## Why

Testing `manus-first-creative-pipeline` (archived 2026-08-15) surfaced a real gap: the poller's
Manus client only calls `GET /v2/task.detail`, which returns status metadata (`status`,
`credit_usage`, `task_url`) but never the content Manus actually produced. `report_result()`
therefore never writes anything into `operator_tasks.result` beyond that metadata, so
`get_latest_manus_draft()` (which reads `result["hooks"]`) can never find a real Manus draft — the
"Manus produces, the Copywriter refines" loop cannot close with a real Manus task, only with
hand-inserted test data. This was the root cause of the previously-observed "orphan task resolved
by pasting the Manus output manually" pattern (`661d395f…`).

Manus API v2 does expose the actual output: `GET /v2/task.listMessages` (confirmed against
`https://open.manus.ai/docs/v2/task.listMessages.md`, 2026-08-15) returns the task's message
history, including `assistant_message.content` (free text) and, when the task was asked for
structured output, `structured_output_result.value` (parsed JSON). This needs no new public
infrastructure (no webhook callback URL, no Cloudflare tunnel) — it's a second polling call the
already-running poller can make alongside its existing `task.detail` call.

## What Changes

- `apps/hermes-manus-poller/manus_client.py` gains `list_messages(task_id)`: calls
  `GET /v2/task.listMessages`, fail-soft (returns `None` on any failure, matching
  `create_task()`/`get_task()`'s existing pattern — never crashes a tick).
- `apps/hermes-manus-poller/poller.py::_resolve_dispatched()`, after detecting a terminal status,
  calls `list_messages()` and extracts the task's actual output: prefers the last
  `structured_output_result.value` when `success=true`; if a `hooks` list is found there, it's
  written directly into the reported `result["hooks"]` (keeping `get_latest_manus_draft()`
  unchanged — no backend-side code to touch). Falls back to concatenating `assistant_message`
  text into `result["manus_message"]` when no structured output is present, for human review —
  never invents a `hooks` key from unstructured text.
- `apps/hermes-manus-poller/prompts.py`'s `research` branch gains an explicit structured-output
  instruction (`{"hooks": [{"headline", "body", "cta", "pain_tag"}, ...]}`) when the task's
  payload signals a creative-brief request (a `creative_brief` key present) — existing
  non-creative research prompts (fiscal lookups, etc.) are unaffected.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `hermes-manus-poller`: the poller's terminal-task handling gains a second Manus API call
  (`task.listMessages`) to retrieve actual task output, not just status metadata; the research-task
  prompt gains an opt-in structured-output request for creative-brief payloads.

## Impact

- `apps/hermes-manus-poller/manus_client.py` (new `list_messages()`)
- `apps/hermes-manus-poller/poller.py` (modified `_resolve_dispatched()`)
- `apps/hermes-manus-poller/prompts.py` (modified `research` branch)
- `openspec/specs/hermes-manus-poller/spec.md` (delta: content retrieval requirement)
- No backend (`apps/backend/`) changes — `get_latest_manus_draft()` is unchanged, it already reads
  `result["hooks"]`.
- **This is a local-only service** (Windows Scheduled Task on the founder's machine, per
  `ARCHITECTURE.md` decision #1). Stage 11 here means: commit + push to `main`, plus an explicit
  founder action (`git pull` on the local checkout) — the scheduled task re-invokes
  `python main.py` fresh every tick, so no service restart is needed, only a code pull.
