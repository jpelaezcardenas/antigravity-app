# Step 3 verification — ads-ab-task-dispatch

Date: 2026-07-20

## Test results

Full targeted suite, 31/31 green, zero regression:

```
tests/test_operator_task_service.py ............. (13, incl. 2 new)
tests/test_sell_machine_service.py
tests/test_sell_machine_endpoints.py
```

## Scope of the change

`services/operator_task_service.py`: `dispatch_campaign_package` now infers `task_type` from the
approved package's own `budget_cents` field — `run_ads_ab` when truthy, `post_content` (unchanged
default) otherwise. No new field, no new endpoint parameter — reuses data already present on every
`campaign_package` draft.

## No migration, no new endpoint

Pure logic change to one existing function.
