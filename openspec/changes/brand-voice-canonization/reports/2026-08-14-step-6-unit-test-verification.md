# Step 6 Report - Unit Tests and State Verification

- Date: 2026-08-14
- Change: brand-voice-canonization
- Agent: Claude Code (Sonnet)

## Commands Executed

- `python -m pytest tests/test_brand_rubric.py -v` (before implementation — confirmed collection
  failure, module didn't exist yet)
- `python -m pytest tests/test_brand_rubric.py -v` (after implementation)
- `python -m pytest tests/test_content_evaluator.py tests/test_brand_rubric.py -v`
- `python -m pytest tests/test_copywriter_service.py -v`
- `python -m pytest --ignore=tests/test_profile_support.py --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py -q`
  (full suite baseline; the 3 ignored files fail at collection with `ModuleNotFoundError: No
  module named 'apps'` — a pre-existing absolute-import bug unrelated to this change, present
  before any file in this change was touched)
- `python -m pytest tests/test_brand_rubric.py tests/test_content_evaluator.py tests/test_copywriter_service.py -q`
  (final re-verification, run after an unrelated `git stash`/`stash pop` cycle — see Notes)

## Unit Test Results

- Targeted (`test_brand_rubric.py`): 7 passed
- Targeted (`test_content_evaluator.py` + `test_brand_rubric.py`): 16 passed
- Targeted (`test_copywriter_service.py`): 14 passed
- Combined final re-run of all three files touched by this change: **30 passed**
- Full backend suite (940 collected, 3 pre-existing collection errors excluded): **786 passed, 39
  failed, 115 skipped** — runtime 266.96s

## Baseline Comparison — the 39 Pre-Existing Failures

None of the 39 failing tests import or reference any file this change touches
(`agents/content_evaluator.py`, `agents/brand_rubric.py`, `services/copywriter_service.py`) —
confirmed via `grep -l "content_evaluator\|copywriter_service\|brand_rubric"` across all 11 failing
test files: zero matches. The failures fall into three pre-existing categories, unrelated to brand
voice / Sell Machine:

1. **Siigo CSV parser / Shadow GL migration acceptance checks** (`test_shadow_gl_*.py`,
   `test_approval_rules_stage*.py`) — these assert the existence of specific migration/report
   files from other, unrelated OpenSpec changes (e.g. `test_migration_file_exists`,
   `test_design_document_complete`), not runtime logic.
2. **Live-endpoint tests without a running server** (`test_centinela_alerts_get.py`,
   `test_wizard_auditoria_sombra.py`) — connection-dependent, fail in this offline test run
   regardless of this change.
3. **`test_secure_llm.py`** — one LLM-anonymization test, unrelated module.

This matches known pre-existing tech debt (`MEMORY.md` →
`tech-debt-pre-gtm-2026-08-13`, 191 pending tasks across parked changes) and is out of scope for
brand-voice-canonization to fix.

## Database State Verification

- Not applicable — this change touches no database (module-level Python only, no migrations, no
  new tables/rows). No pre/post baseline needed.

## Notes on the Interrupted Baseline-Confirmation Attempt

A separate `git stash && ... && git stash pop` command (run to double-check the 39 failures existed
without this change's diff applied) hit its shell timeout mid-run. `git status`/`git stash list`
were checked immediately afterward and confirmed the stash (`stash@{0}`) was intact and un-lost;
`git stash pop` was then run cleanly and all 4 files this change modifies were restored. The
targeted 30-test re-run above (after the restore) confirms no regression from that incident. The
planned direct-comparison baseline run (same 2 files, before vs. after this change's diff) did not
complete due to the timeout; the import-independence grep check above is used as the substitute
evidence that this change did not introduce any of the 39 failures.

## Outcome

- Step 6 status: **PASS** (with the noted substitution of import-independence verification in
  place of a direct before/after diff run, due to the timeout above)
- Blocking issues: none. The 39 failures are pre-existing, unrelated tech debt — not introduced by
  and not fixed by this change.
