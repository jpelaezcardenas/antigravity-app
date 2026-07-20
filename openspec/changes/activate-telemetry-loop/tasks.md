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

- [x] 4.1 Committed (`afd0bd2`), fast-forward merged to `main`, pushed.
- [x] 4.2 Railway deploy `26464f67` reached `SUCCESS`. No new flag — reuses
      `SELL_MACHINE_CANONICAL`.
- [x] 4.3 **Live smoke test**: `POST /sell-machine/creative-loop/run` → `200`, non-empty
      `survivors`, correct shape. Railway logs confirm the telemetry branch executed for real
      (`list_completed_tasks` ×2 + `get_funnel_snapshot`'s underlying queries all fired). Also
      reconfirmed the `llm_engine.py` bug flagged in `copywriter-rag`, now seen affecting
      `content_evaluator.py` too — both degraded gracefully, no crash.
- [x] 4.4 Created deployment report at
      `openspec/changes/activate-telemetry-loop/reports/2026-07-20-deployment.md`.

## 5. Archive

- [x] 5.1 Synced the ADDED `sell-machine-telemetry-loop` requirement into `openspec/specs/`
      (appended to the existing spec file), archived via `git mv` to
      `openspec/changes/archive/2026-07-20-activate-telemetry-loop/`.
