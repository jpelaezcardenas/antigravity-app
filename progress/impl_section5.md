# Implementation report — Section 5 (approval-queue-tenant-scoping)

Task: tasks.md §5 "Review and Update Existing Unit Tests (MANDATORY)" — 5.1, 5.2.

## Context

Section 2 made `tenant_id` a required keyword-only parameter on
`ApprovalQueueService.enqueue_draft`/`approve_draft`/`reject_draft`. Section 4's reviewer
(`progress/review_section4.md`, "Flagged for Section 5") identified that several pre-existing
call sites across the test suite still called these methods without a `tenant_id` kwarg, which
would raise `TypeError` the moment those methods actually executed. This section fixes every
one of those call sites.

## 5.1 — Files re-read end to end and fixed

### `apps/backend/tests/test_approval_queue_persistence.py` (DB-gated, `RUN_APPROVAL_QUEUE_DB=1`)

Added a module-level constant near the top of the file (after the `pytestmark` skipif block):

```python
_TEST_TENANT_ID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"
```

This is the real production Cliente Cero tenant UUID (already used as the mock tenant id in
`test_tenant_stamping.py`, and confirmed by `openspec/changes/approval-queue-tenant-scoping/design.md`
task 0.3 to be the tenant every existing live `approval_queue` row carries). Chose it because:
`enqueue_draft` used to *silently default to Cliente Cero internally* before Section 2 — using
the same UUID as an explicit kwarg is the closest 1:1 preservation of these tests' original,
non-scoping-focused intent. There is no FK constraint on `approval_queue.tenant_id`
(migration `0001_add_tenant_id_columns.sql` — plain UUID column, default zeros, no
`REFERENCES`), so this is a safe standalone constant, not a live-DB dependency.

Call sites fixed (all previously missing `tenant_id`):
- `TestEnqueuePersistence::test_balanced_draft_persists_to_table` (line ~62 pre-change) →
  `tenant_id=_TEST_TENANT_ID`
- `TestEnqueuePersistence::test_unbalanced_draft_is_not_persisted` (~86) →
  `tenant_id=_TEST_TENANT_ID`
- `TestEnqueuePersistence::test_non_journal_draft_type_skips_balance_validation` (~101) →
  `tenant_id=_TEST_TENANT_ID`
- `TestListDrafts::test_list_returns_pending_drafts_across_draft_types` (~115, ~120) — both
  `enqueue_draft` calls → `tenant_id=_TEST_TENANT_ID`. The `list_drafts(status=...)` call in
  this test is deliberately left without a `tenant_id` filter — this test is about
  cross-draft-type listing, not tenant scoping (`list_drafts`'s `tenant_id` param already
  defaults to `None` = unrestricted, no signature change there).
- `TestListDrafts::test_list_filters_by_draft_type` (~135, ~140) — same treatment.
- `TestListDrafts::test_list_excludes_resolved_drafts_when_status_filtered` (~155) — enqueue
  gets `tenant_id=_TEST_TENANT_ID`; the following `approve_draft` call (~161) gets the **same**
  `tenant_id=_TEST_TENANT_ID` (draft enqueued under that tenant, so the approve must be scoped
  to the same tenant to succeed — a mismatched or `None` tenant would either 404 or silently
  pass unrestricted, changing what the test is actually proving).
- `TestApproveRejectPersistence::test_approve_updates_row_and_returns_immediately` (~176 enqueue,
  ~183 approve) — both stamped with `tenant_id=_TEST_TENANT_ID` (same tenant, matching flow).
- `TestApproveRejectPersistence::test_reject_updates_row` (~205 enqueue, ~212 reject) — same
  pattern.
- `TestApproveRejectPersistence::test_approve_unknown_decision_id_fails` (~232) — **judgment
  call**: this test never enqueues anything; it approves a random, never-created
  `decision_id` to prove the "not found" error path. There is no "matching tenant" to inherit,
  and the property under test ("even the operator can't approve a decision that doesn't exist")
  is explicitly about the unrestricted/admin path, not tenant isolation (that's what
  `TestTenantScopedRoundTrip` two paragraphs below already covers, added in Section 4.5). I set
  `tenant_id=None` explicitly with an inline comment explaining the choice, rather than reusing
  `_TEST_TENANT_ID`, to keep this test's intent (unrestricted "not found" behavior) legible and
  distinct from the tenant-scoped "not found" behavior already covered elsewhere.

