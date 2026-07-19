## 1. Setup + schema verification

- [x] 1.1 Create branch `feature/hermes-manus-execution-bridge`.
- [x] 1.2 Re-confirm live schema for `executor_outbox`/`approval_queue`/`tenants` via Supabase MCP
      `execute_sql` (already done during proposal — re-verify no drift before writing DDL).
- [x] 1.3 Re-confirm `ApprovalQueueService.list_drafts`/`approve_draft`'s exact signatures by
      reading the live source directly (no guessing at return shapes).

## 2. Migration — `operator_tasks` table

- [x] 2.1 Write a failing schema test (`test_operator_tasks_schema.py`, mirroring
      `test_crm_b2b_schema.py`'s idiom) asserting the table/columns/constraints exist. Confirmed
      it cannot pass locally (no Supabase creds in this shell, same as the CRM precedent) — real
      verification done directly via Supabase MCP (2.3/2.4).
- [x] 2.2 Authored `apps/backend/migrations/0024_operator_tasks.sql`: `operator_tasks(id uuid PK,
      tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, task_type text NOT NULL
      CHECK (task_type IN ('post_content','run_ads_ab','research','metrics_pull',
      'external_integration','generate_doc')), status text NOT NULL DEFAULT 'pending' CHECK
      (status IN ('pending','dispatched','completed','failed')), payload jsonb NOT NULL DEFAULT
      '{}', result jsonb, created_at/updated_at timestamptz)`. Admin-only RLS using the live `role`
      enum (same pattern as `0020`/`0022`), reuse `update_crm_b2b_updated_at()` trigger, idempotent
      DDL (`IF NOT EXISTS`, `DROP POLICY IF EXISTS ... ; CREATE POLICY ...`), closes with
      `SELECT '✅ …' AS status;`.
- [x] 2.3 Applied via Supabase MCP `apply_migration`; re-applied once via `execute_sql` — no errors,
      idempotent.
- [x] 2.4 Verified live via direct SQL: invalid `task_type` rejected with `23514 check_violation`;
      valid insert defaults `status='pending'`; test row cleaned up.

## 3. Service layer — TDD

- [x] 3.1 Wrote `apps/backend/tests/test_operator_task_service.py`: `create_task` (rejects
      `post_content`/`run_ads_ab` returning `(False, None, error)`; accepts the 4 read-only types),
      `list_pending_tasks`, `mark_dispatched` (pending→dispatched succeeds; any other current
      status returns an error), `report_result` (dispatched→completed/failed succeeds;
      pending→result returns an error), `dispatch_campaign_package` (reads an approved
      `campaign_package` decision via a mocked `ApprovalQueueService.list_drafts`, creates a
      `post_content` task with `payload.source_decision_id`; rejects if the decision isn't
      `approved` or isn't `campaign_package` or doesn't exist). Confirmed failing (module didn't
      exist), then fixed a test-helper bug (MagicMock attribute misuse) before all passed.
- [x] 3.2 Authored `apps/backend/services/operator_task_service.py` implementing all functions
      above (tuple `(success, row, error)` return pattern for mutating ops, consistent with
      `ApprovalQueueService`), Supabase-preferred pattern consistent with `crm_service.py`. Does
      NOT modify `approval_queue_service.py` — only reads from it via `list_drafts`.
- [x] 3.3 11/11 new service tests green. Full targeted suite (61 tests: Sell Machine + CRM +
      operator task) green, zero regression.

## 4. Endpoints — TDD

- [x] 4.1 Wrote `test_operator_task_endpoints.py` (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`, matching `test_sell_machine_endpoints.py`'s idiom)
      for all 5 routes: `GET /tasks/pending`, `POST /tasks` (400 on side-effecting types), `POST
      /campaigns/{id}/dispatch` (200/400/404), `POST /tasks/{id}/status` (200/404/409), `POST
      /tasks/{id}/result` (200/409). Confirmed failing (routes didn't exist).
- [x] 4.2 Added the 5 routes to `apps/backend/presentation/sell_machine_endpoints.py` (extending
      the existing file/flag rather than a new module, since they share `SELL_MACHINE_CANONICAL`
      and the same router prefix). No new flag added to `config.py`. Added a `_raise_for_error`
      helper mapping service error strings to 404 (not found) / 409 (invalid transition) / 400
      (everything else, incl. rejected side-effecting task_type).
- [x] 4.3 11/11 new endpoint tests green. Full targeted suite (72 tests: operator task + Sell
      Machine + CRM) green, zero regression despite touching a shared file.

## 5. Verify + DB state (MANDATORY before Stage 11)

- [x] 5.1 Ran the full targeted suite: 72/72 green (22 new + 50 pre-existing, zero regression).
      Confirmed via `git status --short` that no `contexia-app/` files were touched — no sw.js
      bump/rebuild-sync needed for this change's Stage 11.
- [x] 5.2 Confirmed live in Supabase (via MCP, direct SQL simulation pre-deploy): created one task
      of each read-only `task_type`, all landed `status='pending'`; simulated dispatching the real
      approved `campaign_package` (`7b4439c3-ba70-4490-bd0b-3fcd412aac20`, still `approved` in
      production) into a `post_content` task with `payload.source_decision_id` correctly set. All
      verification rows cleaned up afterward.
- [x] 5.3 Wrote `openspec/changes/hermes-manus-execution-bridge/reports/2026-07-19-step5-verification.md`.

## 6. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 6.1 Committed backend changes on `feature/hermes-manus-execution-bridge` (`d7b830a`),
      referencing this change id.
- [x] 6.2 Fast-forward merged to `main` (no divergence, confirmed via `git fetch` + `git log
      origin/main` first) and pushed.
- [x] 6.3 Railway deploy `ef9dc1d3-b611-4b3d-a048-a90b0e38318e` reached `SUCCESS`. Confirmed via
      `git status --short` before committing that no `contexia-app/` files were touched — no sw.js
      bump/rebuild-sync needed.
- [x] 6.4 Confirmed live post-deploy: `GET /api/v1/sell-machine/tasks/pending` returned `200 []`
      (took ~10-12 min cold start, longer than prior deploys but no crash in logs — noted in the
      deployment report).
- [x] 6.5 Full live smoke test via curl against production: created a `research` task (pending) →
      confirmed in `/tasks/pending` → marked `dispatched` (200) → re-dispatch correctly rejected
      (409) → reported a `completed` result (200) → dispatched the real approved
      `campaign_package` `7b4439c3-...` into a `post_content` task with `payload.source_decision_id`
      set (200) → dispatching an unknown decision correctly rejected (404) → creating
      `post_content` directly correctly rejected (400). Both resulting rows confirmed via direct
      Supabase SQL.
- [x] 6.6 Created deployment report at
      `openspec/changes/hermes-manus-execution-bridge/reports/2026-07-19-deployment.md`, including
      all accepted-risk notes from design.md.

## 7. Archive

- [x] 7.1 Sync the `hermes-manus-execution-bridge` capability into `openspec/specs/` (using
      `git mv` for the archive move, per the process fix established after Change A's tree-drift
      incident) and archive this change once Stage 11 is confirmed complete and verified live.
