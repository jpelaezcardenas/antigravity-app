## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/manus-gtm-patches-b3-b4-b5` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Bug Fix: poller.py Dispatch Indentation

- [x] 1.1 Identified: `created = manus_client.create_task(...)` landed inside the
      `if not backend_client.mark_dispatched(...): ... continue` block (dead code after
      `continue`), causing `UnboundLocalError` on every successful claim
- [x] 1.2 Fixed: moved the call to its correct position, sibling to the claim-guard, matching
      the pre-existing structure

## 2. Failing Tests First (TDD) — Dispatch-Time Schema Coverage

- [x] 2.1 Added failing tests to `test_poller.py`: a `research` task dispatch calls
      `create_task()` with `structured_output_schema=RESEARCH_HOOKS_SCHEMA`; a non-`research`
      task dispatch calls it with `structured_output_schema=None`
- [x] 2.2 Confirmed they fail against the pre-fix code (via manual trace — the pre-fix code
      raised `UnboundLocalError` before `create_task` was ever meaningfully asserted on)

## 3. Implementation

- [x] 3.1 Bug fix (section 1) + already-applied B3/B4/B5 code confirmed correct via syntax check
      and full suite run
- [x] 3.2 Run and confirm all tests pass

## 4. Run Unit Tests and Verify State (MANDATORY)

- [x] 4.1 Ran the full `apps/hermes-manus-poller/tests` suite
- [x] 4.2 No database touched — noted, no migration/DB verification needed
- [x] 4.3 Create report
      `openspec/changes/manus-gtm-patches-b3-b4-b5/reports/YYYY-MM-DD-unit-test-verification.md`
- [x] 4.4 Mark complete only after report exists and tests are green

## 5. Not Applicable: Manual Endpoint / E2E Testing

- [x] 5.1 Local scheduled-task service, no HTTP endpoint, no frontend — not applicable

## 6. OpenSpec: Sync Spec + Documentation

- [x] 6.1 Confirmed the delta spec matches the implemented/verified behavior
- [x] 6.2 No canon doc references to update

## 7. Deploy (Local Service — Stage 11 Adapted)

- [x] 7.1 Commit + merge into `main` + push
- [x] 7.2 **Founder action required:** `git pull` + restart `ContexiaHermesManusPoller` scheduled
      task (same as after `manus-content-retrieval` — env/code changes need the next tick or a
      manual restart to take effect)
- [x] 7.3 Create deployment report:
      `openspec/changes/manus-gtm-patches-b3-b4-b5/reports/YYYY-MM-DD-deployment.md`

## 8. Archive

- [x] 8.1 Run `openspec-sync-specs` to merge the delta spec into
      `openspec/specs/hermes-manus-poller/spec.md`
- [x] 8.2 Archive this change once Stage 11 is documented and all tasks above are checked
