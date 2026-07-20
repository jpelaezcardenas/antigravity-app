## 1. Setup + verification

- [x] 1.1 Created branch `feature/activate-telemetry-loop`.
- [x] 1.2 Re-confirmed `run_creative_loop`'s signature and `sell_machine_endpoints.py`'s current
      route list — no drift.

## 2. New endpoint — TDD

- [x] 2.1 Wrote failing tests for `POST /sell-machine/creative-loop/run`: returns `survivors`
      from `run_creative_loop(count, target_segment, use_telemetry=True)`; default `count` when
      omitted; `target_segment` passed through when provided. Confirmed failing.
- [x] 2.2 Implemented the endpoint in `sell_machine_endpoints.py`.
- [x] 2.3 Green (9/9).

## 3. Verify + DB state (MANDATORY before Stage 11)

- [x] 3.1 Ran the full targeted suite: 48/48 green across
      `test_sell_machine_endpoints.py`/`test_sell_machine_service.py`/`test_copywriter_service.py`/
      `test_content_evaluator.py`/`test_operator_task_service.py`, zero regression.
- [x] 3.2 Wrote `openspec/changes/activate-telemetry-loop/reports/2026-07-20-step3-verification.md`.

## 4. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 4.1 Commit + merge to `main` (check for divergence) + push.
- [ ] 4.2 Confirm Railway deploy green. No new flag — reuses `SELL_MACHINE_CANONICAL`.
- [ ] 4.3 Live smoke test: call the real `POST /api/v1/sell-machine/creative-loop/run` endpoint;
      confirm `200` and a non-empty `survivors` list; inspect Railway logs for evidence
      `get_telemetry_report`/`list_completed_tasks`/`get_funnel_snapshot` were actually invoked
      (confirming the telemetry branch executed, not the generic one).
- [ ] 4.4 Create deployment report at
      `openspec/changes/activate-telemetry-loop/reports/YYYY-MM-DD-deployment.md`.

## 5. Archive

- [ ] 5.1 Sync the ADDED `sell-machine-telemetry-loop` requirement into `openspec/specs/` (append
      to the existing spec file), archive via `git mv` once Stage 11 is confirmed complete.
