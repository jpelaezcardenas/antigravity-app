# Review — task section5 (approval-queue-tenant-scoping, commit 1aa3d50)

**Verdict:** APPROVED

## Checkpoints

- C1 (persistence file, all Section-4-flagged sites): read `apps/backend/tests/test_approval_queue_persistence.py` diff directly — every previously-flagged `enqueue_draft`/`approve_draft`/`reject_draft` call in `TestEnqueuePersistence`, `TestListDrafts`, `TestApproveRejectPersistence` now has `tenant_id=_TEST_TENANT_ID`. [x]
- C2 (tenant matching within a flow): every enqueue→approve/reject pair uses the same `_TEST_TENANT_ID` value (lines 171/183, 194/202, 225/233, 155/161). `test_approve_unknown_decision_id_fails` — read directly: it never calls `enqueue_draft`, only `approve_draft` on a fresh `uuid.uuid4()` never persisted. `tenant_id=None` with an inline comment is a sound judgment call — this is the pre-existing "not found" path, distinct from `TestTenantScopedRoundTrip` (Section 4.5) which already covers tenant-scoped isolation. [x]
- C3 spot-checked `test_approval_outbox_integration.py` and `test_vectorization_regression.py` diffs — all 5 enqueue/approve pairs use matching `_TEST_TENANT_ID`. [x]
- C4 `test_slice2_e2e.py` — confirmed `approve_draft(..., tenant_id=cliente_cero_tenant_id)` matches the fixture, not the hardcoded constant. Traced `generate_draft_with_retry` in `services/resolution_agent_service.py:158-162` — it does thread `tenant_id=tenant_id` into `enqueue_draft`, so the draft is genuinely enqueued under `cliente_cero_tenant_id`. Judgment sound. [x]
- C5 root-level `tests/test_approval_queue_integration.py` and `tests/test_fase3_e2e.py` — confirmed via grep neither file had any `pytestmark`/`skipif` gating before or after; they were genuinely broken call sites, now fixed consistently with matching tenant_id across enqueue/approve pairs. [x]
- C6 ran `cd apps/backend && python -m pytest tests/test_approval_queue_persistence.py tests/test_approval_outbox_integration.py tests/test_vectorization_regression.py tests/test_slice2_e2e.py -v` myself: `16 skipped, 19 warnings in 0.83s` — clean collection, no TypeError/ImportError, exact match to report. [x]
- C7 ran `python -m pytest tests/test_approval_queue_integration.py tests/test_fase3_e2e.py -v` from repo root myself: `3 failed, 2 passed`. Verified the 3 failures are `AssertionError: Enqueue failed: supabase_url is required`, raised from inside `enqueue_draft`'s try/except (per traceback: `services.approval_queue_service:approval_queue_service.py:107 Approval queue enqueue error`) — i.e. past the point a missing-tenant_id TypeError would fire. This is strong evidence the tenant_id kwarg fix itself is correct; remaining failure is env-credential related and pre-existing/unrelated to this change. [x]
- C8 spot-checked 3 of the 11 grep-audit matches directly in source: `services/sell_machine_service.py:20,112` and `services/social_ops_service.py:16,830` both import and call `resolve_cliente_cero_tenant_id` explicitly at the call site before `enqueue_draft`, confirming Section 3.2/3.3's "explicit resolution at the caller boundary" pattern — the "intentional" judgment is correct, not a leftover assumption. [x]
- C9 scope discipline: `git show 1aa3d50 --stat` touches exactly the 6 test files + tasks.md + progress/impl_section5.md. `core/tenant_context.py`, `services/approval_queue_service.py`, `presentation/approval_queue_endpoints.py` absent from the diff. No `apps/backend/migrations/0033*` file exists. [x]
- Docs-sync: N/A — no container/dependency change requiring an `ARCHITECTURE.md` update at this section.

## Required changes

None — approved as-is.
