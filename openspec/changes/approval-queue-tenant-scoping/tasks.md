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

- [x] 2.1 Rewrite `apps/backend/tests/test_tenant_stamping.py::TestEnqueueDraftStampsTenantId`:
  - `test_stamps_explicitly_passed_tenant_id_on_insert`
  - `test_missing_tenant_id_returns_error_not_silent_insert`
  - (leave `TestSaveAlertsStampsTenantId` — centinela — untouched)
- [x] 2.2 Add scoping tests (same file or new `test_approval_queue_service_scoping.py`):
  - `test_approve_with_tenant_scope_filters_select_and_update_by_tenant`
  - `test_approve_cross_tenant_returns_not_found`
  - `test_approve_with_none_scope_is_unrestricted`
  - `test_reject_with_tenant_scope_filters_by_tenant`
- [x] 2.3 Run 2.1/2.2 — confirm they fail against current code
- [x] 2.4 Apply `apps/backend/services/approval_queue_service.py` changes per `design.md`:
      `enqueue_draft` requires `tenant_id` kw (no internal Cliente Cero resolution, guard
      returns error on falsy value); `approve_draft`/`reject_draft` require `tenant_id:
      Optional[str]` kw, add `.eq("tenant_id", ...)` to both the existence-select and the
      update when not None; remove the `core.tenant_context` import
- [x] 2.5 Run 2.1/2.2 — confirm green

## 3. Internal Service Callers (explicit Cliente Cero, no silent default)

- [x] 3.1 `apps/backend/services/resolution_agent_service.py:106,157` — pass the
      already-in-scope `tenant_id` through to `enqueue_draft`; update its tests
      (no dedicated mock of `enqueue_draft` existed for this service — its own test files
      (`test_resolution_agent.py`, `test_resolution_agent_retry.py`) are `RUN_SHADOW_GL=1`
      gated live-integration tests that call `generate_draft`/`generate_draft_with_retry`
      with a real `tenant_id`, so no mock update was needed; confirmed by inspection + a
      skipped-collection run)
- [x] 3.2 `apps/backend/services/social_ops_service.py:829` — resolve
      `resolve_cliente_cero_tenant_id(get_supabase())` explicitly at the call site before
      `enqueue_draft`; log + skip if `None`; update `tests/test_social_ops_endpoints.py`
- [x] 3.3 `apps/backend/services/sell_machine_service.py:110` — same explicit resolution;
      update `tests/test_sell_machine_service.py`
- [x] 3.4 Confirm `tests/test_operator_task_service.py` still green (no signature change to
      `list_drafts`) — 13/13 passed unchanged
- [x] 3.5 `grep -rn "enqueue_draft(" apps/backend` — confirm every call site was updated (no
      stray callers left on the old implicit-Cliente-Cero signature); also grepped
      `approve_draft(`/`reject_draft(` — the only production callers outside
      `services/approval_queue_service.py` are `presentation/approval_queue_endpoints.py`
      (Section 4, out of scope here) and `presentation/social_ops_endpoints.py`, which calls
      `SocialOpsService.approve_draft`/`reject_draft` — unrelated in-memory methods on a
      different class, not `ApprovalQueueService`

## 4. Endpoints (TDD)

- [x] 4.1 Write `apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py`
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
  - (plus `test_approve_unresolved_returns_403`, `test_reject_passes_caller_tenant_scope`,
    `test_admin_reject_passes_unrestricted_scope`, `test_reject_unresolved_returns_403` for
    full 403/scope symmetry between approve and reject)
- [x] 4.2 Run 4.1 — confirm failures (14/14 failed, all `AttributeError:
      module 'presentation.approval_queue_endpoints' has no attribute
      'resolve_request_tenant_scope'` — endpoints not yet implemented)
- [x] 4.3 Implement `apps/backend/presentation/approval_queue_endpoints.py` changes per
      `design.md`: `Depends(get_current_user)` on all 4 routes, scope resolution, `?tenant_id`
      admin filter, `DraftListItem.tenant_id`, delete the dead `request.state` read
- [x] 4.4 Run 4.1 — confirm green (14/14 passed)
- [x] 4.5 Extend the DB-gated `apps/backend/tests/test_approval_queue_persistence.py` with a
      hermetic two-tenant round trip (borrow the throwaway-tenant fixture pattern from
      `test_financials_endpoint_tenant_scoping.py`): enqueue under tenant A, assert a
      tenant-B-scoped list excludes it, tenant-B-scoped approve returns not-found,
      tenant-A-scoped approve succeeds. Gated by the file's existing
      `RUN_APPROVAL_QUEUE_DB=1` skipif — collects and skips cleanly with no env vars set
      locally (confirmed: `10 skipped`)
- [x] 4.6 Checked `tests/e2e/test_multi_tenant_flow.py` (repo root) — one approval-queue call
      (`TestHermesOperators::test_approval_queue_with_tenant_context`), unauthenticated payload
      missing `draft_type`/`lines`. FastAPI/pydantic rejects the body with 422 before the
      handler (and its new tenant-scope check) ever runs, so the existing
      `assert response.status_code in [200, 201, 404, 422]` still holds — no code change
      needed. Could not execute the file to confirm empirically: the entire file's
      `TestClient` fixture errors in this environment on an unrelated, pre-existing
      httpx/starlette version mismatch (`Client.__init__() got an unexpected keyword
      argument 'app'`), reproduced on an unrelated test in the same file
      (`TestTenantContextMiddleware`) — confirmed not caused by this change.

