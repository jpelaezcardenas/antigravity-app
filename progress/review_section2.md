# Review — task section2 (approval-queue-tenant-scoping, commit d75e90f)

**Verdict:** APPROVED

## Checkpoints
- C1 (enqueue_draft signature `(draft_id, draft_type, journal_entry, memo="", *, tenant_id: str)`): [x] — `approval_queue_service.py:52-58`.
- C2 (no internal Cliente Cero resolution, import removed): [x] — `import from core.tenant_context` deleted (diff line 16); `resolve_cliente_cero_tenant_id(supabase)` call removed (was line ~68).
- C3 (falsy tenant_id -> `(False, None, "tenant_id is required")`, no DB write): [x] — guard at `approval_queue_service.py:80-81` runs before `get_service_supabase()`; `test_missing_tenant_id_returns_error_not_silent_insert` asserts `insert.assert_not_called()`.
- C4 (approve_draft/reject_draft gain required `*, tenant_id: Optional[str]`): [x] — both signatures updated, no default value (keyword-only, mandatory).
- C5 (`.eq("tenant_id", tenant_id)` on both select and update when not None): [x] — verified directly in code for approve_draft (lines ~148-151, ~178-181) and reject_draft (mirrored), not just via test.
- C6 (cross-tenant mismatch = same error string as missing id, no leak): [x] — single `f"Decision {decision_id} not found"` string used for both cases; `test_approve_cross_tenant_returns_not_found` confirms.
- C7 (tenant_id=None -> fully unrestricted): [x] — conditional `.eq` only applied `if tenant_id is not None`; `test_approve_with_none_scope_is_unrestricted` asserts no `tenant_id` eq call present.
- C8 (tests non-tautological): [x] — mentally reverting any of the added `.eq("tenant_id", ...)` calls, or reverting the falsy-tenant_id guard, or restoring the old `resolve_cliente_cero_tenant_id` call, causes the corresponding new test to fail. Confirmed red-then-green sequence documented and independently re-run.
- C9 (tests pass): [x] — `python -m pytest tests/test_tenant_stamping.py tests/test_approval_queue_service_scoping.py tests/test_tenant_scope_resolution.py -v` -> 13 passed, 0 failed.
- C10 (scope discipline): [x] — `git show d75e90f --stat` touches only `approval_queue_service.py`, `test_approval_queue_service_scoping.py` (new), `test_tenant_stamping.py`, and `tasks.md`. No hits for `resolution_agent_service.py`, `social_ops_service.py`, `sell_machine_service.py`, or `presentation/approval_queue_endpoints.py`.
- C11 (CHECKPOINTS.md docs-sync gate): [x] — no tenant/approval-queue-specific gate exists yet in `DEPLOYMENT_STAGE/CHECKPOINTS.md`; this is an internal service-layer TDD checkpoint, not a deploy-stage checkpoint, so no update is due here. No container/dependency change occurred (still Railway FastAPI backend, same Supabase tables), so `ARCHITECTURE.md` does not need updating for this commit.

## Required changes
None.
