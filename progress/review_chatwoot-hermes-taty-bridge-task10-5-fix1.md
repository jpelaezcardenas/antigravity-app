# Review — task chatwoot-hermes-taty-bridge-10.5 (fix round 1: README)

**Verdict:** APPROVED

## Summary

The single blocking finding from the prior review (`progress/review_chatwoot-hermes-taty-bridge-task10-5.md`)
— stale onboarding-trigger claims in `apps/chatwoot-bridge/README.md` (lines 17, 24-25, 30) — is fully
resolved. The leader's direct README edit is scoped correctly: no other file was touched in this fix
round, and the rest of the (already-reviewed, still-uncommitted) task 10.5 code/tests are untouched.

## Checkpoints

- C1 (README no longer claims onboarding-triggering is current behavior): [x] — read the full file.
  Line 17 arrow annotation now reads "CRM lead intake" only (onboarding dropped). Step 3 now describes
  only `set_contact_attributes` tagging (`tipo_lead`/`estado: "nuevo"`) for new leads, explicitly notes
  "no company onboarding is triggered here, see design.md decision 5". Step 5's degrades-gracefully list
  drops "onboarding" from the dependency list (now just "CRM, Hermes"). A new troubleshooting bullet
  ("New leads aren't getting a company/workspace onboarded automatically") explicitly frames the absence
  as intentional design (decision 5), not a bug. Accurately reflects the corrected code/spec.
- C2 (grep entire `apps/chatwoot-bridge/` for `trigger_onboarding`/`onboarding/start`, any file type):
  [x] — only hit is `apps/chatwoot-bridge/.pytest_cache/v/cache/nodeids`, an auto-generated pytest
  cache artifact storing the *old test name* `test_returning_contact_does_not_trigger_onboarding` from
  a prior test run — not source, not committed, regenerated on every `pytest` invocation, harmless.
  No source, doc, config, or `.env.example` reference remains.
- C3 (code/tests unchanged, still 30 passing): [x] — re-ran
  `cd apps/chatwoot-bridge && python -m pytest tests -v` myself: **30 passed**, 1 pre-existing unrelated
  `python_multipart` deprecation warning, 3.26s. Identical pass list to the prior review's C4.
- C4 (no other file touched beyond README.md in this follow-up): [x] — `git diff --stat -- apps/chatwoot-bridge`
  shows `README.md`, `backend_client.py`, `main.py`, `tests/test_backend_client.py`,
  `tests/test_process_message.py` — the latter four are byte-identical to what was already reviewed and
  approved-pending-README in the prior round (verified against `progress/impl_chatwoot-hermes-taty-bridge-task10-5.md`'s
  documented diff). Only `README.md`'s diff is new in this round.

## Docs-sync

No architecture container/dependency changed in this fix round (doc-only correction of already-corrected
behavior) — `ARCHITECTURE.md` update not applicable.

## Required changes

None.
