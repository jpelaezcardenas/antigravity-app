# Tasks — Approval Queue Tenant Scoping

## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/approval-queue-tenant-scoping` from updated `main`
      (done via isolated worktree `.claude/worktrees/approval-queue-tenant-scoping`, branch
      `worktree-approval-queue-tenant-scoping`, HEAD = `origin/main` @ `f944918`)
- [x] 0.2 Verify branch creation and current branch status (`git branch --show-current`)
- [x] 0.3 Read-only verification query: confirm live `approval_queue.tenant_id` values —
      6/6 rows carry the real Cliente Cero UUID `e2d30d09-6b96-4ebe-a79a-c6aff7a5df34`, no
      NULL/zeros rows (recorded in `design.md`)

## 1. Tenant Scope Helper (TDD)

- [x] 1.1 Write `apps/backend/tests/test_tenant_scope_resolution.py` (mocked client, mirrors
      `test_tenant_stamping.py` style):
  - `test_client_with_resolved_tenant_gets_own_scope_not_all_tenants`
  - `test_cliente_cero_member_gets_all_tenants_scope`
  - `test_staging_identity_gets_cliente_cero_all_tenants_scope`
  - `test_authenticated_unresolved_returns_none`
  - `test_missing_cliente_cero_row_still_resolves_client_tenant`
- [x] 1.2 Run the new tests — confirm they fail (no implementation yet)
- [x] 1.3 Implement `TenantScope` dataclass + `resolve_request_tenant_scope(user, client)` in
      `apps/backend/core/tenant_context.py` per `design.md`
- [x] 1.4 Run 1.1's tests — confirm green

## 2. Service Layer (TDD)

- [ ] 2.1 Rewrite `apps/backend/tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId`:
  - `test_stamps_explicitly_passed_tenant_id_on_insert`
  - `test_missing_tenant_id_returns_error_not_silent_insert`
  - (leave `TestSaveAlertsStampsTenantId` — centinela — untouched)
- [ ] 2.2 Add scoping tests (same file or new `test_approval_queue_service_scoping.py`):
  - `test_approve_with_tenant_scope_filters_select_and_update_by_tenant`
  - `test_approve_cross_tenant_returns_not_found`
  - `test_approve_with_none_scope_is_unrestricted`
  - `test_reject_with_tenant_scope_filters_by_tenant`
- [ ] 2.3 Run 2.1/2.2 — confirm they fail against current code
- [ ] 2.4 Apply `apps/backend/services/approval_queue_service.py` changes per `design.md`:
      `enqueue_draft` requires `tenant_id` kw (no internal Cliente Cero resolution, guard
      returns error on falsy value); `approve_draft`/`reject_draft` require `tenant_id:
      Optional[str]` kw, add `.eq("tenant_id", ...)` to both the existence-select and the
      update when not None; remove the `core.tenant_context` import
- [ ] 2.5 Run 2.1/2.2 — confirm green

## 3. Internal Service Callers (explicit Cliente Cero, no silent default)

- [ ] 3.1 `apps/backend/services/resolution_agent_service.py:106,157` — pass the
      already-in-scope `tenant_id` through to `enqueue_draft`; update its tests
- [ ] 3.2 `apps/backend/services/social_ops_service.py:829` — resolve
      `resolve_cliente_cero_tenant_id(get_supabase())` explicitly at the call site before
      `enqueue_draft`; log + skip if `None`; update `tests/test_social_ops_endpoints.py`
- [ ] 3.3 `apps/backend/services/sell_machine_service.py:110` — same explicit resolution;
      update `tests/test_sell_machine_service.py`
- [ ] 3.4 Confirm `tests/test_operator_task_service.py` still green (no signature change to
      `list_drafts`)
- [ ] 3.5 `grep -rn "enqueue_draft(" apps/backend` — confirm every call site was updated (no
      stray callers left on the old implicit-Cliente-Cero signature)

## 4. Endpoints (TDD)

