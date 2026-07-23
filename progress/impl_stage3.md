# Implementer report — Stage 3: liquidity bridge endpoint (TDD)

## Task in progress
`openspec/changes/pwa-tenant-aware-screens/tasks.md` Stage 3, items 3.1–3.3
(3.4 = the green-suite run below).

## Scope respected
Worktree: `antigravity-app-pwa-tenant-aware-screens`, branch
`feature/pwa-tenant-aware-screens`. Touched only:
- `apps/backend/services/financials_service.py`
- `apps/backend/presentation/financials_endpoints.py`
- `apps/backend/tests/test_financials_liquidity_bridge.py` (new)

Did **not** touch `apps/backend/presentation/centinela_endpoints.py` or
`apps/backend/tests/test_centinela_alerts_tenant_scoping.py` (both modified/created
concurrently by the Stage 2 agent in the same worktree) — confirmed via `git status`
before staging, and those files were excluded from `git add`/the commit. Did not modify
`core/tenant_context.py` (Stage 1, frozen) — only imported/called
`resolve_caller_tenant_id` from it, read-only.

## What was implemented

### `services/financials_service.py`
`compute_liquidity_bridge(tenant_id: str, year: int, month: int) -> dict`, placed above
`compute_pulso_daily_snapshot`:
- `initial_balance` = `_compute_caja_real_balance(supabase, tenant_id, month_start - 1 day)`
  — reused directly, no duplicated balance logic.
- A separate lightweight query (`erp_journal_lines` account 1110, `entry_date <= day_before_month`)
  determines `has_prior_lines`, used only for the `status` decision (see below) — kept
  separate from `_compute_caja_real_balance`'s sum so a tenant whose prior debits/credits
  happen to net to zero is still correctly reported `"ready"`, not `"empty"`.
- In-month query: same `erp_journal_entries!inner(entry_date)` join pattern used elsewhere
  in the file, filtered `account_code == "1110"` and `entry_date` in `[month_start, month_end]`.
  `inflows` = sum `debit_minor`, `outflows` = sum `credit_minor`.
- `final_balance = initial_balance + inflows - outflows`.
- `status`: `"empty"` only if there are zero 1110 lines at all for the tenant (no prior-period
  lines AND no in-month lines) — not simply "balance is zero" (a tenant with real but
  perfectly offsetting 1110 activity is still `"ready"`).
