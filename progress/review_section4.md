# Review — task section4 (approval-queue-tenant-scoping, commit ff5dfd3)

**Verdict:** APPROVED

## Checkpoints

- C1 GET "" wiring matches design.md exactly: `presentation/approval_queue_endpoints.py:94-97`
  — `scope is None` → `DraftListResponse(drafts=[])` (200, empty); `scope.all_tenants` →
  `effective_tenant_id = tenant_id` (query param, defaults None = unfiltered); normal client →
  `effective_tenant_id = scope.tenant_id`, query param silently ignored. [x]
- C2 POST /enqueue: `scope is None` → 403 (`:138-139`); otherwise `tenant_id=scope.tenant_id`
  passed to `enqueue_draft` (`:154`). Dead `request.state.tenant_id` read and unused `Request`
  import are gone (confirmed via diff/grep — no `Request` import remains). [x]
- C3 POST /approve, /reject: `scope is None` → 403 (`:190-191`, `:229-230`); else
  `tenant_id=None if scope.all_tenants else scope.tenant_id` (`:198`, `:237`) — matches the
  design table's "unrestricted for operator, own tenant otherwise." [x]
- C4 `DraftListItem.tenant_id: Optional[str] = None` (`:67`), populated from `d.tenant_id`
  (`:113`). [x]
- C5 "Must-not-call guard" deviation: verified `core/tenant_context.py:58`,
  `resolve_cliente_cero_tenant_id(client)` is called unconditionally as step 1 of every ladder
  invocation — patching it to raise would break every test in the file, not just the
  unresolved-caller case, exactly as the implementer describes. The endpoint-level guard they
  substituted (patch `resolve_request_tenant_scope` → `None`, assert
  `ApprovalQueueService.<method>` is never called) is a stronger, more direct proof of the
  property that actually matters — "the write path never executes without a resolved scope" —
  than asserting a resolver function wasn't called. This is a legitimate, well-justified
  deviation, not scope creep. [x]
- C6 Tests run locally: `27 passed, 10 skipped, 20 warnings in 4.55s` — matches the reported
  count exactly. All 14 new endpoint tests pass; `test_tenant_stamping.py`,
  `test_approval_queue_service_scoping.py`, `test_tenant_scope_resolution.py` pass; all 10 in
  `test_approval_queue_persistence.py` skip (no `RUN_APPROVAL_QUEUE_DB`/service-role key set),
  confirmed collecting cleanly (10 items, up from 9 pre-change). [x]
- C7 Flagged persistence-test gap is real, confirmed by direct inspection of
  `test_approval_queue_persistence.py`: `TestEnqueuePersistence` (lines 62, 86, 101),
  `TestListDrafts` (115, 120, 135, 140, 155), and `TestApproveRejectPersistence` (161, 176,
  183, 205, 212) all call `enqueue_draft`/`approve_draft`/`reject_draft` with no `tenant_id`
  kwarg. Since Section 2 made `tenant_id` a required keyword-only param on all three methods,
  these calls will raise `TypeError` if run with `RUN_APPROVAL_QUEUE_DB=1`. Section 4 did not
  introduce this — it's an artifact of Section 2's signature change on tests Section 4 never
  touched — and `tasks.md` §5 ("Review and Update Existing Unit Tests") is explicitly the
  right place to fix it (5.1: "Re-read every test file touched in Sections 2–4 end to end").
  Correctly scoped as future work, correctly flagged loud in `impl_section4.md:152-161`. [x]
- C8 Scope discipline: no `apps/backend/migrations/0033*` file exists in the worktree —
  confirmed. `git show ff5dfd3 --stat` touches exactly 5 files: the endpoints module, the new
  test file, the persistence test extension, `tasks.md` (4.1-4.6 only), and
  `progress/impl_section4.md`. Sections 5-11 untouched. [x]
- Docs-sync: N/A for this checkpoint — no container/dependency change in `ARCHITECTURE.md`
  terms; Decision #13 update is explicitly deferred to §9.1, not owed by Section 4. [x]

## Flagged for Section 5 (do not miss)

`test_approval_queue_persistence.py`'s pre-existing tests in `TestEnqueuePersistence`,
`TestListDrafts`, and `TestApproveRejectPersistence` call `ApprovalQueueService.enqueue_draft` /
`approve_draft` / `reject_draft` **without a `tenant_id` kwarg**. These currently skip locally
(no `RUN_APPROVAL_QUEUE_DB=1`) so they show green, but they will `TypeError` the moment anyone
runs this file with the DB gate on, because Section 2 made `tenant_id` required-keyword-only on
all three methods. Section 5 (`tasks.md` 5.1-5.2) must update every one of these call sites to
pass an explicit `tenant_id` before this file can be trusted DB-gated.

## Required changes

None — this section is approved as-is.
