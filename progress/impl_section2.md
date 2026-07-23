# Implementation report — Section 2: Service Layer (TDD)

Change: `approval-queue-tenant-scoping`
Tasks completed: 2.1, 2.2, 2.3, 2.4, 2.5
Commit: `d75e90f` (on top of Section 1's `3cbf6aa`)

## What was done

### 2.1 — Rewrote `TestEnqueueDraftStampsTenantId`

In `apps/backend/tests/test_tenant_stamping.py`, replaced the two tests that asserted the
OLD implicit-Cliente-Cero-resolution behavior with two tests matching the NEW contract:

- `test_stamps_explicitly_passed_tenant_id_on_insert` — calls
  `enqueue_draft(..., tenant_id=<explicit uuid>)` and asserts the inserted row's
  `tenant_id` equals that value. Also patches `core.tenant_context.resolve_cliente_cero_tenant_id`
  and asserts `mock_resolve.assert_not_called()` — proving the service no longer resolves
  Cliente Cero internally (chosen over the "removed import" approach so the test itself is
  the guardrail, not just code inspection; the import was also removed from the service, see
  2.4).
- `test_missing_tenant_id_returns_error_not_silent_insert` — calls
  `enqueue_draft(..., tenant_id=None)` and asserts it returns
  `(False, None, "tenant_id is required")` and that `insert()` was never called.

`TestSaveAlertsStampsTenantId` (centinela, unrelated) was left completely untouched.

### 2.2 — Scoping tests for `approve_draft`/`reject_draft`

Created a **new file**, `apps/backend/tests/test_approval_queue_service_scoping.py`, rather
than appending to `test_tenant_stamping.py`. Rationale: `test_tenant_stamping.py` is scoped
to insert-time stamping (the Ground Truth Correction #3 root-cause fix); this section covers
a different concern — read/update filtering on the approve/reject decision-lookup path — so a
dedicated file keeps each file's purpose singular and matches the existing pattern of
splitting concerns across test files in this repo (e.g. `test_tenant_scope_resolution.py`
being separate from `test_tenant_stamping.py` in Section 1).

Four tests, per the task spec:
- `test_approve_with_tenant_scope_filters_select_and_update_by_tenant`
- `test_approve_cross_tenant_returns_not_found`
- `test_approve_with_none_scope_is_unrestricted`
- `test_reject_with_tenant_scope_filters_by_tenant`

The mock helper `_mock_client_for_approve` builds independently-trackable select/update
MagicMock chains (each `.eq()` call is recorded via `call_args_list`) so tests can assert
exactly which `.eq(...)` filters were applied to each chain, without conflating select-time
and update-time calls.

### 2.3 — Confirmed red

Ran the 6 new/rewritten tests against the pre-2.4 code:

```
FAILED tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId::test_stamps_explicitly_passed_tenant_id_on_insert
FAILED tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId::test_missing_tenant_id_returns_error_not_silent_insert
FAILED tests/test_approval_queue_service_scoping.py::TestApproveDraftTenantScoping::test_approve_with_tenant_scope_filters_select_and_update_by_tenant
FAILED tests/test_approval_queue_service_scoping.py::TestApproveDraftTenantScoping::test_approve_cross_tenant_returns_not_found
FAILED tests/test_approval_queue_service_scoping.py::TestApproveDraftTenantScoping::test_approve_with_none_scope_is_unrestricted
FAILED tests/test_approval_queue_service_scoping.py::TestRejectDraftTenantScoping::test_reject_with_tenant_scope_filters_by_tenant
6 failed, 2 passed, 20 warnings in 6.70s
```

(The 2 that passed were pre-existing `TestSaveAlertsStampsTenantId` centinela tests, untouched.)
`approve_draft`/`reject_draft` failed with `TypeError: got an unexpected keyword argument
'tenant_id'` — confirming the old signature, as expected.

### 2.4 — Applied `apps/backend/services/approval_queue_service.py` changes

- Removed `from core.tenant_context import resolve_cliente_cero_tenant_id`.
- `enqueue_draft(draft_id, draft_type, journal_entry, memo="", *, tenant_id: str)` — dropped
  the internal `resolve_cliente_cero_tenant_id(supabase)` call; added
  `if not tenant_id: return False, None, "tenant_id is required"` right after the Critic
  validation block, before any DB access; the passed-in `tenant_id` is stamped on the
  `ApprovalDecision`.
- `approve_draft(decision_id, approval_reason, approved_by, *, tenant_id: Optional[str])` and
  `reject_draft(decision_id, rejection_reason, rejected_by, *, tenant_id: Optional[str])` —
  both the existence-check select (`.select("*")`/`.select("id")` chain) and the update chain
  now conditionally add `.eq("tenant_id", tenant_id)` when `tenant_id is not None`, alongside
  the existing `.eq("id", decision_id)` (not replacing it). The `"Decision {id} not found"`
  error string is unchanged and used for both the "genuinely missing" and "exists under
  another tenant" cases — no separate cross-tenant message, per design.md's no-existence-leak
  requirement.
- `Optional` was already imported at the file header (`Tuple, Dict, Any, List, Optional`) —
  no new import needed.

### 2.5 — Confirmed green

```
tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId::test_stamps_explicitly_passed_tenant_id_on_insert PASSED
tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId::test_missing_tenant_id_returns_error_not_silent_insert PASSED
tests/test_tenant_stamping.py::TestSaveAlertsStampsTenantId::test_stamps_resolved_tenant_id_on_each_alert PASSED
tests/test_tenant_stamping.py::TestSaveAlertsStampsTenantId::test_does_not_override_an_explicitly_provided_tenant_id PASSED
tests/test_approval_queue_service_scoping.py::TestApproveDraftTenantScoping::test_approve_with_tenant_scope_filters_select_and_update_by_tenant PASSED
tests/test_approval_queue_service_scoping.py::TestApproveDraftTenantScoping::test_approve_cross_tenant_returns_not_found PASSED
tests/test_approval_queue_service_scoping.py::TestApproveDraftTenantScoping::test_approve_with_none_scope_is_unrestricted PASSED
tests/test_approval_queue_service_scoping.py::TestRejectDraftTenantScoping::test_reject_with_tenant_scope_filters_by_tenant PASSED
tests/test_tenant_scope_resolution.py::test_client_with_resolved_tenant_gets_own_scope_not_all_tenants PASSED
tests/test_tenant_scope_resolution.py::test_cliente_cero_member_gets_all_tenants_scope PASSED
tests/test_tenant_scope_resolution.py::test_staging_identity_gets_cliente_cero_all_tenants_scope PASSED
tests/test_tenant_scope_resolution.py::test_authenticated_unresolved_returns_none PASSED
tests/test_tenant_scope_resolution.py::test_missing_cliente_cero_row_still_resolves_client_tenant PASSED

13 passed, 20 warnings in 2.43s
```

Section 1's `test_tenant_scope_resolution.py` (5 tests) re-run and confirmed unaffected.

## Files touched

- `apps/backend/tests/test_tenant_stamping.py` (rewrote `TestEnqueueDraftStampsTenantId`,
  left `TestSaveAlertsStampsTenantId` untouched)
- `apps/backend/tests/test_approval_queue_service_scoping.py` (new file, 4 tests)
- `apps/backend/services/approval_queue_service.py` (`enqueue_draft`, `approve_draft`,
  `reject_draft` signatures + bodies per design.md; removed unused import)
- `openspec/changes/approval-queue-tenant-scoping/tasks.md` (checked off 2.1-2.5)

## Deviations from plan

None. Followed the task instructions and design.md's "Service-layer contract" section
exactly. Chose a separate test file for the scoping tests (2.2) as permitted by the task
instructions ("your call") — rationale given above.

## Out of scope (not touched, per instructions)

`resolution_agent_service.py`, `social_ops_service.py`, `sell_machine_service.py`,
`presentation/approval_queue_endpoints.py`, migration `0033`, and any other Section 3+
artifacts — all untouched, as required.

## Note on pre-existing uncommitted files found in the worktree

At the start of this session, `feature_list.json` (active-change pointer + status updates)
and `progress/review_section1.md` were present but uncommitted/untracked, left over from
Section 1's setup. They were not part of this task's scope, so they were left as-is
(neither staged nor committed) rather than folded into the Section 2 commit — the leader
should confirm whether they belong to a separate Section 1 follow-up commit.
