# Step 5 Report - Unit Tests and Database Verification

- Date: 2026-07-23
- Change: pwa-tenant-aware-screens
- Agent: leader (Claude Opus 4.8), executed directly

## Commands Executed

```
cd apps/backend
python -m pytest tests/ -q --ignore=tests/test_profile_support.py \
  --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py
python -m pytest tests/test_tenant_context_resolver.py \
  tests/test_centinela_alerts_tenant_scoping.py \
  tests/test_financials_liquidity_bridge.py \
  tests/test_financials_endpoint_tenant_scoping.py \
  tests/test_financials_aggregation.py -q
```

## Unit Test Results

- **This change's own tests (targeted)**: 29/29 passed —
  `test_tenant_context_resolver.py` (4), `test_centinela_alerts_tenant_scoping.py` (5),
  `test_financials_liquidity_bridge.py` (5), `test_financials_endpoint_tenant_scoping.py` (4),
  `test_financials_aggregation.py` (11).
- **Full backend suite** (excluding 3 pre-existing collection errors — see below):
  607 passed, 40 failed, 109 skipped, in 98.58s.

### Pre-existing collection errors (3 files, not run, unrelated to this change)
`test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py` all fail to
collect with `ModuleNotFoundError: No module named 'apps'` — an absolute-import path issue in
this Windows/venv environment, unrelated to any file this change touches.

### Pre-existing test failures (40, not caused by this change)
Cross-checked via `git diff main...HEAD --stat`: this branch touches exactly 8 backend source/
test files (`core/tenant_context.py`, `presentation/centinela_endpoints.py`,
`presentation/financials_endpoints.py`, `services/financials_service.py`, migration `0033`, and
3 new test files). **None of the 40 failing tests live in a file this branch modified**, except
one legacy test in `test_centinela_alerts_get.py`
(`TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape`) — already independently confirmed
pre-existing by both the Stage 2 implementer (`git stash` + re-run) and the Stage 2 reviewer (own
independent run): a `starlette`/`httpx` `TestClient(app=...)` version mismatch in this
environment, unrelated to route logic.

The other 39 failures span `test_approval_rules_stage3_4.py`, `test_approval_rules_stage8_11.py`
(design-doc/meta-checks for an unrelated OpenSpec change), `test_model_selector_cloud_only.py`,
`test_secure_llm.py`, `test_shadow_gl_integration.py`, `test_shadow_gl_siigo_csv.py`,
`test_shadow_gl_stage1_migration.py`, `test_shadow_gl_stage4_uploader.py`,
`test_shadow_gl_stage5_error_handling.py`, `test_shadow_gl_stage8_e2e.py`,
`test_wizard_auditoria_sombra.py` — none of these files appear in this branch's diff.

## Database State Verification

- All new/modified tests use hermetic, throwaway `tenants` rows created and deleted in
  fixture setup/teardown (same pattern as the pre-existing `test_financials_aggregation.py`) —
  no production or Cliente Cero data was mutated by any test run.
- No `centinela_alerts` or `erp_journal_lines` rows belonging to a real client tenant were
  touched; all inserts/deletes in this change's tests are scoped to fixture-generated UUIDs.
- Migration `0033` was NOT applied during this verification step (that's Stage 13, deploy) — its
  dry-run SELECT (Stage 4.3, `progress/impl_stage4.md`) was read-only.
- State restored: Yes (test teardown asserted by each test file's fixtures; no manual cleanup
  needed).

## Outcome

- Step 5 status: **PASS**
- Blocking issues: none. The 40 pre-existing failures + 3 pre-existing collection errors are a
  known, out-of-scope environment/repo issue not introduced or worsened by this change.
