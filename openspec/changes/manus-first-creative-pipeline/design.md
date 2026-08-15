## Context

`sell_machine_service.py::run_creative_loop()` today is:

```python
def run_creative_loop(count=5, target_segment=None, use_telemetry=False) -> List[Dict]:
    report = get_telemetry_report() if use_telemetry else None
    hooks = generate_hooks(count=count, report=report)
    return evaluate_hooks(hooks)
```

`evaluate_hooks()` (also existing, unchanged by this proposal) already does the hard part: hard-ban
+ Claim Ledger check (`brand-voice-canonization`, shipped 2026-08-15) + LLM tone check, with one
rewrite pass via `copywriter_service.rewrite_hook()` for anything fixable. The only thing missing
for the Manus-first design is a way to feed raw hooks *in* instead of always generating them via
`copywriter_service.generate_hooks()`.

Separately, `operator_task_service.py` already supports creating a read-only `research` task and
reading its result back (`create_task("research", ...)` / `list_completed_tasks(task_type="research")`)
— this is the existing, already-operational mechanism for getting anything out of Manus and into
Supabase. No new ingestion channel is needed.

## Goals / Non-Goals

**Goals:**
- Let a Manus-produced draft (a list of raw hooks) enter the same evaluate/rewrite/survivor
  pipeline that LLM-generated hooks already go through, so the Content Critic and Claim Ledger gate
  Manus's output exactly as strictly as they gate the internal Copywriter's.
- Zero behavior change for every existing caller that doesn't pass a Manus draft.

**Non-Goals:**
- Not wiring a new HTTP endpoint or Búnker UI control to trigger this path — `run_creative_loop()`
  is already callable from a Python context (a script, a notebook, a future admin action); adding
  a dedicated endpoint is a small, separable follow-up once there's a concrete first sprint to run
  through it, not required to prove the loop closes end-to-end.
- Not changing what happens *after* `evaluate_hooks()` — `create_campaign_package()`, the Approval
  Queue, `operator_tasks`, and the poller are all unchanged; a Manus-sourced survivor is
  indistinguishable from an LLM-generated one once it passes evaluation.
- Not building a schema/validation layer for the Manus `research` task's raw result — Manus's
  result is a completed operator task, an opaque JSON blob; `get_latest_manus_draft()` extracts a
  hook list from it defensively (see Decision 2) rather than trusting its shape.

## Decisions

**1. `manus_draft_hooks` as an optional parameter, not a separate function.**
`run_creative_loop()` already has the exact orchestration shape needed (get hooks → evaluate →
return survivors); branching on whether hooks come from generation or from a draft is a 3-line
diff inside the existing function, not a new code path to keep in sync. A caller that wants the
old behavior passes nothing; a caller with a Manus draft in hand passes it directly — this also
keeps `run_creative_loop()` testable without touching `operator_task_service` at all (unit tests
can just pass a `manus_draft_hooks` list).

**2. `get_latest_manus_draft()` fails closed to `None`, never raises, never guesses.**
A Manus `research` task's `result` column is operator-supplied JSON with no enforced schema. If it
doesn't contain a recognizable `hooks` list (e.g. Manus returned prose instead of structured data,
or no `research` task has completed yet), `get_latest_manus_draft()` returns `None` and the caller
falls back to `generate_hooks()` — exactly the same fail-safe posture `copywriter_service.py` and
`content_evaluator.py` already use for LLM-unavailability (never block or crash the loop; degrade
to the next-best deterministic behavior).

**3. No new task_type.** `research` already exists, is already `READ_ONLY`, and its poller prompt
(`apps/hermes-manus-poller/prompts.py::build_manus_prompt`) already instructs Manus not to invent
facts. Introducing a dedicated `creative_draft` task_type would require touching the poller (a
separately-deployed local service) for a naming preference only — not worth the coordination cost
across two deploy surfaces for this change.

## Risks / Trade-offs

- **[Risk] A Manus `research` result intended for something else (e.g. a DIAN-normograma lookup)
  gets misread as a creative draft.** **Mitigation**: `get_latest_manus_draft()` only reads the
  *most recent* completed `research` task and requires its result to contain a `hooks` key shaped
  like `[{headline, body, cta}, ...]`; anything else returns `None` rather than a wrong guess. The
  founder is expected to know what the latest `research` task was for when invoking this path —
  same operational discipline already required for any manual step in this pipeline.
- **[Trade-off] No endpoint yet, so triggering this path today requires a manual/scripted call.**
  Accepted — see Non-Goals. Building UI for a capability with zero real usage yet is premature; the
  first real sprint (Ola 2's stated goal) can run through a direct call, and the endpoint can be
  added once there's a concrete Búnker screen asking for it.

## Migration Plan

1. Failing tests first: `run_creative_loop(manus_draft_hooks=[...])` skips generation and evaluates
   the passed hooks; `get_latest_manus_draft()` returns `None` on no data / malformed data, and the
   parsed hook list on a well-shaped `research` result.
2. Implement `get_latest_manus_draft()`.
3. Implement the `manus_draft_hooks` branch in `run_creative_loop()`.
4. Sync the `sell-machine-creative-swarm` spec delta.
5. Stage 11: deploy, verify via Supabase MCP that a hand-created `research`-task result is
   correctly read back by `get_latest_manus_draft()` in the live environment, report, archive.

No data migration, no API contract change, no rollback complexity beyond a normal revert.

## Open Questions

None blocking.