`TestTenantScopedRoundTrip` (added in Section 4.5) was already fully correct — untouched.

### `apps/backend/tests/test_approval_outbox_integration.py` (DB-gated)

Same `_TEST_TENANT_ID` constant added (with a comment pointing back to
`test_approval_queue_persistence.py` for the rationale, to avoid duplicating the full
explanation). Three enqueue/approve pairs, all part of a single flow each (enqueue then
immediately approve the same draft) — every `approve_draft` call got the same
`tenant_id=_TEST_TENANT_ID` as the `enqueue_draft` call feeding it, in:
- `test_approving_tax_correction_creates_executor_outbox_row`
- `test_approve_returns_immediately_without_blocking`
- `test_non_tax_correction_draft_does_not_create_outbox_row`

### `apps/backend/tests/test_vectorization_regression.py` (DB-gated)

Same pattern, same constant + rationale comment. Two enqueue/approve pairs:
- `test_vectorization_fires_on_tax_correction_approval`
- `test_non_tax_correction_draft_skips_vectorization`

### `apps/backend/tests/test_slice2_e2e.py` (DB-gated, `RUN_SHADOW_GL=1` + `RUN_APPROVAL_QUEUE_DB=1`)

One `approve_draft` call. Unlike the files above, this test already has a real
`cliente_cero_tenant_id` module-scoped fixture (queries the live `tenants` table for
`is_cliente_cero = true`), and the draft being approved was generated by
`generate_draft_with_retry(tenant_id=cliente_cero_tenant_id, ...)` — which Section 3.1 already
threaded `tenant_id` through into `enqueue_draft`. So the draft is genuinely enqueued under
`cliente_cero_tenant_id`, and the `approve_draft` call must use the *same* fixture value (not
the hardcoded `_TEST_TENANT_ID` constant, which would be a different, unrelated UUID and would
make the approve 404 against a real, non-mocked Supabase instance). Fixed:
`tenant_id=cliente_cero_tenant_id`.

### Root-level `tests/test_approval_queue_integration.py` and `tests/test_fase3_e2e.py`

