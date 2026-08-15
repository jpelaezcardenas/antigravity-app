## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/manus-content-retrieval` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Poller: manus_client.list_messages() — Failing Tests First (TDD)

- [x] 1.1 Added failing tests to `apps/hermes-manus-poller/tests/test_poller.py`:
      `list_messages()` posts to `/v2/task.listMessages` with `task_id`; returns `None` on non-200,
      not-ok body, or any exception (never raises); returns the parsed `messages` list on success
- [x] 1.2 Confirmed failure: `AttributeError: module 'manus_client' does not have the attribute
      'list_messages'`

## 2. Poller: manus_client.list_messages() — Implementation

- [x] 2.1 Implemented `list_messages(task_id)` in `manus_client.py`, mirroring `get_task()`'s
      fail-soft pattern exactly
- [x] 2.2 Confirmed pass

## 3. Poller: Extraction Logic in _resolve_dispatched() — Failing Tests First (TDD)

- [x] 3.1 Added failing tests: structured `hooks` → included verbatim; unstructured text →
      `manus_message`, no `hooks` key; `list_messages()` failure → base result unaffected; last
      successful `structured_output_result` wins over an earlier failed one
- [x] 3.2 Confirmed failure (AttributeError, same as above — shared implementation gap)

## 4. Poller: Extraction Logic — Implementation

- [x] 4.1 Implemented `_extract_manus_output()` (pure, testable without network) in `poller.py`,
      wired into `_resolve_dispatched()` via `result.update(...)` right after building the base
      `result` dict
- [x] 4.2 Confirmed pass — full `TestRunTick` class green (38/38 total), including a hygiene fix to
      `test_error_status_maps_to_failed` (added the missing `list_messages` mock so it stays fully
      network-mocked per this test file's own stated contract)

## 5. Poller: Creative-Brief Prompt Instruction — Failing Tests First (TDD)

- [x] 5.1 Added failing tests to `TestPrompts`: creative-brief research → structured `{"hooks":
      [...]}` instruction present; non-creative research → prompt unchanged
- [x] 5.2 Confirmed failure (`'"hooks"' in prompt` was False before implementation)

## 6. Poller: Creative-Brief Prompt Instruction — Implementation

- [x] 6.1 Implemented the `creative_brief`-gated branch in `prompts.py`'s `research` case (checked
      before the existing generic `research` branch)
- [x] 6.2 Confirmed pass

## 7. Review and Update Existing Unit Tests (MANDATORY)

- [x] 7.1 Run the full `apps/hermes-manus-poller/tests` suite and confirm all pre-existing tests
      (23 before this change) still pass unmodified
- [x] 7.2 Confirmed `get_latest_manus_draft()` needs no changes — re-read it: it reads
      `result["hooks"]`, exactly what this change's `_extract_manus_output()` writes on success

## 8. Run Unit Tests and Verify State (MANDATORY)

- [x] 8.1 Ran the full `apps/hermes-manus-poller/tests` suite — 38/38 passed
- [x] 8.2 No database touched — noted in the report
- [x] 8.3 Report created:
      `openspec/changes/manus-content-retrieval/reports/2026-08-15-step-8-unit-test-verification.md`
- [x] 8.4 Section complete — report exists, all poller tests green

## 9. Not Applicable: Manual Endpoint / E2E Testing

- [x] 9.1 Confirmed and documented in the Step 8 report: no HTTP endpoint, no frontend behavior.

## 10. OpenSpec: Sync Spec + Documentation

- [x] 10.1 Confirmed the delta spec matches the implemented behavior
- [x] 10.2 Grepped `AGENTES.md`/`ARCHITECTURE.md` for poller result-shape references — none found,
      nothing to update

## 11. Deploy (Local Service — Stage 11 Adapted)

This service runs on the founder's local Windows machine (Scheduled Task
`ContexiaHermesManusPoller`), never on Railway/Vercel (`ARCHITECTURE.md` decision #1). There is no
build/deploy pipeline to trigger — "production" for this service means the founder's local
checkout is current.

- [ ] 11.1 Commit + merge `feature/manus-content-retrieval` into `main` + push
- [ ] 11.2 **Founder action required (documented here, not performed by the agent):** run
      `git pull` in the local `antigravity-app` checkout on the machine running the Scheduled
      Task. No restart needed — each tick invokes `python main.py` fresh, so the next scheduled
      tick (within 1 minute) picks up the new code automatically.
- [ ] 11.3 Verification is deferred to the live end-to-end test already in progress this session
      (a real `research` task with a `creative_brief` payload, dispatched through the now-updated
      poller) — not a separate synthetic check here, since that live test is the actual
      verification this change exists to enable.
- [ ] 11.4 Create a short report noting the commit hash and that founder action 11.2 is pending/
      complete: `openspec/changes/manus-content-retrieval/reports/YYYY-MM-DD-deployment.md`

## 12. Archive

- [ ] 12.1 Run `openspec-sync-specs` to merge the delta spec into
      `openspec/specs/hermes-manus-poller/spec.md`
- [ ] 12.2 Archive this change once 11.4's report exists and all tasks above are checked