- Returns `{ initial_balance, inflows, outflows, final_balance, period: "YYYY-MM", status }`,
  all amounts in COP minor units (cents), matching the spec delta
  (`specs/pulso-financials-api/spec.md`, "Monthly liquidity bridge derived from Caja Real
  ledger").

### `presentation/financials_endpoints.py`
- Added `_empty_liquidity_bridge()` helper mirroring `_empty_snapshot()`'s non-leak contract.
- Added `GET /liquidity-bridge` (final path `/api/v1/financials/liquidity-bridge`, confirmed
  via `presentation/router.py`'s `prefix="/financials"` wiring), same router as `get_financials`.
  Depends on `get_current_user`; resolves tenant via
  `resolve_caller_tenant_id(user, cliente_cero_resolver=_resolve_cliente_cero_tenant_id)` — the
  same shared Stage 1 resolver and the same existing monkeypatchable Cliente Cero resolver
  `get_financials` already uses, so both endpoints stay policy-identical without duplicating
  Cliente Cero lookup logic. `None` tenant → `_empty_liquidity_bridge()`. Otherwise
  `compute_liquidity_bridge(tenant_id, today.year, today.month)`.

## TDD sequence

1. Wrote `tests/test_financials_liquidity_bridge.py` first (5 cases: bridge math with
   opening balance + in-month inflow/outflow; `final_balance` parity with
   `_compute_caja_real_balance` for month-end; empty tenant → zeroed `"empty"`; two-tenant
   isolation; month-boundary exclusion of prior/next-month movements from
   inflows/outflows). Reuses `insert_test_entry` imported from
   `tests.test_financials_aggregation` (not duplicated), hermetic throwaway tenants created/
   torn down per-test, same pattern as the existing suite.
2. Confirmed red: `ImportError: cannot import name 'compute_liquidity_bridge'` (5 failed).
3. Implemented the service function + endpoint.
4. Confirmed green.

## Test commands + output

```
cd apps/backend && python -m pytest tests/test_financials_liquidity_bridge.py tests/test_financials_aggregation.py tests/test_financials_endpoint_tenant_scoping.py -v
```

```
collected 20 items

tests/test_financials_liquidity_bridge.py::TestComputeLiquidityBridge::test_bridge_math_with_opening_balance_and_in_month_movements PASSED [  5%]
tests/test_financials_liquidity_bridge.py::TestComputeLiquidityBridge::test_final_balance_matches_equivalent_caja_real PASSED [ 10%]
tests/test_financials_liquidity_bridge.py::TestComputeLiquidityBridge::test_empty_tenant_returns_zeroed_empty_status PASSED [ 15%]
tests/test_financials_liquidity_bridge.py::TestComputeLiquidityBridge::test_tenant_isolation PASSED [ 20%]
tests/test_financials_liquidity_bridge.py::TestComputeLiquidityBridge::test_month_boundary_excludes_prior_and_next_month_movements PASSED [ 25%]
tests/test_financials_aggregation.py::TestFinancialsAggregation::test_caja_real_equals_bank_account_balance PASSED [ 30%]
tests/test_financials_aggregation.py::TestFinancialsAggregation::test_caja_real_includes_prior_period_balance PASSED [ 35%]
tests/test_financials_aggregation.py::TestFinancialsAggregation::test_ventas_periodo_sums_income_credits PASSED [ 40%]
tests/test_financials_aggregation.py::TestFinancialsAggregation::test_salidas_periodo_sums_expense_debits PASSED [ 45%]
tests/test_financials_aggregation.py::TestFinancialsAggregation::test_empty_ledger_returns_zeroes PASSED [ 50%]
tests/test_financials_aggregation.py::TestFinancialsAggregation::test_status_healthy_when_positive PASSED [ 55%]
tests/test_financials_aggregation.py::TestPulsoDailySnapshot::test_caja_real_is_cumulative_balance_as_of_date PASSED [ 60%]
tests/test_financials_aggregation.py::TestPulsoDailySnapshot::test_ventas_ayer_sums_only_yesterdays_income_credits PASSED [ 65%]
tests/test_financials_aggregation.py::TestPulsoDailySnapshot::test_gastos_ayer_sums_only_yesterdays_expense_debits PASSED [ 70%]
tests/test_financials_aggregation.py::TestPulsoDailySnapshot::test_daily_snapshot_empty_ledger_returns_zeroes PASSED [ 75%]
tests/test_financials_aggregation.py::TestPulsoDailySnapshot::test_daily_snapshot_status_healthy_when_positive PASSED [ 80%]
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_authenticated_caller_sees_own_tenant_snapshot PASSED [ 85%]
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_two_clients_see_different_non_leaking_snapshots PASSED [ 90%]
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_staging_identity_falls_back_to_cliente_cero PASSED [ 95%]
tests/test_financials_endpoint_tenant_scoping.py::TestFinancialsEndpointTenantScoping::test_authenticated_unresolved_tenant_returns_empty_not_cliente_cero PASSED [100%]

====================== 20 passed, 20 warnings in 57.32s =======================
```

`test_financials_aggregation.py` and `test_financials_endpoint_tenant_scoping.py` are
byte-for-byte unmodified (not staged/committed) and all 15 of their existing cases stayed
green, confirming this change didn't regress Stage 1's work or the existing aggregation logic.

`apps/backend/.env` already existed in this worktree (from Stage 1's setup) — no new
`.env` creation was needed.

## Commit
`3c809fb` — `feat(pwa-tenant-aware-screens): tenant-scoped GET /api/v1/financials/liquidity-bridge`
Files: `apps/backend/services/financials_service.py`,
`apps/backend/presentation/financials_endpoints.py`,
`apps/backend/tests/test_financials_liquidity_bridge.py` (new). No unrelated files staged —
verified `git status --short` before `git add`; `centinela_endpoints.py` and
`test_centinela_alerts_tenant_scoping.py` (Stage 2, another concurrent agent) left untouched
in the working tree.

## Not done (out of scope for this task)
- Stage 3.4's full report artifact is Stage 5's job per tasks.md structure; this report covers
  3.1–3.3's TDD execution and the green run requested.
- tasks.md checkboxes not marked — leader/reviewer to do after review, per harness protocol.
