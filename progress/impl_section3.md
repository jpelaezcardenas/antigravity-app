# Implementation report — Section 3: Internal Service Callers

Change: `approval-queue-tenant-scoping`
Tasks: 3.1–3.5 (Section 3 only)
Branch: `worktree-approval-queue-tenant-scoping`, on top of `d75e90f` (Section 2)

## Summary

Section 2 made `ApprovalQueueService.enqueue_draft` require a keyword-only `tenant_id: str`
(falsy → error, no DB call) and `approve_draft`/`reject_draft` require a keyword-only
`tenant_id: Optional[str]`. This section threads/resolves `tenant_id` explicitly at every
production call site of `enqueue_draft` so none of them break, per `design.md`'s "Internal
callers — explicit, never a silent default" section.

## 3.1 — `apps/backend/services/resolution_agent_service.py`

Two `enqueue_draft` calls, both inside functions that already receive `tenant_id` as a
parameter (`generate_draft`, `generate_draft_with_retry`). Threaded the existing `tenant_id`
through as the new required keyword — no new resolution logic needed here, just wiring:

- Line ~106 (`generate_draft`): `enqueue_draft(..., tenant_id=tenant_id)`
- Line ~161 (`generate_draft_with_retry`): `enqueue_draft(..., tenant_id=tenant_id)`

**Tests:** Searched for existing coverage. `apps/backend/tests/test_resolution_agent.py` and
`apps/backend/tests/test_resolution_agent_retry.py` are the dedicated test files for this
service, but both are gated `pytestmark = pytest.mark.skipif(RUN_SHADOW_GL != "1", ...)` —
live-Supabase-plus-LLM integration tests that call `generate_draft`/`generate_draft_with_retry`
directly with a real `cliente_cero_tenant_id` fixture; they never mock `enqueue_draft`'s
keyword signature, so no update was required. `tests/test_slice2_e2e.py` similarly imports
`generate_draft_with_retry` under the same `RUN_SHADOW_GL` gate. Ran all three files locally
(no `RUN_SHADOW_GL` env var set) — all 3 tests SKIPPED as expected, confirming they still
collect cleanly. No dedicated hermetic/mocked unit test exists for
`resolution_agent_service.py`'s `enqueue_draft` call sites specifically; flagging this as a
pre-existing gap (not introduced by this change) rather than inventing new test scaffolding
outside the assigned scope.

## 3.2 — `apps/backend/services/social_ops_service.py`

`draft_lead_reply` (draft_type="social_reply") had no per-request tenant in scope (this is a
Contexia-internal Taty agent flow). Added, immediately before the `enqueue_draft` call:

```python
tenant_id = resolve_cliente_cero_tenant_id(get_supabase())
if not tenant_id:
    logger.warning(
        "Skipping approval_queue enqueue for social_reply draft %s: "
        "Cliente Cero tenant could not be resolved",
        draft["id"],
    )
else:
    await ApprovalQueueService.enqueue_draft(..., tenant_id=tenant_id)
```

Imported `resolve_cliente_cero_tenant_id` from `core.tenant_context`. Used `get_supabase()`
(anon client) — already imported in this file for `_mirror_supabase`, and the read
(`tenants` table, `is_cliente_cero=true`) doesn't need service-role privilege.

**Tests (`tests/test_social_ops_endpoints.py`):**
- Updated the existing `test_draft_lead_reply_enqueues_to_approval_queue_with_social_reply_draft_type`
  to also `patch("services.social_ops_service.resolve_cliente_cero_tenant_id", return_value=...)`
  and assert `call_kwargs.get("tenant_id") == fake_cliente_cero_tenant_id`.
- Added a new test, `test_draft_lead_reply_skips_enqueue_when_cliente_cero_unresolved`, which
  patches the resolver to return `None` and asserts `enqueue_draft` is never awaited while the
  lead-reply draft itself is still created/returned (log-and-skip, not a crash).

## 3.3 — `apps/backend/services/sell_machine_service.py`

`create_campaign_package` (draft_type="campaign_package") — same pattern as 3.2: added
`from core.supabase_client import get_supabase` and
`from core.tenant_context import resolve_cliente_cero_tenant_id`, then resolved `tenant_id`
immediately before the `enqueue_draft` call.

**Judgment call on control flow:** unlike `draft_lead_reply` (which can silently return the
draft without enqueueing), `create_campaign_package`'s existing contract is strict — it always
either returns an `ApprovalDecision` or raises `RuntimeError`. There is no "skip and return
something partial" path in its signature (`-> Any`, docstring: "Raises RuntimeError if
enqueueing fails"). So an unresolved Cliente Cero tenant is treated as an enqueue failure: log
a warning, then `raise RuntimeError("Failed to enqueue campaign package: Cliente Cero tenant
could not be resolved")` — same exception type callers already handle for the DB-failure case,
without ever calling `enqueue_draft`. This satisfies "log + skip the enqueue" (skip = never
call it) while staying inside this function's existing control-flow contract instead of
inventing a new return shape.

