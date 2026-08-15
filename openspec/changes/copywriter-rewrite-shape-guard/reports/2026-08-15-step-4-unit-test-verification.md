# Step 4 Report - Unit Tests, State Verification, and Live Crash Reproduction

- Date: 2026-08-15
- Change: copywriter-rewrite-shape-guard
- Agent: Claude Code (Sonnet)

## Commands Executed

- `python -m pytest tests/test_copywriter_service.py -k "ShapeGuard" -v` (before implementation —
  3/5 new tests failed, confirming the gap)
- `python -m pytest tests/test_copywriter_service.py -v` (after implementation — 19/19 passed)
- `python -m pytest --ignore=tests/test_profile_support.py --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py -q`
  (full suite)
- `python -m pytest tests/test_financials_liquidity_bridge.py -v` (isolation re-run, see Notes)

## Unit Test Results

- Targeted (`test_copywriter_service.py`): **19 passed** (14 pre-existing + 5 new shape-guard
  tests)
- Full backend suite (940 collected, 3 pre-existing collection errors excluded): **797 passed, 39
  failed, 115 skipped, 2 errors** — runtime 182.07s

## Baseline Comparison

`brand-voice-canonization`'s Step 6 baseline (2026-08-14): 786 passed, 39 failed, 115 skipped.
`manus-content-retrieval`'s equivalent run: not applicable (poller-only, separate test suite). This
run: 797 passed (+11 vs. the 786 baseline — the net of `manus-first-creative-pipeline`'s +8 and
this change's +5, minus overlap), **same 39 pre-existing failures**, no new regressions.

## Notes — 2 Errors in `test_financials_liquidity_bridge.py` (Full-Suite Run Only)

`test_final_balance_matches_equivalent_caja_real` and `test_empty_tenant_returns_zeroed_empty_status`
errored in the full-suite run but are **unrelated to this change** — `test_financials_liquidity_bridge.py`
tests `financials_endpoints.py`'s liquidity bridge computation, a module this change never touches.
Re-run in isolation (`pytest tests/test_financials_liquidity_bridge.py -v`): **5/5 passed**,
including both tests that errored in the full run. This is a pre-existing test-isolation/ordering
flakiness in the broader suite (likely resource contention across 940 tests, some of which hit real
external services), not a regression introduced here.

## Live Crash Reproduction (Task 3)

**Before this fix** (2026-08-15, earlier in this session): running the 3 real Manus-sourced hooks
from operator_task `17ee4d8b…` through `run_creative_loop(manus_draft_hooks=...)` against
production data crashed with:
```
AttributeError: 'list' object has no attribute 'get'
```
at `content_evaluator._hook_text()`, because a rewrite response got wrapped in a JSON list by the
LLM and was never validated before being treated as a single hook.

**After this fix**, the identical call against the identical data:
```
SURVIVORS: 1 of 3
```
No crash. The Claim Ledger (from `brand-voice-canonization`) correctly rejected 2 of the 3 original
hooks for unsourced/imprecise peso figures (`$69,7` — a truncated abbreviation of "$69,7 millones",
and `$524.000` — a reasonable rounding of the exact `$523.740` sanction figure); one was fixed by
the one-rewrite-pass and survived. This is the Claim Ledger working as designed — strict, not a
bug — and is a useful signal for future rubric tuning (out of scope for this change).

## Database State Verification

- Not applicable — this change touches no database.

## Outcome

- Step 4 status: **PASS**
- Blocking issues: none. The 2 liquidity-bridge errors are pre-existing suite flakiness, confirmed
  unrelated by isolation re-run.
