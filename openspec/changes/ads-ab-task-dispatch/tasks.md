## 1. Setup + verification

- [x] 1.1 Created branch `feature/ads-ab-task-dispatch`.
- [x] 1.2 Re-confirmed `dispatch_campaign_package`'s current body and `SIDE_EFFECTING_TASK_TYPES`
      — no drift.

## 2. Task-type inference — TDD

- [x] 2.1 Wrote failing tests for the extended `dispatch_campaign_package`: `budget_cents=None`
      dispatches `post_content` (unchanged); a positive `budget_cents` dispatches `run_ads_ab`;
      `budget_cents=0` dispatches `post_content`; non-approved rejection path unaffected.
      Confirmed failing.
- [x] 2.2 Implemented the inference in `dispatch_campaign_package`.
- [x] 2.3 13/13 green in `test_operator_task_service.py` (2 new + 11 pre-existing), zero
      regression.

## 3. Verify + DB state (MANDATORY before Stage 11)

- [x] 3.1 Ran the full targeted suite: 31/31 green across
      `test_operator_task_service.py`/`test_sell_machine_service.py`/
      `test_sell_machine_endpoints.py`, zero regression.
- [x] 3.2 Wrote `openspec/changes/ads-ab-task-dispatch/reports/2026-07-20-step3-verification.md`.

## 4. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 4.1 Commit + merge to `main` (check for divergence) + push.
- [ ] 4.2 Confirm Railway deploy green. No new flag — reuses `SELL_MACHINE_CANONICAL`.
- [ ] 4.3 Live smoke test: create two real approved `campaign_package` Approval Queue drafts (one
      with `budget_cents` set, one without) via direct Supabase SQL/API, call the real
      `POST /sell-machine/campaigns/{id}/dispatch` for each, confirm via Supabase SQL that the
      resulting `operator_tasks.task_type` is `run_ads_ab` and `post_content` respectively. Clean
      up test data.
- [ ] 4.4 Create deployment report at
      `openspec/changes/ads-ab-task-dispatch/reports/YYYY-MM-DD-deployment.md`.

## 5. Archive

- [ ] 5.1 Sync the MODIFIED `hermes-manus-execution-bridge` delta into `openspec/specs/` (merge
      into the existing spec file), archive via `git mv` once Stage 11 is confirmed complete.