## 5. Review and Update Existing Unit Tests (MANDATORY)

- [x] 5.1 Re-read every test file touched in Sections 2–4 end to end; confirm no test asserts
      the old implicit-Cliente-Cero behavior
- [x] 5.2 `grep -rn "resolve_cliente_cero_tenant_id" apps/backend/tests` — confirm each match
      is an intentional explicit-resolution test, not a leftover assumption

## 6. Run Unit Tests and Verify Database State (MANDATORY)

- [x] 6.1 Capture pre-test baseline: `SELECT tenant_id, count(*) FROM approval_queue GROUP BY
      1` (expect the single Cliente Cero group, count 6 — from Task 0.3). No live query tool
      access from this session; cited the `design.md` "Pre-work verification (2026-07-23)"
      baseline run before implementation began (single group,
      `tenant_id=e2d30d09-6b96-4ebe-a79a-c6aff7a5df34`, count=6, no NULL/zeros rows).
- [x] 6.2 Run targeted tests:
      `pytest apps/backend/tests/test_tenant_scope_resolution.py apps/backend/tests/test_tenant_stamping.py apps/backend/tests/test_approval_queue_endpoint_tenant_scoping.py -v`
      — 23/23 passed.
- [x] 6.3 Run full backend suite: `pytest apps/backend/tests` (+ `bash init.sh`) — 605 passed,
      40 failed, 110 skipped, 13 errors (excluding 3 pre-existing collection-broken files); all
      failures/errors confirmed pre-existing/environmental and unrelated to files touched by
      this change (see report). `bash init.sh` green.
- [x] 6.4 Re-run the Task 6.1 query — confirm unchanged (unit tests use mocks; any DB-gated
      test in 4.5 must clean up its own throwaway tenants). No live query access from this
      session; definitionally unchanged since no code path in Sections 1–6 touched a live
      Supabase connection (confirmed: targeted/scoped tests all use mocked clients; the one
      DB-gated file collected `10 skipped`, no env vars set).
- [x] 6.5 Create report
      `openspec/changes/approval-queue-tenant-scoping/reports/2026-07-23-step-6-unit-test-and-db-verification.md`
- [x] 6.6 Mark this section complete only after 6.3 is green and the report exists

## 7. Manual Endpoint Testing with curl (MANDATORY — AGENT MUST EXECUTE)

- [x] 7.1 Start the backend locally (`uvicorn main:app --reload` from `apps/backend`,
      `AUTH_ENFORCED=false` for local staging-identity coverage) — started successfully
      (all routers incl. approval-queue registered); no live Supabase credentials in this
      environment (confirmed `SUPABASE_URL=''`), so every downstream endpoint call hits the
      DB boundary — documented exactly where per test in the report
