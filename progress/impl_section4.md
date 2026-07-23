# Implementation report — approval-queue-tenant-scoping, Section 4 (Endpoints, TDD)

Scope: tasks.md 4.1-4.6 only. Sections 1-3 (helper, service layer, internal callers)
were already done and reviewed before this session (commits 3cbf6aa, d75e90f, 264243a).

## Files touched

- `apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py` (new, 14 tests)
- `apps/backend/presentation/approval_queue_endpoints.py` (all 4 routes rewired)
- `apps/backend/tests/test_approval_queue_persistence.py` (extended: `two_test_tenants`
  fixture + `TestTenantScopedRoundTrip.test_two_tenant_round_trip_is_isolated`)
- `openspec/changes/approval-queue-tenant-scoping/tasks.md` (4.1-4.6 checked off)

## 4.1 — Test file (TDD)

Mirrors `test_financials_endpoint_tenant_scoping.py`'s style: direct coroutine
invocation with fake `user` dicts, no `TestClient`. All 4 endpoint coroutines
(`list_drafts`, `enqueue_for_approval`, `approve_draft`, `reject_draft`) are imported
directly from `presentation.approval_queue_endpoints` and called with keyword args.

Two mocking seams:
1. `presentation.approval_queue_endpoints.resolve_request_tenant_scope` — monkeypatched
   per test to return a fixed `TenantScope` or `None`, independent of the real ladder
   (already fully covered by `test_tenant_scope_resolution.py`, Section 1).
2. `ApprovalQueueService.<method>` — monkeypatched per test to record the `tenant_id`
   kwarg it was called with (or to raise `AssertionError` if it must never be called —
   the "must-not-call guard" pattern from `test_financials_endpoint_tenant_scoping.py:151`,
   applied here to `ApprovalQueueService.enqueue_draft`/`approve_draft`/`reject_draft`
   rather than to `resolve_cliente_cero_tenant_id`, because in this design that resolver
   is called unconditionally as step 1 of the *real* ladder — see judgment call below).

10 tests requested by tasks.md 4.1, plus 4 extra for approve/reject 403 + reject-scope
symmetry (`test_approve_unresolved_returns_403`, `test_reject_passes_caller_tenant_scope`,
`test_admin_reject_passes_unrestricted_scope`, `test_reject_unresolved_returns_403`) — 14
total.

