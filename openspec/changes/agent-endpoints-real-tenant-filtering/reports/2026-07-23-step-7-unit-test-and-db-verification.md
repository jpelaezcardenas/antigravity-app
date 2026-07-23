# Stage 7 — Unit Test and DB State Verification

## Targeted test files (Stages 1-6)

```
pytest tests/test_agents_endpoints_auth.py tests/test_agent_stub_endpoints_tenant.py
       tests/test_centinela_endpoint_tenant_scoping.py tests/test_taty_endpoints_tenant_scoping.py
       tests/test_approval_queue_endpoint_tenant_scoping.py tests/test_tenant_context_helpers.py
       tests/test_tenant_scope_resolution.py tests/test_tenant_stamping.py -v
```

All 61 tests pass (2 + 6 + 6 + 5 + 14 + 3 + 5 + 5, adjusted after Stage 4's removal of 3
`resolve_caller_tenant`-specific tests and its net-new tests across the migrated files).

No hermetic Supabase fixtures are used by any test touched in this change — every one of the
6 in-scope endpoint functions is called directly with fake `user` dicts and monkeypatched
service/helper calls (mirroring `test_financials_endpoint_tenant_scoping.py`), so there is no
database state to capture a baseline for or verify teardown against.

## Full backend suite comparison

Baseline (unmodified code on this branch's tip before Stages 1-6, new test files excluded via
`--ignore`):
```
40 failed, 666 passed, 112 skipped, 13 errors
```

After Stages 1-6 (full suite, new test files included):
```
40 failed, 671 passed, 112 skipped, 13 errors
```

**Identical 40 failures and 13 errors in both runs** (same test IDs, verified by diff) — zero
regressions introduced by this change. The pass-count delta (+5) is fully explained:
+8 from the 2 new test files (`test_agents_endpoints_auth.py`,
`test_agent_stub_endpoints_tenant.py`), -3 from Stage 4's removal of
`TestResolveCallerTenant`'s 3 tests in `test_tenant_context_helpers.py` (the helper they
covered was deleted; `test_tenant_scope_resolution.py` already covers the same 3 branches for
the now-canonical `resolve_request_tenant_scope`).

## Pre-existing failures/errors (not touched by this change, verified unchanged)

- `test_secure_llm.py::test_pulso_analyze_endpoint_anonymizes_outbound_prompt` and
  `test_centinela_alerts_get.py::TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape` —
  both use `fastapi.testclient.TestClient(app)` and fail with
  `TypeError: Client.__init__() got an unexpected keyword argument 'app'` — a
  starlette/httpx version mismatch in this local environment, reproduced identically on
  unmodified code via `git stash`. Not caused by this change's auth-gating; these routes never
  reach the new `Depends(get_current_user)` code path before the TestClient constructor itself
  fails.
- `test_shadow_gl_*`, `test_wizard_auditoria_sombra.py`, `test_approval_rules_stage*.py`,
  `test_model_selector_cloud_only.py` (40 total) — unrelated subsystems (Siigo CSV parsing,
  Shadow GL migrations, wizard endpoint, approval-rules OpenSpec-artifact-existence checks).
- 13 `ERROR`s in `test_financials_aggregation.py` / `test_financials_endpoint_tenant_scoping.py`
  — pre-existing, env-var-gated integration tests requiring `SUPABASE_SERVICE_ROLE_KEY`, absent
  from this local `.env` (documented gap, see `openspec/changes/agent-endpoints-real-tenant-filtering/design.md`'s testing strategy note).
- 3 collection errors (`test_profile_support.py`, `test_swarm_operators.py`,
  `test_t11_integration.py`) — pre-existing `ModuleNotFoundError: No module named 'apps'`
  (wrong import path style, unrelated to this change), excluded via `--ignore` from both runs
  for a like-for-like comparison.

## Conclusion

Stage 7 passes: all new/updated tests green, full-suite regression diff is clean (0 new
failures), database-state verification is not applicable (no DB-touching tests in this
change's scope).
