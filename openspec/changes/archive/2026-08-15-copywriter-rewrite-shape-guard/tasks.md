## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/copywriter-rewrite-shape-guard` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Failing Tests First (TDD)

- [x] 1.1 Add failing tests to `apps/backend/tests/test_copywriter_service.py`'s `TestRewriteHook`:
      `_llm_rewrite_hook` mocked to return a 1-element list with a well-shaped hook → `rewrite_hook`
      returns that element; mocked to return an empty list → returns the original hook; mocked to
      return a list whose first element is missing required keys → returns the original hook;
      mocked to return a dict missing `headline`/`body`/`cta` → returns the original hook
- [x] 1.2 Run and confirm they fail (no shape validation exists yet — the malformed values would
      currently be returned as-is)

## 2. Implementation

- [x] 2.1 Implement the shape guard in `rewrite_hook()`: validate `rewritten` is a well-shaped
      single hook dict; if it's a list, take the first well-shaped element or fall back; if it's a
      dict missing required keys, fall back
- [x] 2.2 Run and confirm the new tests pass, plus the full existing `TestRewriteHook` class (no
      regression to the happy-path or LLM-unavailable-exception paths)

## 3. Reproduce and Confirm the Original Crash Is Fixed

- [x] 3.1 Re-run the exact scenario that crashed live (2026-08-15): the 3 real Manus-sourced hooks
      from operator_task `17ee4d8b…` through `run_creative_loop(manus_draft_hooks=...)` locally
      against production data — confirm it completes without crashing and returns a survivors list
      (even if 0 survivors, that's a valid evaluation outcome — no crash is the bar)
- [x] 3.2 Document the before/after (crash → clean completion) in the Step 4 report

## 4. Run Unit Tests and Verify State (MANDATORY)

- [x] 4.1 Run the full `apps/backend` test suite (excluding the 3 known pre-existing
      collection-broken files) and confirm no new regressions vs. the `brand-voice-canonization`
      Step 6 baseline (786 passed / 39 failed / 115 skipped)
- [x] 4.2 This change touches no database — no migration, no DB state capture/restore needed
- [x] 4.3 Create report
      `openspec/changes/copywriter-rewrite-shape-guard/reports/YYYY-MM-DD-step-4-unit-test-verification.md`,
      including the 3.1 reproduction result
- [x] 4.4 Mark this section complete only after the report exists and tests are green

## 5. Not Applicable: Manual Endpoint / E2E Testing

- [x] 5.1 Confirm and document in the report (4.3) that this change adds no new/modified HTTP
      endpoint and no frontend-facing behavior.

## 6. OpenSpec: Sync Spec + Documentation

- [x] 6.1 Confirm the delta spec matches the implemented behavior
- [x] 6.2 Grep for other references to `rewrite_hook`'s exact contract — update only if found

## 7. Deploy to Production (MANDATORY — CLOSES THE LOOP, Stage 11)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 7.1 Commit + merge `feature/copywriter-rewrite-shape-guard` into `main` + push
- [x] 7.2 Railway deploy active — confirm `SUCCESS` via Railway MCP
- [x] 7.3 Verify in production: same auth-boundary substitution as prior changes this session
      (clean response from an existing sell-machine endpoint + Railway logs showing no crash) —
      document in the report
- [x] 7.4 Create deployment report:
      `openspec/changes/copywriter-rewrite-shape-guard/reports/YYYY-MM-DD-deployment.md`

## 8. Archive

- [x] 8.1 Run `openspec-sync-specs` to merge the delta spec into
      `openspec/specs/sell-machine-creative-swarm/spec.md`
- [x] 8.2 Archive this change once Stage 11 is verified and all tasks above are checked
