# Implementation report — Section 1: Tenant Scope Helper (TDD)

Change: `approval-queue-tenant-scoping`
Tasks: 1.1, 1.2, 1.3, 1.4 (Section 1 only)

## What was done

1. **1.1** — Wrote `apps/backend/tests/test_tenant_scope_resolution.py` with the 5 required
   test cases, mirroring `test_tenant_stamping.py`'s mocked-client style
   (`client.table().select().eq().single().execute().data`):
   - `test_client_with_resolved_tenant_gets_own_scope_not_all_tenants`
   - `test_cliente_cero_member_gets_all_tenants_scope`
   - `test_staging_identity_gets_cliente_cero_all_tenants_scope` (uses `dict(_STAGING_USER)`
     imported from `core.deps`)
   - `test_authenticated_unresolved_returns_none`
   - `test_missing_cliente_cero_row_still_resolves_client_tenant`

2. **1.2** — Ran `pytest tests/test_tenant_scope_resolution.py -v` before implementation:
   collection failed with `ImportError: cannot import name 'TenantScope' from
   'core.tenant_context'` — expected failure mode for a new-module addition (function/class
   don't exist yet).

3. **1.3** — Implemented in `apps/backend/core/tenant_context.py` (appended below the existing
   `resolve_cliente_cero_tenant_id`, which is untouched):
   - `from dataclasses import dataclass` added to imports
   - `from core.deps import _STAGING_USER` added to imports (top-level, not a function-local
     import — see "Deviations" below)
   - `TenantScope` frozen dataclass (`tenant_id: str`, `all_tenants: bool = False`)
   - `resolve_request_tenant_scope(user: dict, client) -> Optional[TenantScope]` implementing
     the 4-way ladder exactly as specified in `design.md` ("Tenant scope resolution (shared
     helper)" section), using `_STAGING_USER["id"]` instead of the literal string
     `"test-user-staging"`.

4. **1.4** — Ran `pytest tests/test_tenant_scope_resolution.py -v`: all 5 pass. Also ran
   `pytest tests/test_tenant_stamping.py -v` to confirm the existing Cliente Cero helper tests
   still pass (4/4 green, no regression).

## Deviations from the plan

- **Import style**: the task description offered a choice between a clean top-level
  `from core.deps import _STAGING_USER` (if no circular-import risk) or a literal-string
  fallback. I verified `core/deps.py`'s imports (`fastapi`, `typing`, `requests`, `jose`,
  `config`, `core.security`, `core.identity_resolver`) — it does **not** import anything from
  `core.tenant_context`, so there is no circular-import risk. Used the clean top-level import
  as instructed for that case. (I initially wrote it as a function-local import out of an
  abundance of caution, then moved it to module level once the circular-import check confirmed
  it was safe — final state is the top-level import.)

## Test output

```
$ python -m pytest tests/test_tenant_scope_resolution.py -v
collected 5 items
tests/test_tenant_scope_resolution.py::test_client_with_resolved_tenant_gets_own_scope_not_all_tenants PASSED [ 20%]
tests/test_tenant_scope_resolution.py::test_cliente_cero_member_gets_all_tenants_scope PASSED [ 40%]
tests/test_tenant_scope_resolution.py::test_staging_identity_gets_cliente_cero_all_tenants_scope PASSED [ 60%]
tests/test_tenant_scope_resolution.py::test_authenticated_unresolved_returns_none PASSED [ 80%]
tests/test_tenant_scope_resolution.py::test_missing_cliente_cero_row_still_resolves_client_tenant PASSED [100%]
======================= 5 passed, 20 warnings in 2.84s ========================

$ python -m pytest tests/test_tenant_stamping.py -v
collected 4 items
tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId::test_stamps_resolved_tenant_id_on_insert PASSED [ 25%]
tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId::test_no_cliente_cero_row_stamps_none_without_crashing PASSED [ 50%]
tests/test_tenant_stamping.py::TestSaveAlertsStampsTenantId::test_stamps_resolved_tenant_id_on_each_alert PASSED [ 75%]
tests/test_tenant_stamping.py::TestSaveAlertsStampsTenantId::test_does_not_override_an_explicitly_provided_tenant_id PASSED [100%]
======================= 4 passed, 20 warnings in 3.51s ========================
```

## Files touched

- `apps/backend/tests/test_tenant_scope_resolution.py` (new)
- `apps/backend/core/tenant_context.py` (extended — `resolve_cliente_cero_tenant_id` untouched)
- `openspec/changes/approval-queue-tenant-scoping/tasks.md` (1.1–1.4 checked off)
- `progress/impl_section1.md` (this report)

## Status

Section 1 (tasks 1.1–1.4) is complete and verified. Scope was strictly limited to this
section — no changes to Section 2+ files (`services/approval_queue_service.py`,
`presentation/approval_queue_endpoints.py`, other test files, etc.). Handing off for review.