These are **not** `RUN_APPROVAL_QUEUE_DB`-gated at all (no `pytestmark`/`skipif`) — they call
`ApprovalQueueService` directly against whatever `get_service_supabase()` resolves to, with no
skip guard. Explicitly called out in the task instructions as needing the same check. Added the
same `_TEST_TENANT_ID` constant (with the same rationale comment) to both files and threaded it
through every `enqueue_draft`/`approve_draft` call:
- `tests/test_approval_queue_integration.py`: `test_balanced_draft_enqueued`,
  `test_unbalanced_draft_rejected`, `test_draft_approved_after_enqueue` (enqueue + approve, same
  tenant for both since it's one flow).
- `tests/test_fase3_e2e.py`: `test_cliente_cero_full_loop` (enqueue + approve, same tenant) and
  `test_blocked_unbalanced_draft` (enqueue only — Critic rejects before it would ever reach the
  tenant_id guard, but the kwarg must still be present since `tenant_id` is
  keyword-only-required with no default).

### Files re-read and confirmed already correct (no change needed)

- `apps/backend/tests/test_tenant_stamping.py` (Section 2) — both `enqueue_draft` calls already
  pass `tenant_id` explicitly (`explicit_tenant_id` / `None`), and
  `mock_resolve.assert_not_called()` correctly asserts the service no longer resolves Cliente
  Cero internally.
- `apps/backend/tests/test_approval_queue_service_scoping.py` (Section 2) — all four
  `approve_draft`/`reject_draft` calls already pass `tenant_id` (concrete value or `None` for
  the unrestricted-path tests) matching the scoping contract in `design.md`.
- `apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py` (Section 4) — endpoint
  tests call the FastAPI route handlers, not `ApprovalQueueService` methods directly; the
  handlers themselves resolve/pass `tenant_id` per `presentation/approval_queue_endpoints.py`
  (Section 4, out of scope for edits here). No `tenant_id`-kwarg issue exists in this file.

## 5.2 — `resolve_cliente_cero_tenant_id` grep audit

`grep -rn "resolve_cliente_cero_tenant_id" apps/backend/tests` (see command output below)
returned 11 non-binary matches across 5 files. Reviewed every one; all are intentional,
consistent with the design established in Sections 2–3 — **no code change made**:

- `test_financials_endpoint_tenant_scoping.py:133,153` — patches
  `_resolve_cliente_cero_tenant_id` on the *financials* endpoints module. Unrelated to
  approval-queue; pre-existing pattern from `per-tenant-client-access`, outside this change's
  scope.
- `test_operator_task_service.py:55,152,182,212` — patches
  `services.operator_task_service._resolve_cliente_cero_tenant_id`. `OperatorTaskService`
  (`list_drafts`-only caller per Section 3.4, "no signature change") is unaffected by this
  change; its own explicit-resolution pattern predates and is untouched by this OpenSpec change.
- `test_sell_machine_service.py:123,143,157` — patches
  `services.sell_machine_service.resolve_cliente_cero_tenant_id`. This is exactly the
  **Section 3.3** pattern: `sell_machine_service.py` resolves Cliente Cero explicitly at the
  call site (not inside `ApprovalQueueService`) before calling `enqueue_draft`. Intentional.
- `test_social_ops_endpoints.py:103,159` — patches
  `services.social_ops_service.resolve_cliente_cero_tenant_id`. Same as above — **Section 3.2**'s
  explicit call-site resolution pattern for `social_ops_service.py`. Intentional.
- `test_tenant_stamping.py:41` — patches `core.tenant_context.resolve_cliente_cero_tenant_id`
  as a **negative assertion** (`mock_resolve.assert_not_called()`), proving
  `ApprovalQueueService.enqueue_draft` no longer resolves Cliente Cero internally (the whole
  point of Section 2's refactor). Intentional and correct.

No leftover assumptions found; every match reflects the deliberate "explicit resolution at the
internal-caller boundary, never inside the service" design from Sections 2–3.

## Verification run

```
cd apps/backend && python -m pytest tests/test_approval_queue_persistence.py \
  tests/test_approval_outbox_integration.py tests/test_vectorization_regression.py \
  tests/test_slice2_e2e.py -v
```
Result: `16 skipped, 19 warnings in 1.68s` (no `RUN_APPROVAL_QUEUE_DB`/`RUN_SHADOW_GL` set
locally — all four files collect and skip cleanly, no `TypeError`/import/syntax errors; count
matches expected: 9 in `test_approval_queue_persistence.py` (pre-4.5) + 1 (4.5's
`TestTenantScopedRoundTrip`) + 3 + 2 + 1 = 16).

```
cd . && python -m pytest tests/test_approval_queue_integration.py tests/test_fase3_e2e.py -v
```
Run from the repo root (these two files are **not** gated and are not normally invoked with a
`RUN_*` env var — `conftest.py` at repo root only adds `apps/backend` to `sys.path`, no skip
logic). Result: `3 failed, 2 passed`.

The 2 passes (`test_unbalanced_draft_rejected`, `test_blocked_unbalanced_draft`) never reach the
Supabase call — Agent Critic rejects the unbalanced entry first, so `enqueue_draft` returns
`(False, None, "...")` before touching the DB.

The 3 failures (`test_balanced_draft_enqueued`, `test_draft_approved_after_enqueue`,
`test_cliente_cero_full_loop`) all fail with the **same** message:
`AssertionError: Enqueue failed: supabase_url is required` — this is `get_service_supabase()`
raising because `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` are not set in this local
environment. This is a **pre-existing environmental condition**, not caused by this change —
these two files were never DB-gated to begin with, so they were already broken locally before
Section 5 (or before this entire OpenSpec change) whenever no live Supabase credentials are
configured. Critically, the failure now happens *inside* `enqueue_draft`'s `try/except` (i.e.
past the point where a missing-`tenant_id` `TypeError` would have occurred) — confirming the
`tenant_id` kwarg fix is correct and the remaining failure is unrelated to this section's scope.
No credentials are available in this environment to run these live, matching every other
DB-gated file in the suite.

## Files changed

- `apps/backend/tests/test_approval_queue_persistence.py`
- `apps/backend/tests/test_approval_outbox_integration.py`
- `apps/backend/tests/test_vectorization_regression.py`
- `apps/backend/tests/test_slice2_e2e.py`
- `tests/test_approval_queue_integration.py`
- `tests/test_fase3_e2e.py`
- `openspec/changes/approval-queue-tenant-scoping/tasks.md` (5.1, 5.2 → `[x]`)

No production code touched (`core/tenant_context.py`, `services/approval_queue_service.py`,
`presentation/approval_queue_endpoints.py` untouched, per scope discipline). No migration 0033
created.
