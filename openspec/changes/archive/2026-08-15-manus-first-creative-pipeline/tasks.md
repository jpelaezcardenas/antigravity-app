## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/manus-first-creative-pipeline` from `main`
- [x] 0.2 Verify branch creation and current branch status

## 1. Backend: get_latest_manus_draft() — Failing Tests First (TDD)

- [x] 1.1 Added failing tests to `apps/backend/tests/test_sell_machine_service.py` (already
      existed): `get_latest_manus_draft()` returns `None` on empty completed-task list, `None` on
      malformed/missing `hooks` key, `None` on non-dict/missing-required-keys hook items, and the
      hook list on a well-shaped result — plus 3 tests for the `manus_draft_hooks` branch of
      `run_creative_loop()`
- [x] 1.2 Ran the new tests and confirmed they fail: `ImportError: cannot import name
      'get_latest_manus_draft' from 'services.sell_machine_service'`

## 2. Backend: get_latest_manus_draft() — Implementation

- [x] 2.1 Implemented `get_latest_manus_draft()` in `sell_machine_service.py`: calls
      `list_completed_tasks(task_type="research")`, takes the most recent by `created_at`,
      defensively extracts and validates `result["hooks"]` (list of dicts with
      headline/body/cta keys), returns `None` on any mismatch
- [x] 2.2 Ran the tests and confirmed they pass

## 3. Backend: run_creative_loop() — Manus Draft Branch (TDD)

- [x] 3.1 Added failing tests (see 1.1)
- [x] 3.2 Implemented `manus_draft_hooks: Optional[List[Dict[str, Any]]] = None` and the
      skip-generation branch in `run_creative_loop()`
- [x] 3.3 Ran the tests and confirmed they pass — 18/18 in `test_sell_machine_service.py`

## 4. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 4.1 Confirmed via grep: the only caller of `run_creative_loop()` outside tests is
      `presentation/sell_machine_endpoints.py`, which does not pass `manus_draft_hooks` —
      unaffected
- [x] 4.2 Confirmed: Approval Queue, `create_campaign_package`, and the poller all consume
      survivor hooks by shape only, identically regardless of origin — no changes needed

## 5. Backend: Run Unit Tests and Verify State (MANDATORY)

- [x] 5.1 Captured baseline from `brand-voice-canonization`'s Step 6 report (same exclusion set):
      786 passed, 39 failed, 115 skipped
- [x] 5.2 Ran targeted tests: `test_sell_machine_service.py` — 18/18 passed
- [x] 5.3 Ran the full suite: 794 passed (+8, this change's new coverage), same 39 pre-existing
      failures, no regressions
- [x] 5.4 No database touched — noted in the report
- [x] 5.5 Report created:
      `openspec/changes/manus-first-creative-pipeline/reports/2026-08-15-step-5-unit-test-verification.md`
- [x] 5.6 Section complete — report exists, this change's tests are green

## 6. Not Applicable: Manual Endpoint / E2E Testing

- [x] 6.1 Confirmed and documented in the Step 5 report: no new/modified HTTP endpoint, no
      frontend-facing behavior.

## 7. OpenSpec: Sync Spec + Documentation

- [x] 7.1 Confirmed the delta spec matches the implemented behavior (both ADDED requirements map
      1:1 to the implemented functions/branches)
- [x] 7.2 Searched `AGENTES.md`/`ARCHITECTURE.md` for `run_creative_loop`/`get_latest_manus_draft`
      references — none found, nothing to update

## 8. Deploy to Production (MANDATORY — CLOSES THE LOOP, Stage 11)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 8.1 Committed (`189c183`) + fast-forward merged into `main` + pushed (`5de7789..189c183`)
- [x] 8.2 Railway deploy `b66c0081-490a-4ba0-8433-82704b103310` confirmed `SUCCESS` via Railway MCP
- [x] 8.3 Verified: `GET /sell-machine/tasks/pending` (imports the modified module) returns clean
      200s post-deploy, Manus↔poller loop unaffected. Full functional exercise of a real Manus
      `research` result awaits a founder-run Manus task — see `reports/2026-08-15-deployment.md`
- [x] 8.4 Deployment report created:
      `openspec/changes/manus-first-creative-pipeline/reports/2026-08-15-deployment.md`

## 9. Archive

- [x] 9.1 Ran `openspec-sync-specs`: merged the 2 ADDED requirements into
      `openspec/specs/sell-machine-creative-swarm/spec.md`
- [x] 9.2 Archiving this change now that Stage 11 is verified and all tasks above are checked