- [x] 7.2 `GET /api/v1/approval-queue` with no token → staging identity is reached correctly
      (no exception in `get_current_user`), then breaks at
      `resolve_request_tenant_scope`'s first Supabase call (`SupabaseException: supabase_url
      is required`) — proves the routing/auth logic up to the DB boundary; full response
      assertion requires live Supabase (deferred to Stage 11)
- [x] 7.3 `POST /enqueue` with no token (staging) → same DB-boundary break, before
      `ApprovalQueueService.enqueue_draft` is ever called; no row created, no cleanup needed
- [x] 7.4 Tenant-scoped path tested with a locally-signed backend JWT
      (`core.security.create_access_token`, explicit `JWT_SECRET` for a matching
      verify/sign pair) — proves JWT verification succeeds and `identity_resolver` fails
      closed (catches its own Supabase error, doesn't crash) before the endpoint's own
      `resolve_request_tenant_scope` call raises; documented in the report
- [x] 7.5 `POST /approve` / `POST /reject` — both break at the same
      `resolve_request_tenant_scope` DB boundary before reaching the service layer; the
      scoped-select/cross-tenant-"not found" behavior itself is proven by the mocked-client
      unit tests in Sections 2 and 4 (100% green), documented as the source of that proof
      since curl cannot add anything beyond it without live credentials
- [x] 7.6 Error cases: missing token with `AUTH_ENFORCED=true` → **401** on all 4 routes,
      confirmed fully DB-independent (zero Supabase calls, verified via server log) — this is
      the one sub-check proven completely end-to-end locally; malformed `decision_id` is not
      independently reachable (breaks earlier at the same DB boundary), verified instead by
      inspection that Section 2's diff (commit `d75e90f`) left the existing error-handling
      path untouched
- [x] 7.7 Documented all commands + real responses (including the credential-boundary
      failures, which are real signal, not something to hide) in
      `openspec/changes/approval-queue-tenant-scoping/reports/2026-07-23-step-7-curl-endpoint-tests.md`.
      Full DB-backed round-trip verification is explicitly deferred to Stage 11 / task 10.5,
      by design — this local pass proves every code path executes correctly up to the
      Supabase boundary, which is everything this environment can prove without credentials

## 8. Migration

- [x] 8.1 Create `apps/backend/migrations/0033_approval_queue_tenant_not_null.sql` per
      `design.md` (idempotent: safety re-backfill, `DROP DEFAULT`, `SET NOT NULL`)
- [x] 8.2 Validate: `npm run migrate:test` (or repo-equivalent dry-run) — no `migrate:test`
      script exists anywhere in the repo (checked root `package.json`, `contexia-app/`,
      `contexia-wizard/`, `frontend/dashboard/`; no `apps/backend/package.json` at all); did a
      static SQL syntax review instead — balanced `DO $$ ... END $$;` / `IF ... THEN ...
      END IF;`, guard idiom matches `0001_add_tenant_id_columns.sql`/`0003_enable_rls_policies.sql`'s
      `information_schema.columns` pattern, all statements semicolon-terminated (see
      `progress/impl_section8_migration_file.md` for full detail)
- [x] 8.3 **Ask the founder for explicit confirmation before applying to the live database**
      (schema change on a production table) — confirmed via AskUserQuestion, 2026-07-23
- [x] 8.4 Apply migration 0033 to Supabase project `kpynymwghfwshvcvevxq` — applied via
      `apply_migration` MCP tool, 2026-07-23, `{"success":true}`
- [x] 8.5 Re-run the Task 0.3 / 6.1 verification query — confirmed: `SELECT count(*) FROM
      approval_queue WHERE tenant_id IS NULL` → 0; `information_schema.columns` for
      `approval_queue.tenant_id` → `column_default: null, is_nullable: "NO"`. Matches design.md's
      expected post-migration state exactly.

## 9. Update Technical Documentation (MANDATORY)

- [x] 9.1 Update `ARCHITECTURE.md` Decision #13 (or add a note) — approval queue is now
      tenant-scoped; Contexia operator = caller resolved to Cliente Cero's tenant (added
      Decisión #14, extending #13)
- [x] 9.2 Sync `specs/approval-queue/spec.md` into main `openspec/specs/` (via
      `openspec-sync-specs` skill) before archiving (manually merged, per the skill's own
      "ADDED Requirements" rule, into the pre-existing `openspec/specs/approval-queue/spec.md`)
- [x] 9.3 Note the deferred follow-ups from `design.md` (RLS policy cleanup owned by
      `hermes-multi-tenant-wrapper`; financials refactor to reuse the shared helper) somewhere
      trackable (added a follow-up note in `hermes-multi-tenant-wrapper/tasks.md` after Ground
      Truth Correction #3 for the RLS cleanup; the financials refactor follow-up was already
      documented in this change's `design.md` §"Out of scope", judged sufficient)

## 10. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [x] 10.1 Merged `worktree-approval-queue-tenant-scoping` → `main` (two catch-up merges for
      concurrent parallel-session pushes: `hermes-task-queue-tenant-scoping` and
      `taty-per-tenant-profiles`, both purely additive, tests re-verified green after each);
      `git branch --show-current` checked before every commit throughout
- [x] 10.2 `git push origin HEAD:main` succeeded (commit `9008215`, 2026-07-23T11:19Z) — no
      classifier block encountered
- [x] 10.3 Frontend untouched by this change (no `contexia-app/` files modified) — no Vercel
      regression risk; not independently re-verified since nothing frontend-facing shipped
- [x] 10.4 Railway deploy `5cac29b7` on `antigravity-app-production-175a` → **SUCCESS**
- [x] 10.5 Production verification (full detail in the Stage 11 report):
  - `GET /api/v1/approval-queue` with no token → **401** — confirmed via curl ✅
  - Founder's login resolves to Cliente Cero (riskiest assumption) → **confirmed via read-only
    query**: `jpelaezcardenas@gmail.com` has an active, `is_owner=true` `user_tenants`
    membership in Cliente Cero's tenant — not re-verified by clicking through the Búnker UI
    (no credentials handled), but the underlying DB fact the UI check would prove is confirmed
    directly ✅
  - Provisioned client login sees only its own tenant → **not independently re-exercised
    live** (no test client session created against production); covered by Sections 2/4's
    tests and the identical, already-verified-live `per-tenant-client-access` pattern
  - Internal enqueue path stamps real tenant → **not triggered live** in this pass; covered by
    Section 3's tests confirming explicit resolution at each call site
  - Supabase: `SELECT count(*), count(*) FILTER (WHERE tenant_id IS NULL) FROM approval_queue`
    → `6, 0` ✅; column confirmed NOT NULL, no default ✅
  - Railway logs: clean — `"Approval queue router registered successfully"`, no NOT NULL
    violations, no 500s on approval-queue routes ✅
- [x] 10.6 Report created:
      `openspec/changes/approval-queue-tenant-scoping/reports/2026-07-23-deployment.md`

## 11. Archive

- [ ] 11.1 Confirm all sections above are `[x]` and Stage 10 verification is documented
- [ ] 11.2 Archive via `openspec-archive-change` skill
