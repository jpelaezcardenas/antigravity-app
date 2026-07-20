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

- [x] 4.1 Committed (`c9841a6`), fast-forward merged to `main`, pushed.
- [x] 4.2 Railway deploy `a8d0a193` reached `SUCCESS`. No new flag — reuses
      `SELL_MACHINE_CANONICAL`.
- [x] 4.3 **Live smoke test**: created two real `approval_queue` rows (`status='approved'`,
      `draft_type='campaign_package'` — one with `budget_cents=500000`, one with `budget_cents:
      null`) via Supabase SQL, dispatched both via the real
      `POST /sell-machine/campaigns/{id}/dispatch` endpoint → `200`/`run_ads_ab` and
      `200`/`post_content` respectively, confirmed directly via Supabase SQL against the resulting
      `operator_tasks` rows. All test data cleaned up.
- [x] 4.4 Created deployment report at
      `openspec/changes/ads-ab-task-dispatch/reports/2026-07-20-deployment.md`, including the
      full session summary (all 6 gaps closed + 2 new bugs flagged).

## 5. Archive

- [x] 5.1 Synced the MODIFIED `hermes-manus-execution-bridge` delta into `openspec/specs/`
      (merged into the existing spec file), archived via `git mv` to
      `openspec/changes/archive/2026-07-20-ads-ab-task-dispatch/`.
