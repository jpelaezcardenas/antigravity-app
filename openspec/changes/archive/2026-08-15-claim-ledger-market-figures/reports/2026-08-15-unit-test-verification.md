# Unit Test Verification Report — claim-ledger-market-figures

- Date: 2026-08-15
- Change: claim-ledger-market-figures
- Agent: Claude Code (Sonnet)

## Commands Executed

- `python -m pytest tests/test_brand_rubric.py -v` (before implementation — 2/13 failed on the
  real Manus hook fixtures, confirming the false-positive)
- `python -m pytest tests/test_brand_rubric.py -v` (after implementation — 13/13 passed)
- `python -c "..."` — re-ran the 3 actual real Manus hooks from operator_task `ad6d3fcf…` through
  the full `evaluate_hook()` pipeline (not just `check_claims()` in isolation)
- `python -m pytest --ignore=tests/test_profile_support.py --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py -q`
  (full suite)

## Unit Test Results

- Targeted (`test_brand_rubric.py`): **13 passed** (7 pre-existing + 6 new)
- Full backend suite (940 collected, 3 pre-existing collection errors excluded): **821 passed, 39
  failed, 115 skipped**

## Baseline Comparison

`retention-loop`'s most recent run (2026-08-15): 815 passed, 39 failed, 115 skipped. This run: 821
passed (+6, this change's new coverage), **same 39 pre-existing failures**. No regressions.

## Design Adjustment Found During Implementation

The initial design (proximity-only citation, ~40 chars after each figure) failed on the real
Manus text: `"...movió $105,4 billones (+26,7% vs 2023, CCCE) y en el 2T2025 ya fueron $26,9
billones..."` — the source is cited once for the paragraph, not once per individual figure, so
the second `$26,9` figure has no nearby parenthetical of its own. Widened `_has_nearby_citation()`
to fall back to "recognized source name appears anywhere in the hook's full text" when no nearby
parenthetical is found. Documented in `design.md` Decision 2.

## Reproduction: Real Manus Hooks (Task 3)

**Before this fix**: 2 of 3 real hooks from `ad6d3fcf-7ff6-4dcd-9d06-26425bd61337` were rejected by
`check_claims()` for citing CCCE market figures ($105,4 billones, $191.850) with no path to pass.

**After this fix**, running the identical 3 hooks through the full `evaluate_hook()` pipeline
(Claim Ledger + hard-bans + LLM tone check):
```
Hook 1: approved=True
Hook 2: approved=True
Hook 3: approved=True
```
All 3 now pass end-to-end.

## Database

- Not applicable — pure logic change, no database touched.

## Outcome

- Status: **PASS**. False-positive fixed, regression-tested with real captured data, no
  regressions to existing fiscal-constant or hard-ban behavior.
