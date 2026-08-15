## Why

Manus AI's GTM-readiness audit (informe final, 2026-08-15) identified 5 gaps (B1–B5) in the
poller↔Manus contract before the Renta Natural / Envigado go-live. B1 (project_id) was already
resolved by the founder. B3/B4/B5 patches (structured output schema, evidence/idempotency
contract, expirable-asset rule) were applied directly to the working tree by the founder from
Manus's drafted diffs. This change formalizes those already-applied edits through the repo's
mandatory TDD/OpenSpec process, and fixes a real bug the direct patch application introduced.

**Bug found and fixed in the same pass**: the B3 patch's edit to `_dispatch_pending()` in
`poller.py` mis-indented the `created = manus_client.create_task(...)` call — it landed inside the
`if not backend_client.mark_dispatched(...): ... continue` block, after the `continue`, making it
dead code. On the common path (claim succeeds), `created` was never assigned, so `if created is
None:` immediately below would raise `UnboundLocalError` on every single dispatch attempt — the
poller would have crashed on its very next real task, silently breaking the entire GTM circuit at
the worst possible moment. No test caught this because no test exercised the exact
successful-claim-then-dispatch code path introduced by the patch.

## What Changes

- **Fixed** (already applied by this change): `poller.py::_dispatch_pending()`'s `create_task()`
  call moved out of the dead-code branch to its correct position (after a successful claim,
  sibling to the `if not mark_dispatched` guard).
- **B3 — structured output schema** (already applied): `manus_client.py` gains
  `RESEARCH_HOOKS_SCHEMA` and `create_task()` accepts an optional `structured_output_schema`
  param, sent only for `task_type == "research"` dispatches.
- **B4 — evidence/idempotency contract** (already applied): `prompts.py`'s `_APPROVED_BANNER`
  (side-effecting task types) now demands a structured `{post_url, post_id, published_at, status}`
  report, a 24h-duplicate-detection instruction, and a fail-closed PII rule.
- **B5 — expirable-asset rule** (already applied): the creative-brief research prompt now
  instructs Manus to reference only already-uploaded public URLs (`file.upload`), never local/
  private paths.
- **New**: test coverage for B3's dispatch-time behavior (schema passed for `research`, omitted
  otherwise) — the exact gap that let the indentation bug ship untested.

## Capabilities

### Modified Capabilities
- `hermes-manus-poller`: dispatch now sends a structured-output schema for research tasks; the
  approved-content prompt banner gains an evidence/idempotency/PII contract.

## Impact

- `apps/hermes-manus-poller/poller.py` (bug fix + already-applied B3 wiring)
- `apps/hermes-manus-poller/manus_client.py` (already applied: `RESEARCH_HOOKS_SCHEMA`,
  `create_task()` signature)
- `apps/hermes-manus-poller/prompts.py` (already applied: B4/B5 banner text)
- `apps/hermes-manus-poller/tests/test_poller.py` (new: dispatch-time schema coverage)
- `openspec/specs/hermes-manus-poller/spec.md` (delta)
- **Local-only service** — Stage 11 here means commit+push plus a founder `git pull` + scheduled
  task restart (same pattern as `manus-content-retrieval`).
