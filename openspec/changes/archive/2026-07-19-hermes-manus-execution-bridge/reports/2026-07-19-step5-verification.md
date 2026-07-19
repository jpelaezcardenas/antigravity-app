# Verification report — hermes-manus-execution-bridge (Section 5)

Date: 2026-07-19

## 5.1 — Test suites

Backend: `pytest tests/test_operator_task_service.py tests/test_operator_task_endpoints.py
tests/test_sell_machine_service.py tests/test_sell_machine_endpoints.py
tests/test_content_evaluator.py tests/test_copywriter_service.py
tests/test_crm_service_grid_logic.py tests/test_crm_endpoints.py
tests/test_crm_service_b2c_logic.py tests/test_crm_b2c_endpoints.py` — **72/72 passed**
(11 new service tests + 11 new endpoint tests + 50 pre-existing Sell Machine/CRM tests re-run
alongside, zero regression despite `presentation/sell_machine_endpoints.py` being a shared file).

This change touches no `contexia-app/` files (confirmed via `git status --short` before this
report) — no `tsc`/build/sw.js-bump step applies to Stage 11 for this change.

## 5.2 — DB state (direct Supabase verification, pre-deploy)

Since the migration was already applied directly to the (single, shared) production Supabase
project, this step verifies the table/constraints/dispatch logic at the DB layer directly via SQL
— ahead of the code being deployed. The actual live-API smoke test happens in Stage 11 (6.5) once
the endpoints are reachable.

- Inserted one row for each read-only `task_type` (`research`, `metrics_pull`,
  `external_integration`, `generate_doc`) directly: all 4 landed with `status='pending'` as
  expected.
- Simulated the campaign-package dispatch: read the real approved `campaign_package` decision from
  Change E's own Stage 11 smoke test (`7b4439c3-ba70-4490-bd0b-3fcd412aac20`, confirmed still
  `status='approved'` in production), inserted a `post_content` operator task whose `payload`
  correctly carries `source_decision_id` pointing back to that decision.
- All 5 verification rows were deleted afterward — they were direct-SQL simulations of what the
  service will do, not artifacts of the real code path (which isn't deployed yet).

## 5.3 — This report

Written per Section 5, task 5.3.

## Summary

All verifiable-now checks pass: 72/72 tests, and the `operator_tasks` table/constraints/dispatch
shape behave correctly under direct SQL simulation. The live full-loop walkthrough via the actual
deployed endpoints (create a read-only task, mark dispatched, report a result, dispatch the real
approved campaign package) is deferred to Stage 11 (6.5), where the new routes become reachable.