- [ ] 4.1 Write `apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py`
      (financials-style: direct coroutine calls with fake `user` dicts):
  - `test_enqueue_stamps_callers_resolved_tenant`
  - `test_client_list_is_scoped_to_own_tenant`
  - `test_admin_cliente_cero_member_lists_all_tenants`
  - `test_admin_can_filter_by_tenant_query_param`
  - `test_authenticated_unresolved_gets_empty_list`
  - `test_authenticated_unresolved_enqueue_returns_403_never_cliente_cero` (must-not-call
    guard on the Cliente Cero resolver, same trick as
    `test_financials_endpoint_tenant_scoping.py:151`)
  - `test_staging_identity_enqueues_under_cliente_cero_backcompat`
  - `test_approve_passes_caller_tenant_scope`
  - `test_admin_approve_passes_unrestricted_scope`
  - `test_list_response_includes_tenant_id_field`
- [ ] 4.2 Run 4.1 — confirm failures
- [ ] 4.3 Implement `apps/backend/presentation/approval_queue_endpoints.py` changes per
      `design.md`: `Depends(get_current_user)` on all 4 routes, scope resolution, `?tenant_id`
      admin filter, `DraftListItem.tenant_id`, delete the dead `request.state` read
- [ ] 4.4 Run 4.1 — confirm green
- [ ] 4.5 Extend the DB-gated `apps/backend/tests/test_approval_queue_persistence.py` with a
      hermetic two-tenant round trip (borrow the throwaway-tenant fixture pattern from
      `test_financials_endpoint_tenant_scoping.py`): enqueue under tenant A, assert a
      tenant-B-scoped list excludes it, tenant-B-scoped approve returns not-found,
      tenant-A-scoped approve succeeds
- [ ] 4.6 Check `tests/e2e/test_multi_tenant_flow.py` (repo root) for unauthenticated
      approval-queue calls; update or env-gate as needed

## 5. Review and Update Existing Unit Tests (MANDATORY)

- [ ] 5.1 Re-read every test file touched in Sections 2–4 end to end; confirm no test asserts
      the old implicit-Cliente-Cero behavior
- [ ] 5.2 `grep -rn "resolve_cliente_cero_tenant_id" apps/backend/tests` — confirm each match
      is an intentional explicit-resolution test, not a leftover assumption

