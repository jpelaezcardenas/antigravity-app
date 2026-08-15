## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/brand-voice-canonization` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Backend: brand_rubric.py — Failing Tests First (TDD)

- [x] 1.1 Create `apps/backend/tests/test_brand_rubric.py` (flat `tests/` dir, matching this
      repo's actual convention — not `tests/agents/`, which doesn't exist) with failing tests:
      each of the 5 hard-ban phrases is exported and matches; Claim Ledger accepts a peso figure
      correctly derived from `core.constants.UVT_2026`; Claim Ledger rejects an unrecognized
      peso/UVT figure (e.g. the known-wrong `$471.000`); a hook with no peso/UVT tokens is
      unaffected by the Claim Ledger
- [x] 1.2 Run the new test file and confirm all new tests fail (module doesn't exist yet) —
      confirmed: `ModuleNotFoundError: No module named 'agents.brand_rubric'`

## 2. Backend: brand_rubric.py — Implementation

- [x] 2.1 Create `apps/backend/agents/brand_rubric.py`: move `BRAND_RUBRIC_SYSTEM_PROMPT` and
      hard-ban phrases (exported as `HARD_BAN_PHRASES`, re-exported as `_HARD_BAN_PHRASES` in
      `content_evaluator.py` for backward compat) from `content_evaluator.py`, import
      `UVT_2025`/`UVT_2026` and thresholds from `core.constants`
- [x] 2.2 Implement the Claim Ledger: known-value allowlist derived from imported constants (raw
      UVT values + 10x multiples), regex-extract `$<digits>` and `<digits> UVT` patterns, and
      `check_claims(hook) -> str | None`
- [x] 2.3 Run `pytest apps/backend/tests/test_brand_rubric.py` and confirm all tests now pass —
      7/7 passed (one test-authoring bug found and fixed along the way, not a code bug — see
      commit)

## 3. Backend: content_evaluator.py — Wire In the Rubric Module

- [x] 3.1 Update `content_evaluator.py` to import `BRAND_RUBRIC_SYSTEM_PROMPT`, `HARD_BAN_PHRASES`,
      and `check_claims` from `brand_rubric.py`; updated module docstring to point at the new file
- [x] 3.2 Add a Claim Ledger check to `evaluate_hook()`, in the same non-overridable position as
      the existing hard-ban check (before the LLM tone check, never subject to its fail-open
      fallback)
- [x] 3.3 Add/update tests in the existing content_evaluator test file: `TestClaimLedgerGate` (3
      tests) — unsourced figure rejected even if LLM would approve, rejected even if LLM fails,
      correctly-sourced figure unaffected
- [x] 3.4 Run the updated test file and confirm all pass — 16/16 passed (9 pre-existing + 7 new
      via brand_rubric.py)

## 4. Backend: copywriter_service.py — Fix Voseo/Tuteo + Shared Rubric Source

- [x] 4.1 Fixed the fallback hook CTA text: "Habla con Taty y salé de dudas" → "Habla con Taty y
      sal de dudas"
- [x] 4.2 Re-pointed `_SYSTEM_PROMPT` to embed `BRAND_RUBRIC_SYSTEM_PROMPT` from `brand_rubric.py`
      (imported, not duplicated) alongside its own generation-specific instructions
- [x] 4.3 Added `TestFallbackHooksAreTuteoConsistent` asserting no voseo marker appears in any
      fallback hook's text
- [x] 4.4 Run the updated test file and confirm all pass — 14/14 passed

## 5. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 5.1 Searched for any other reference to `content_evaluator.BRAND_RUBRIC_SYSTEM_PROMPT` /
      `content_evaluator._HARD_BAN_PHRASES` — none found outside content_evaluator.py itself
- [x] 5.2 Confirmed via grep across `apps/backend` that no other module duplicates the hard-ban
      list or fiscal constants independently — `brand_rubric.py` is the single source

## 6. Backend: Run Unit Tests and Verify State (MANDATORY)

- [x] 6.1 Captured baseline: full suite (940 collected, 3 pre-existing collection errors excluded)
      → 786 passed, 39 failed, 115 skipped
- [x] 6.2 Ran targeted tests: `test_brand_rubric.py` (7), `test_content_evaluator.py` (16 combined
      w/ brand_rubric), `test_copywriter_service.py` (14) — all passed
- [x] 6.3 Ran the full suite and confirmed the 39 failures are pre-existing, unrelated tech debt
      (confirmed via import-independence grep — see report) — no regressions from this change
- [x] 6.4 No database touched by this change — noted in the report, no capture/restore needed
- [x] 6.5 Report created:
      `openspec/changes/brand-voice-canonization/reports/2026-08-14-step-6-unit-test-verification.md`
- [x] 6.6 Section complete — report exists, all 30 tests in this change's scope are green

## 7. Not Applicable: Manual Endpoint / E2E Testing

- [x] 7.1 Confirmed and documented in the Step 6 report: this change adds no new/modified HTTP
      endpoint and no frontend-facing behavior. `POST /api/v1/sell-machine/hooks/evaluate`'s
      contract is unchanged; only its internal rejection logic gains a new deterministic gate,
      already covered by unit tests 3.3/3.4.

## 8. OpenSpec: Sync Spec + Documentation

- [x] 8.1 Confirmed the delta spec at `specs/sell-machine-creative-swarm/spec.md` in this change
      accurately reflects the implemented behavior (Claim Ledger scenarios match `check_claims`)
- [x] 8.2 Searched `AGENTES.md`/`ARCHITECTURE.md` for references to the old inline rubric location
      or `content_ops_rules.md` — no matches, nothing to update

## 9. Deploy to Production (MANDATORY — CLOSES THE LOOP, Stage 11)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 9.1 Committed (`867b144`) + fast-forward merged `feature/brand-voice-canonization` into
      `main` + pushed to `origin/main` (`2cd52a9..867b144`)
- [x] 9.2 Railway deploy `21b80fdb-f1d2-4e14-8600-d5cc11c57187` confirmed `SUCCESS` via Railway MCP
- [x] 9.3 Live verification: `POST /hooks/evaluate` requires `Depends(get_current_user)` (real
      Supabase auth), which the agent must never obtain/hold per this session's safety rules —
      substituted with: (a) unauthenticated curl returned a clean `401`, not a 500/crash, proving
      the deployed `brand_rubric.py` import graph resolved correctly; (b) Railway runtime logs
      confirm the deploy is serving traffic normally; (c) the exact `$471.000` regression case is
      covered by the 30 passing unit tests against the same deployed module. See
      `reports/2026-08-15-deployment.md` for full detail
- [x] 9.4 Deployment report created:
      `openspec/changes/brand-voice-canonization/reports/2026-08-15-deployment.md`

## 10. Archive

- [x] 10.1 Ran `openspec-sync-specs`: merged the MODIFIED requirement (Claim Ledger scenarios) into
      `openspec/specs/sell-machine-creative-swarm/spec.md`
- [x] 10.2 Archiving this change now that Stage 11 is verified and all tasks above are checked