`list_drafts`-backed `list_campaigns` at ~line 129 is unchanged, as directed (unfiltered
internal read, `tenant_id=None` remains valid).

**Tests (`tests/test_sell_machine_service.py`):**
- Updated `test_enqueues_a_campaign_package_draft` and `test_raises_on_enqueue_failure` to
  patch `resolve_cliente_cero_tenant_id` and assert the resolved `tenant_id` is passed through.
- Added `test_raises_when_cliente_cero_tenant_unresolved`: patches the resolver to `None`,
  asserts `RuntimeError` is raised and `enqueue_draft` is never awaited.

## 3.4 — `tests/test_operator_task_service.py`

Ran directly: `pytest tests/test_operator_task_service.py -v` → **13 passed**, no changes
needed (its `list_drafts` call has no signature change, confirmed by inspection — it's an
unfiltered internal read).

## 3.5 — Grep verification

`grep -rn "enqueue_draft(" apps/backend` (production, excluding the method definition and
tests) shows exactly these call sites, all now passing `tenant_id` explicitly:
- `services/resolution_agent_service.py:106,158`
- `services/sell_machine_service.py:123`
- `services/social_ops_service.py:838`
- `presentation/approval_queue_endpoints.py:122` — **intentionally untouched**, this is
  Section 4 scope (endpoint wiring); it will fail loudly until Section 4 implements
  `resolve_request_tenant_scope` there, which is expected and correct sequencing.

`grep -rn "\.approve_draft(\|\.reject_draft("` shows the only production callers outside
`services/approval_queue_service.py` itself are:
- `presentation/approval_queue_endpoints.py` (Section 4, out of scope)
- `presentation/social_ops_endpoints.py:244,254` — calls `SocialOpsService.approve_draft` /
  `SocialOpsService.reject_draft`, which are **unrelated in-memory methods on a different
  class** (`services/social_ops_service.py:929,947`; in-memory `social_command_drafts` /
  `social_reply_drafts` bookkeeping, not `ApprovalQueueService`). No change needed — verified
  by reading the two method definitions.

No stray callers found on the old implicit-Cliente-Cero signature.

## Files touched

- `apps/backend/services/resolution_agent_service.py` (2 call sites)
- `apps/backend/services/social_ops_service.py` (1 call site + import)
- `apps/backend/services/sell_machine_service.py` (1 call site + 2 imports)
- `apps/backend/tests/test_social_ops_endpoints.py` (1 test updated, 1 test added)
- `apps/backend/tests/test_sell_machine_service.py` (2 tests updated, 1 test added)
- `openspec/changes/approval-queue-tenant-scoping/tasks.md` (3.1–3.5 checked off)

## Test results

```
pytest tests/test_tenant_stamping.py tests/test_approval_queue_service_scoping.py \
       tests/test_tenant_scope_resolution.py tests/test_social_ops_endpoints.py \
       tests/test_sell_machine_service.py tests/test_operator_task_service.py -v

47 passed, 20 warnings in 3.51s
```

```
pytest tests/test_resolution_agent.py tests/test_resolution_agent_retry.py tests/test_slice2_e2e.py -v

3 skipped, 19 warnings in 1.22s   (all RUN_SHADOW_GL-gated, expected — no live Supabase/LLM creds here)
```

Full backend suite (`pytest tests/ -q --ignore=tests/test_profile_support.py
--ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py`, those 3
ignored for a pre-existing unrelated `ModuleNotFoundError: No module named 'apps'` import-path
issue) — result: **591 passed, 40 failed, 109 skipped, 13 errors**. Verified none of the 40
failures / 13 errors touch any file changed in this section (`git status --short` cross-checked
against the failure list) — they are pre-existing issues unrelated to Section 3: a
`starlette.testclient` / `httpx` version mismatch (`Client.__init__() got an unexpected keyword
argument 'app'`) affecting several endpoint tests, doc/migration-existence assertions for other
OpenSpec changes (Phase 7/8 stage acceptance tests), and Siigo CSV parser tests — none reference
`approval_queue`, `enqueue_draft`, `resolution_agent_service`, `social_ops_service`, or
`sell_machine_service`.

## Deviations / judgment calls

1. **3.1**: no test file needed updating (explained above) — deviates from the task's phrasing
   ("update its tests") only in that there was nothing to update; documented the investigation
   instead of fabricating a mock.
2. **3.3**: `create_campaign_package`'s "log + skip" was implemented as "log, then raise
   `RuntimeError`" rather than a silent skip, because the function's existing contract has no
   partial-success return path — this keeps behavior inside the function's documented contract
   (raise-or-succeed) instead of introducing a new implicit return shape. `social_ops_service.py`
   (3.2) genuinely skips (returns the draft without enqueueing) because `draft_lead_reply`
   already tolerates optional side effects (the Supabase mirror write is best-effort too).

Scope discipline respected: did not touch `presentation/approval_queue_endpoints.py` (Section 4)
or create migration `0033` (Section 8).
