# Implementation report — taty-per-tenant-profiles, task 3 (3.1–3.3)

Branch confirmed: `feature/taty-per-tenant-profiles` (`git branch --show-current`).

## Scope

`openspec/changes/taty-per-tenant-profiles/tasks.md` section "## 3. Backend: Endpoint Auth +
Tenant Resolution (TDD)" only — items 3.1, 3.2, 3.3. No other section touched. `core/deps.py`,
`financials_endpoints.py`, `telegram_endpoints.py`, `agents_endpoints.py`,
`taty_intent_router.py`, `taty_service.py` are untouched.

## Files touched

- **New**: `apps/backend/tests/test_taty_endpoints_tenant_scoping.py` (5 tests, 1 class,
  mirrors `test_financials_endpoint_tenant_scoping.py`'s direct-function-call pattern)
- **Modified**: `apps/backend/presentation/taty_endpoints.py`
  - Imports: added `Depends` (fastapi), `get_current_user` + `_STAGING_USER` (from
    `core.deps`), `get_supabase` (from `core.supabase_client`) — lines 10, 16-17
  - New local `_resolve_cliente_cero_tenant_id()` helper (lines 26-36) — copied verbatim
    in spirit from `financials_endpoints.py`, same query against `tenants` where
    `is_cliente_cero=True`, per design D3's explicit "matching existing convention beats
    inventing a shared module mid-change"
  - `TatyAskRequest.company_id`: `str` (required) → `Optional[str] = None` (lines 45-53),
    description updated to state it's deprecated and ignored for resolution
  - `TatyAskResponse`: added `error_code: Optional[str] = None` field (lines 112-115)
  - `ask_taty` (POST `/ask`, lines 128-215): added `user: dict = Depends(get_current_user)`
    param; implemented the 3-way resolution block before calling `taty.ask()` (lines
    174-187): resolved tenant → use it; staging identity (`user["id"] ==
    _STAGING_USER["id"]`) → `await _resolve_cliente_cero_tenant_id()`; else → return an
    in-band `TatyAskResponse` with Spanish `answer`, `error_code="tenant_not_resolved"`,
    `confidence=0.0`, `requires_human_review=True`, `citations=[]`, `latency_ms=0`. Call
    site now passes `tenant_id=tenant_id` instead of `company_id=request.company_id` (line
    196) — this is the fix for the previously-broken call flagged in task 2's report
    (`taty_endpoints.py:144`). Docstring updated: dropped the `company_id=ctx-001` JSON
    example and the `?company_id=ctx-001` query example, added an explicit
    "Auth / tenant resolution" section describing the 3 cases.
  - `ask_taty_get` (GET `/ask`, lines 223-247): added `x_hermes_profile: Optional[str] =
    Header(None)` and `user: dict = Depends(get_current_user)` params; `company_id` query
    param is now `Optional[str] = None` with an "ignored for resolution" description;
    delegates to `ask_taty(request, x_hermes_profile=x_hermes_profile, user=user)` so both
    handlers share exactly one resolution code path (no duplicated logic to test/maintain
    separately).

## Does POST/GET share resolution logic? How was both tested?

Yes — `ask_taty_get` is a thin query-param → `TatyAskRequest` adapter that calls `ask_taty`
directly (unchanged from before this task, just now forwarding `x_hermes_profile` and `user`
too). The 3-way resolution block lives in exactly one place (`ask_taty`). Per the task's
guidance ("don't blindly duplicate all 4 tests... use judgment"), tests 1–4 (resolved/staging/
unresolved/spoofed) exercise `ask_taty` directly; test 5
(`test_get_handler_shares_resolution_logic`) is a lighter smoke test that calls `ask_taty_get`
once and asserts the same `tenant_id` resolution reaches the mocked `taty.ask()` — proving the
GET path correctly forwards into the shared logic rather than re-testing all 4 scenarios twice.

## TDD sequence

### Step 1 — new tests written first, confirmed RED

```
FAILED test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_resolved_user_is_scoped_to_own_tenant
  TypeError: ask_taty() got an unexpected keyword argument 'user'
FAILED test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_staging_identity_falls_back_to_cliente_cero
  TypeError: ask_taty() got an unexpected keyword argument 'user'
FAILED test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_authenticated_unresolved_caller_gets_error_and_never_calls_cliente_cero
  AttributeError: <module 'presentation.taty_endpoints' ...> has no attribute '_resolve_cliente_cero_tenant_id'
FAILED test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_spoofed_company_id_is_ignored
  TypeError: ask_taty() got an unexpected keyword argument 'user'
FAILED test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_get_handler_shares_resolution_logic
  TypeError: ask_taty_get() got an unexpected keyword argument 'user'
======================= 5 failed, 20 warnings in 6.28s ========================
```

### Step 2 — implementation applied, all tests GREEN

One iteration snag along the way (not a design change, a test-harness detail): calling
`ask_taty_get` directly (bypassing FastAPI's request pipeline) leaves `Query(...)` default
objects unresolved for any param not explicitly passed, since FastAPI's dependency-injection
layer — which normally resolves `Query()` markers into plain values — never runs. Fixed by
passing `channel`/`conversation_id`/`user_id` explicitly in the smoke test rather than relying
on their `Query()` defaults; no production code was changed for this.

```
pytest apps/backend/tests/test_taty_endpoints_tenant_scoping.py apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_tenant_profiles.py -v

test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_resolved_user_is_scoped_to_own_tenant PASSED
test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_staging_identity_falls_back_to_cliente_cero PASSED
test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_authenticated_unresolved_caller_gets_error_and_never_calls_cliente_cero PASSED
test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_spoofed_company_id_is_ignored PASSED
test_taty_endpoints_tenant_scoping.py::TestAskTatyEndpointTenantScoping::test_get_handler_shares_resolution_logic PASSED
test_taty_ask_tenant_scoping.py::TestBuildPromptRegimenOmission::test_regimen_none_omits_regimen_clause PASSED
test_taty_ask_tenant_scoping.py::TestBuildPromptRegimenOmission::test_regimen_set_includes_regimen_clause PASSED
test_taty_ask_tenant_scoping.py::TestRetrieveChunksKbClientIdKeying::test_retrieve_chunks_passes_through_kb_client_id_to_retrieve_similar PASSED
test_taty_ask_tenant_scoping.py::TestRetrieveChunksKbClientIdKeying::test_cliente_cero_profile_retrieves_with_ctx_001_client_id PASSED
test_taty_ask_tenant_scoping.py::TestAskUsesTenantProfileDirectly::test_unknown_tenant_returns_tenant_not_found_error_code PASSED
test_taty_ask_tenant_scoping.py::TestAskUsesTenantProfileDirectly::test_resolved_tenant_calls_get_tenant_profile_not_get_agent_profile PASSED
test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_provisioned_tenant_profile_matches_legal_name PASSED
test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_provisioned_tenant_profile_regimen_is_none_by_default PASSED
test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_cliente_cero_tenant_gets_contexia_fiscal_source_without_mutating_default PASSED
test_taty_tenant_profiles.py::TestGetTenantProfileUnknownTenant::test_unknown_tenant_uuid_returns_none PASSED
test_taty_tenant_profiles.py::TestGetTenantProfileLegacyNonUuidKey::test_legacy_non_uuid_key_returns_none_without_exception PASSED
test_taty_tenant_profiles.py::TestErrorResponseErrorCode::test_error_response_includes_error_code_when_provided PASSED
test_taty_tenant_profiles.py::TestErrorResponseErrorCode::test_error_response_omits_error_code_when_not_provided PASSED

======================= 18 passed, 20 warnings in 6.21s =======================
```

All 5 new tests + 13 from tasks 1/2's suites (regression check) green, no failures.

## Module import check

```
$ python -c "import sys; sys.path.insert(0,'.'); from presentation import taty_endpoints; print('import OK')"
(run from apps/backend/)
import OK
```
(Same unrelated dev-only warning as task 2's report: "JWT_SECRET not set — using
auto-generated secret for development" — from an unrelated module's import-time side effect,
not from `taty_endpoints.py`.)

Confirms the previously-broken call site (task 2's report: `taty_endpoints.py:144`,
`taty.ask(company_id=request.company_id, ...)`) is fixed — it now reads
`taty.ask(tenant_id=tenant_id, ...)` (line 196) using the resolved tenant, never the request
body's `company_id`.

## Deviations

None from the plan. One test-only fix (Query-default resolution when calling the GET handler
directly, not via FastAPI's pipeline) — documented above, no production code impact.

## Not done in this task (explicitly out of scope, deferred to later tasks.md sections)

- Telegram `_resolve_tenant_for_company_id` translation helper (task 4)
- Deletion of the deprecated `POST /api/v1/agents/taty/ask` route in `agents_endpoints.py`
  (task 5) — that call site still raises `TypeError` on `company_id=` today, as flagged in
  task 2's report; task 5 deletes the route entirely rather than fixing the call
- Full `RUN_TESTS=1 bash init.sh` suite run (task 7) — task 2's reviewer flagged a
  pre-existing, unrelated issue in `test_shadow_gl_stage8_e2e.py`
- `apps/backend/tests` broader audit for other `AGENT_PROFILES`/`ctx-001`/`ferez-001`
  references (task 6)