## 6. Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 6.1 Capture pre-test baseline: `SELECT tenant_id, count(*) FROM approval_queue GROUP BY
      1` (expect the single Cliente Cero group, count 6 — from Task 0.3)
- [ ] 6.2 Run targeted tests:
      `pytest apps/backend/tests/test_tenant_scope_resolution.py apps/backend/tests/test_tenant_stamping.py apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py -v`
- [ ] 6.3 Run full backend suite: `pytest apps/backend/tests` (+ `bash init.sh`)
- [ ] 6.4 Re-run the Task 6.1 query — confirm unchanged (unit tests use mocks; any DB-gated
      test in 4.5 must clean up its own throwaway tenants)
- [ ] 6.5 Create report
      `openspec/changes/approval-queue-tenant-scoping/reports/YYYY-MM-DD-step-6-unit-test-and-db-verification.md`
- [ ] 6.6 Mark this section complete only after 6.3 is green and the report exists

## 7. Manual Endpoint Testing with curl (MANDATORY — AGENT MUST EXECUTE)

- [ ] 7.1 Start the backend locally (`uvicorn main:app --reload` from `apps/backend`,
      `AUTH_ENFORCED=false` for local staging-identity coverage)
- [ ] 7.2 `GET /api/v1/approval-queue` with no token → verify staging/Cliente-Cero-operator
      response (all rows, `tenant_id` field present)
- [ ] 7.3 `POST /enqueue` with no token (staging) → verify the created row's `tenant_id` =
      Cliente Cero UUID; **restore state**: delete the test row after
- [ ] 7.4 Local test of the tenant-scoped path: construct a request with a forged/local JWT
      resolving to a throwaway tenant (or run the Section 4.1 tests directly, since no real
      Supabase session is available locally) — document which method was used
- [ ] 7.5 `POST /approve` / `POST /reject` happy path + cross-tenant-mismatch path (expect
      "not found"); restore any state changed
- [ ] 7.6 Error cases: missing token with `AUTH_ENFORCED=true` (simulate via env override) →
      401; malformed `decision_id` → existing error handling unchanged
- [ ] 7.7 Document all commands + responses in
      `openspec/changes/approval-queue-tenant-scoping/reports/YYYY-MM-DD-step-7-curl-endpoint-tests.md`

## 8. Migration

- [ ] 8.1 Create `apps/backend/migrations/0033_approval_queue_tenant_not_null.sql` per
      `design.md` (idempotent: safety re-backfill, `DROP DEFAULT`, `SET NOT NULL`)
- [ ] 8.2 Validate: `npm run migrate:test` (or repo-equivalent dry-run)
- [ ] 8.3 **Ask the founder for explicit confirmation before applying to the live database**
      (schema change on a production table)
- [ ] 8.4 Apply migration 0033 to Supabase project `kpynymwghfwshvcvevxq` (only after 8.3)
- [ ] 8.5 Re-run the Task 0.3 / 6.1 verification query — confirm 6 rows, all Cliente Cero,
      column is NOT NULL with no default

## 9. Update Technical Documentation (MANDATORY)

- [ ] 9.1 Update `ARCHITECTURE.md` Decision #13 (or add a note) — approval queue is now
      tenant-scoped; Contexia operator = caller resolved to Cliente Cero's tenant
- [ ] 9.2 Sync `specs/approval-queue/spec.md` into main `openspec/specs/` (via
      `openspec-sync-specs` skill) before archiving
- [ ] 9.3 Note the deferred follow-ups from `design.md` (RLS policy cleanup owned by
      `hermes-multi-tenant-wrapper`; financials refactor to reuse the shared helper) somewhere
      trackable (e.g. a TODO in `hermes-multi-tenant-wrapper/tasks.md` or a new backlog note)

## 10. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 10.1 Merge `feature/approval-queue-tenant-scoping` → `main`; verify
      `git branch --show-current` before every commit (parallel sessions active in the shared
      checkout — this change was developed in an isolated worktree specifically to avoid
      collisions)
- [ ] 10.2 git push to `main` (hand to the founder if the security classifier blocks the push)
- [ ] 10.3 Vercel build green (frontend untouched by this change, verify no regression)
- [ ] 10.4 Railway deploy active on `antigravity-app-production-175a`
- [ ] 10.5 Production verification:
  - `GET /api/v1/approval-queue` with no token → **401** (confirms `AUTH_ENFORCED=true` live)
  - Founder logs into the Búnker → Sell Machine tab: list loads, drafts show `tenant_id` =
    Cliente Cero UUID, approve/reject still work — **this is the riskiest assumption
    (founder's login must resolve to Cliente Cero via `user_tenants`); if it 403s, the fix is
    a `user_tenants` row, not code**
  - A provisioned client login (migration 0029/0032 users) → `GET /approval-queue` returns
    only that tenant's rows (currently: empty)
  - Trigger one internal enqueue path (e.g. a sell-machine or social-ops flow) → new row
    carries the real Cliente Cero UUID, not zeros/NULL
  - Supabase: `SELECT count(*) FROM approval_queue WHERE tenant_id IS NULL` → 0; column
    reports NOT NULL, no default
  - Railway logs: no NOT NULL violations or 500s on approval-queue routes
- [ ] 10.6 Create report:
      `openspec/changes/approval-queue-tenant-scoping/reports/YYYY-MM-DD-deployment.md`

## 11. Archive

- [ ] 11.1 Confirm all sections above are `[x]` and Stage 10 verification is documented
- [ ] 11.2 Archive via `openspec-archive-change` skill
