## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/claim-ledger-market-figures` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Failing Tests First (TDD)

- [x] 1.1 Add failing tests to `test_brand_rubric.py` using the exact real Manus hook text
      (`"...$105,4 billones (+26,7% vs 2023, CCCE)..."`, `"...$191.850 (−7,6% anual, CCCE)..."`)
      as regression fixtures — both currently rejected, both should be accepted after this change
- [x] 1.2 Add tests for: a recognized-source citation with no `%`/year (bare `(DANE)`) still
      passes; a peso figure with a parenthetical NOT naming a recognized source still fails; a
      peso figure with no parenthetical at all still fails (unchanged existing behavior); a known
      fiscal constant still passes unconditionally (no citation needed, unchanged)
- [x] 1.3 Run and confirm the new sourced-market-figure tests fail (feature doesn't exist yet) and
      the unchanged-behavior tests already pass (confirms no regression risk)

## 2. Implementation

- [x] 2.1 Add `_RECOGNIZED_MARKET_SOURCES` allowlist (CCCE, DANE, Cámara de Comercio Aburrá Sur,
      Colombia Fintech, MinTIC, Superintendencia de Sociedades) to `brand_rubric.py`
- [x] 2.2 Implement proximity-based citation detection: after a peso/UVT figure fails the
      known-constant check, look for a recognized source name in a nearby parenthetical before
      rejecting
- [x] 2.3 Run and confirm all new tests pass, plus the full existing `test_brand_rubric.py` suite
      (no regression to hard-bans or the existing fiscal-constant path)

## 3. Reproduce and Confirm the Original False-Positive Is Fixed

- [x] 3.1 Re-run the exact 3 real Manus hooks from operator_task `ad6d3fcf…` through
      `evaluate_hook()` — confirm hooks 1 and 2 (previously rejected for the CCCE figures) now
      pass the Claim Ledger check
- [x] 3.2 Document the before/after in the Step 4 report

## 4. Run Unit Tests and Verify State (MANDATORY)

- [x] 4.1 Run the full `apps/backend` test suite (excluding the 3 known pre-existing
      collection-broken files) and confirm no new regressions vs. the most recent baseline
- [x] 4.2 No database touched — noted, no migration/DB verification needed
- [x] 4.3 Create report
      `openspec/changes/claim-ledger-market-figures/reports/YYYY-MM-DD-unit-test-verification.md`
- [x] 4.4 Mark complete only after report exists and tests are green

## 5. Not Applicable: Manual Endpoint / E2E Testing

- [x] 5.1 Confirm and document that this change adds no new/modified HTTP endpoint and no
      frontend-facing behavior — pure logic change inside an existing evaluation path

## 6. OpenSpec: Sync Spec + Documentation

- [x] 6.1 Confirm the delta spec matches the implemented behavior
- [x] 6.2 Grep for other references to the Claim Ledger's allowlist shape — update only if found

## 7. Deploy to Production (MANDATORY — CLOSES THE LOOP, Stage 11)

Project-specific details:
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 7.1 Commit + merge `feature/claim-ledger-market-figures` into `main` + push
- [x] 7.2 Railway deploy active — confirm `SUCCESS` via Railway MCP
- [x] 7.3 Verify in production: same auth-boundary substitution as prior changes this session
- [x] 7.4 Create deployment report:
      `openspec/changes/claim-ledger-market-figures/reports/YYYY-MM-DD-deployment.md`

## 8. Archive

- [x] 8.1 Run `openspec-sync-specs` to merge the delta spec into
      `openspec/specs/sell-machine-creative-swarm/spec.md`
- [x] 8.2 Archive this change once Stage 11 is verified and all tasks above are checked
