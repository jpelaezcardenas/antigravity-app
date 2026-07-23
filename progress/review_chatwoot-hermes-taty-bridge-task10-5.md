# Review — task chatwoot-hermes-taty-bridge-10.5

**Verdict:** CHANGES_REQUESTED

## Summary

Design correction (removing the wrong `POST /api/v1/social-ops/onboarding/start` call from the
new-lead branch) is correctly implemented in code and tests, and matches the already-corrected
`design.md` decision 5 / `specs/chatwoot-hermes-bridge/spec.md` requirement text. Full suite is
green (30 passed). However, `apps/chatwoot-bridge/README.md` was not updated and still documents
the removed onboarding-trigger behavior as current — this is a real inconsistency the task's own
"no remaining reference" bar (and the general docs-must-match-code rule) should have caught.

## Checkpoints

- C1 (`main.py` no longer calls `trigger_onboarding`, still calls `set_contact_attributes`): [x]
  — verified via `git diff apps/chatwoot-bridge/main.py`; the single call site
  `await backend_client.trigger_onboarding()` was removed, `chatwoot_client.set_contact_attributes(...)`
  retained unchanged in the new-lead branch.
- C2 (`backend_client.py`'s `trigger_onboarding` genuinely removed, docstring corrected): [x]
  — function body fully deleted (not just orphaned); module docstring rewritten to state the bridge
  "never triggers the B2B/paid-customer onboarding flow" and the fail-soft paragraph now references
  only `whatsapp_intake`.
- C3 (tests no longer test a removed function; still cover `set_contact_attributes` for new vs.
  returning leads): [x] — `TestTriggerOnboarding` class fully removed from `test_backend_client.py`;
  `test_process_message.py`'s `mocked_clients` fixture drops the `trigger_onboarding` patch/mock,
  and `test_new_lead_sets_contact_attributes_without_onboarding` /
  `test_returning_contact_does_not_set_contact_attributes` correctly assert `set_attrs` is
  called-once / not-called respectively.
- C4 (test run): [x] — re-ran `cd apps/chatwoot-bridge && python -m pytest tests -v` myself:
  **30 passed**, 1 pre-existing unrelated `python_multipart` deprecation warning, 4.76s. Matches
  the implementer's reported baseline (32 → 30, delta = the 2 deleted onboarding tests). No
  discrepancy.
- C5 (no scope creep — diff touches exactly the claimed files): [x] — `git diff --stat` against
  `apps/chatwoot-bridge` + `openspec/changes/chatwoot-hermes-taty-bridge` shows exactly:
  `backend_client.py`, `main.py`, `tests/test_backend_client.py`, `tests/test_process_message.py`,
  plus `design.md`/`spec.md`/`tasks.md` (pre-existing edits from the prior spec-correction session,
  not this implementer's work, per instructions). The separately-modified
  `openspec/changes/archive/2026-07-21-bunker-pwa-auth-enforcement/tasks.md` in `git status` is
  unrelated pre-existing working-tree state, outside this diff's path filter — confirmed not part
  of this task's change set.
- C6 (grep for remaining `trigger_onboarding`/`onboarding/start` references): [ ]  ← Reason:
  `apps/chatwoot-bridge/README.md:17,24-25,30` still describes the removed behavior as current:
  - line 17: `+--HTTP--> Contexia backend (CRM lead intake, onboarding)`
  - lines 24-25: `3. Background pipeline: CRM lead intake (find-or-create + onboarding trigger
    for new leads) -> ...`
  - line 30: `5. Any dependency failure (CRM, onboarding, Hermes) degrades gracefully — ...`

  This is stale documentation directly contradicting the corrected spec/design/code — exactly the
  class of drift the review instructions asked to grep for (item 6 explicitly names README.md as
  an example). `.env.example` is clean (no onboarding references). The only other hits for
  "onboarding" are in `backend_client.py` (now-correct docstring explaining it does NOT trigger
  onboarding) and `test_process_message.py` (docstring/comment correctly describing the new
  contract) — both fine.

## Required changes

1. Update `apps/chatwoot-bridge/README.md`:
   - Line 17: drop "onboarding" from the backend arrow annotation (or state explicitly CRM lead
     intake only, no onboarding).
   - Lines 24-25: remove "+ onboarding trigger for new leads" — replace with a description matching
     the corrected behavior (tag Chatwoot contact via `set_contact_attributes`, no onboarding call).
   - Line 30: drop "onboarding" from the dependency-failure list (or clarify it no longer applies
     since the bridge never calls the onboarding endpoint).
2. Re-grep `apps/chatwoot-bridge/` for `onboarding` after the README fix to confirm no other stale
   mentions remain, then re-submit for review.