**Judgment call on the must-not-call guard (4.1's 6th bullet):** the task description
says to mirror `test_financials_endpoint_tenant_scoping.py:151`'s guard "on the Cliente
Cero resolver." In financials, `_resolve_cliente_cero_tenant_id` is only invoked
*conditionally* (staging-identity branch), so patching it to raise proves it's never
reached for an unresolved caller. In `core/tenant_context.resolve_request_tenant_scope`,
`resolve_cliente_cero_tenant_id(client)` is called **unconditionally** as step 1 of the
ladder (see `design.md`'s pseudocode) — every caller triggers it, resolved or not. Patching
it to raise would make every test in this file fail, not just the unresolved-caller one.
I moved the guard one level up: the endpoint-level test patches
`resolve_request_tenant_scope` to return `None` (simulating "no scope"), then asserts
`ApprovalQueueService.enqueue_draft` is never called and a 403 is raised. This is the
guard that actually matters at the endpoint layer — "the write path must never execute
when there's no resolved scope" — and it's a stronger check than merely asserting the
resolver function wasn't invoked.

## 4.2 — Confirmed failures

```
14 failed, 20 warnings in 3.26s
```
All failures were `AttributeError: module 'presentation.approval_queue_endpoints' has no
attribute 'resolve_request_tenant_scope'` (via `monkeypatch.setattr` target resolution) —
i.e. genuinely red because the endpoint module hadn't been touched yet.

## 4.3 — Implementation

`apps/backend/presentation/approval_queue_endpoints.py`:

- Imports added: `Depends` (fastapi), `get_current_user` (core.deps),
  `get_service_supabase` (core.supabase_client), `resolve_request_tenant_scope`
  (core.tenant_context). Removed `Request` (no longer used anywhere in the file).
- `DraftListItem` gained `tenant_id: Optional[str] = None`, populated from `d.tenant_id`
  in the list comprehension.
- Final signatures:

```python
@router.get("", response_model=DraftListResponse)
async def list_drafts(
    status: Optional[str] = Query(default=None),
    draft_type: Optional[str] = Query(default=None),
    tenant_id: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        return DraftListResponse(drafts=[])
    effective_tenant_id = tenant_id if scope.all_tenants else scope.tenant_id
    decisions = await ApprovalQueueService.list_drafts(
        status=status, draft_type=draft_type, tenant_id=effective_tenant_id
    )
    ...

@router.post("/enqueue", response_model=ApprovalResponse)
async def enqueue_for_approval(
    payload: EnqueueRequest, user: dict = Depends(get_current_user)
):
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        raise HTTPException(status_code=403, detail="No tenant resolved for caller")
    success, decision, error = await ApprovalQueueService.enqueue_draft(
        ..., tenant_id=scope.tenant_id,
    )

@router.post("/approve", response_model=ApprovalResponse)
async def approve_draft(request: ApprovalRequest, user: dict = Depends(get_current_user)):
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        raise HTTPException(status_code=403, detail="No tenant resolved for caller")
    success, decision, error = await ApprovalQueueService.approve_draft(
        ..., tenant_id=None if scope.all_tenants else scope.tenant_id,
    )

@router.post("/reject", response_model=ApprovalResponse)
async def reject_draft(request: RejectionRequest, user: dict = Depends(get_current_user)):
    # same shape as approve_draft
```

- Deleted the dead `tenant_id = getattr(http_request.state, "tenant_id",
  "default-tenant")` line and the `http_request: Request` param — it was never used for
  anything else in `enqueue_for_approval`, and no other route in this file referenced
  `Request`, so the import was dropped too.
- `GET ""`'s `?tenant_id=` admin filter: normal clients' query param is read but ignored
  (`effective_tenant_id = tenant_id if scope.all_tenants else scope.tenant_id` — the
  `else` branch never touches the query param).

## 4.4 — Confirmed green

```
14 passed, 20 warnings in 1.61s
```

## 4.5 — DB-gated round-trip test

Extended `apps/backend/tests/test_approval_queue_persistence.py` with:
- `two_test_tenants` fixture (module-local, borrows the pattern from
  `test_financials_endpoint_tenant_scoping.py`'s fixture of the same name — inserts 2
  throwaway `tenants` rows, yields their ids, deletes them on teardown; no
  `erp_journal_*` cleanup needed here since approval_queue rows are cleaned up by the
  file's existing `_cleanup` fixture, not by tenant deletion).
- `TestTenantScopedRoundTrip.test_two_tenant_round_trip_is_isolated`: enqueues under
  tenant A, asserts a tenant-B-scoped `list_drafts` excludes it, asserts a
  tenant-B-scoped `approve_draft` returns `"Decision {id} not found"`, then asserts a
  tenant-A-scoped `approve_draft` succeeds and the decision's status becomes
  `"approved"`.

**Gating:** inherits the file's existing `pytestmark = pytest.mark.skipif(
os.environ.get("RUN_APPROVAL_QUEUE_DB") != "1", ...)` — no new gate needed since it's in
the same module. Confirmed locally (no `RUN_APPROVAL_QUEUE_DB`/`SUPABASE_SERVICE_ROLE_KEY`
set): the file collects cleanly (10 items, up from 9) and all 10 skip, including the new
test:

```
10 skipped, 19 warnings in 1.35s
```

**Known pre-existing gap, out of this task's scope:** several *other* tests already in
this file (e.g. `test_approve_updates_row_and_returns_immediately`) call
`ApprovalQueueService.approve_draft(...)` without a `tenant_id` kwarg — that will raise a
`TypeError` (missing required keyword-only argument) if this file is ever actually run
with `RUN_APPROVAL_QUEUE_DB=1`, because Section 2 made `tenant_id` a required
keyword-only param on `approve_draft`/`reject_draft`/`enqueue_draft`. This is exactly the
kind of drift Section 5 ("Review and Update Existing Unit Tests") exists to catch across
Sections 2-4's touched files — I did not fix it here since it's out of Section 4's scope
and the task instructions explicitly said not to touch Sections 5-11. Flagging it
explicitly so Section 5 doesn't miss this file.

## 4.6 — e2e file check

`tests/e2e/test_multi_tenant_flow.py` (repo root) has exactly one approval-queue call:
`TestHermesOperators::test_approval_queue_with_tenant_context` (line 281), POSTing to
`/api/v1/approval-queue/enqueue` with a valid signed JWT (`token_contexia`, via
`core.security.create_access_token`) but a payload missing required `EnqueueRequest`
fields (`draft_type`, `lines`) — only `draft_id`, `operator`, `content` are sent.

Static analysis: FastAPI/pydantic validates the request body against `EnqueueRequest`
**before** the handler function (and therefore before my new
`resolve_request_tenant_scope` scope check) ever executes, so this always returns `422`
regardless of the tenant-scoping change — the existing assertion
`assert response.status_code in [200, 201, 404, 422]` still holds. No code change needed.

I attempted to run this test to confirm empirically, but the entire file's `client`
fixture (`TestClient(actual_app)`) errors on collection/setup in this environment with a
pre-existing, unrelated issue:
```
TypeError: Client.__init__() got an unexpected keyword argument 'app'
```
(httpx/starlette version mismatch in the local venv). I confirmed this is not caused by
my change by running a different test in the same file that never touches
approval-queue (`TestTenantContextMiddleware::*`) — it fails identically. Not something
to fix under this task's scope (would be an environment/dependency-pinning fix, unrelated
to approval-queue tenant scoping).

## Final targeted test run

```
cd apps/backend && python -m pytest tests/test_approval_queue_endpoint_tenant_scoping.py tests/test_tenant_stamping.py tests/test_approval_queue_service_scoping.py tests/test_tenant_scope_resolution.py tests/test_approval_queue_persistence.py -v
```

```
27 passed, 10 skipped, 20 warnings in 4.29s
```

## Deviations / judgment calls summary

1. Must-not-call guard applied to `ApprovalQueueService.*` methods at the endpoint layer
   instead of to `resolve_cliente_cero_tenant_id` directly — see 4.1 explanation above.
2. Added 4 extra tests beyond the 10 named in tasks.md 4.1 for full approve/reject
   403/scope symmetry (not required, but cheap and consistent with the approve-side
   coverage already requested).
3. Did not fix the pre-existing missing-`tenant_id`-kwarg calls in
   `test_approval_queue_persistence.py`'s older tests (`TestEnqueuePersistence`,
   `TestListDrafts`, `TestApproveRejectPersistence`) — out of Section 4's scope, flagged
   above for Section 5.
4. `tests/e2e/test_multi_tenant_flow.py` verified by static analysis only (correct
   behavior derived from FastAPI/pydantic validation order), not empirically, due to a
   pre-existing environment issue unrelated to this change.

## Not done (explicitly out of scope per instructions)

- Migration `0033` (Section 8) — not created.
- Sections 5-11 — not touched.
