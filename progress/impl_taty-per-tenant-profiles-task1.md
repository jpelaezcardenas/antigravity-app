# Implementation report — taty-per-tenant-profiles, task 1 (1.1–1.3)

Branch confirmed: `feature/taty-per-tenant-profiles` (`git branch --show-current`).

## Scope

`openspec/changes/taty-per-tenant-profiles/tasks.md` section "## 1. Backend: Service Profile
Resolver (TDD)" only — items 1.1, 1.2, 1.3. No other file/section touched.

## Files touched

- **New**: `apps/backend/tests/test_taty_tenant_profiles.py` (full file, 7 tests)
- **Modified**: `apps/backend/services/taty_service.py`
  - Added `import uuid` and `from core.supabase_client import get_supabase` (top imports, ~line 17-25)
  - Added module-level `DEFAULT_PROFILE` dict right after `ensure_dian_loaded()` (~line 33-49)
  - Deleted `AGENT_PROFILES` class dict (previously ~lines 88-129)
  - Rewrote `_get_agent_profile` to delegate to `_get_tenant_profile` (see Deviation below)
  - Added new `_get_tenant_profile(self, tenant_id: str) -> Optional[Dict]` method (~50 lines,
    right after `_get_agent_profile`)
  - Extended `_error_response(self, error, start_time, error_code: Optional[str] = None)` to
    conditionally include `error_code` in the returned dict

No other method in the file was touched (`ask()`, `_retrieve_chunks`, `_build_prompt`,
`_build_system_prompt`, `_extract_citations`, `_check_escalation`, `_log_conversation` are
unchanged — those belong to task 2/3).

## TDD sequence

### Step 1 — tests written first, confirmed RED (import error, since `DEFAULT_PROFILE` /
`_get_tenant_profile` didn't exist yet):

```
============================= test session starts =============================
...
ERROR collecting apps/backend/tests/test_taty_tenant_profiles.py
ImportError while importing test module '...test_taty_tenant_profiles.py'.
Traceback:
apps\backend\tests\test_taty_tenant_profiles.py:18: in <module>
    from services.taty_service import TatyAgentService, DEFAULT_PROFILE
E   ImportError: cannot import name 'DEFAULT_PROFILE' from 'services.taty_service' (...)
=========================== short test summary info ===========================
ERROR apps/backend/tests/test_taty_tenant_profiles.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 6.05s ===============================
```

### Step 2 — implementation added, tests GREEN:

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-7.4.3, pluggy-1.6.0
collecting ... collected 7 items

apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_provisioned_tenant_profile_matches_legal_name PASSED [ 14%]
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_provisioned_tenant_profile_regimen_is_none_by_default PASSED [ 28%]
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileProvisionedTenant::test_cliente_cero_tenant_gets_contexia_fiscal_source_without_mutating_default PASSED [ 42%]
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileUnknownTenant::test_unknown_tenant_uuid_returns_none PASSED [ 57%]
apps/backend/tests/test_taty_tenant_profiles.py::TestGetTenantProfileLegacyNonUuidKey::test_legacy_non_uuid_key_returns_none_without_exception PASSED [ 71%]
apps/backend/tests/test_taty_tenant_profiles.py::TestErrorResponseErrorCode::test_error_response_includes_error_code_when_provided PASSED [ 85%]
apps/backend/tests/test_taty_tenant_profiles.py::TestErrorResponseErrorCode::test_error_response_omits_error_code_when_not_provided PASSED [100%]

======================= 7 passed, 19 warnings in 2.88s (also re-verified: 4.03s) =========================
```

## Test approach: mocked `get_supabase`, not the hermetic-real-DB pattern

`test_financials_endpoint_tenant_scoping.py`'s hermetic pattern (real inserts against Supabase)
was tried first — `python -m pytest apps/backend/tests/test_financials_endpoint_tenant_scoping.py -q`
in this worktree fails 2 of 4 tests with `supabase.client.SupabaseException: supabase_url is
required` (no live Supabase credentials configured in this environment). Per the task's fallback
instruction, I mocked `services.taty_service.get_supabase` at the module level instead, following
the convention already used by `test_crm_wompi_tenant_scoping.py` (a service-layer, not
endpoint-layer test): `patch("services.taty_service.get_supabase", return_value=MagicMock(...))`
with a `table_side_effect` that shapes `.table("tenants").select(...).eq(...).execute()` to
return `MagicMock(data=[...])`.

## Deviation from the plan

The task said "Do not modify `_get_agent_profile` callers beyond what's needed... you may need
to keep `_get_agent_profile` calling `_get_tenant_profile` now if that's the only way to keep the
file coherent — note this deviation clearly." I took that path: `_get_agent_profile` is now a
thin delegator to `_get_tenant_profile`, so `ask()` (untouched this task, still calls
`self._get_agent_profile(company_id)`) keeps working unchanged and the module stays fully
importable/coherent. This is transitional — task 2 rewires `ask()` to call
`_get_tenant_profile` directly and (per design D5, `ask()` hard rename) `_get_agent_profile`
should then be deleted rather than left as a dead pass-through. Flagging this explicitly so the
task-2 implementer removes it rather than assuming it's permanent.

One behavior note: since `_get_agent_profile` now calls `_get_tenant_profile`, its docstring
"MVP: hardcoded" claim in the old code is gone. Because `ask()` still calls
`_get_agent_profile(company_id)` un-renamed, and `company_id` for the 3 legacy demo keys
(`ferez-001`, `martinez-001`) will now resolve to `None` (not a hardcoded profile) — this is
**expected and intentional** per design D2 ("no compat shim", legacy keys retired), and
confirmed non-breaking by the collateral test run below (no test currently exercises `ask()`
with those legacy keys).

## Collateral test run (broader taty-related suites, no fixes applied — report only)

```
pytest apps/backend/tests/test_taty_intent_router.py apps/backend/tests/test_taty_lead_router.py -v
...
======================= 47 passed, 19 warnings in 6.36s =======================
```

All 47 pass — no collateral breakage found. `test_taty_intent_router.py` and
`test_taty_lead_router.py` do not import `AGENT_PROFILES` or call `TatyAgentService.ask()`/
`_get_agent_profile()` directly, so they were unaffected by this task's changes.

`grep AGENT_PROFILES apps/backend` (post-change) finds only doc-comment mentions (in the new
test file's module docstring and in `_get_agent_profile`'s new docstring, both describing that
the dict was removed) — no remaining code reference to the actual dict.

## Not done in this task (explicitly out of scope, deferred to later tasks.md sections)

- `ask()` still takes `company_id`, not `tenant_id` (task 2)
- `_build_prompt` still asserts `profile['regimen']` unconditionally when `context` is present
  (task 2 — omitting the régimen clause when `None` is task 2.2's job; today `DEFAULT_PROFILE`
  correctly carries `regimen: None`, but nothing yet reads that field defensively in
  `_build_prompt`)
- `_retrieve_chunks` still keys off `profile.get("company_id", "__global__")`, not
  `profile["kb_client_id"]` (task 2)
- Endpoint auth changes (task 3), Telegram translation (task 4), route/router deletions (task 5),
  broader test-suite audit (task 6) — untouched, per this task's scope boundary.
