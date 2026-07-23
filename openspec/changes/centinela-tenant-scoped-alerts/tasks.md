# Tasks — Centinela Fiscal: Tenant-Scoped Alert Writes and Reads

> Registered as `pending` in `feature_list.json` (this artifacts-only session did not flip
> `active` — `chatwoot-hermes-taty-bridge` remains `in_progress`). A future session picks this up
> under the harness (leader → implementer → reviewer, per `HARNESS.md`), verifies `./init.sh`, and
> works through the stages below in order, TDD per stage (failing test first).

## Stage 0. Setup (MANDATORY — FIRST STEP)
- [ ] 0.1 Create feature branch `feature/centinela-tenant-scoped-alerts` from up-to-date `main`
  (already created for this artifacts-only session; re-verify at implementation start).
- [ ] 0.2 Verify `git branch --show-current` before starting work and before every commit
  (multiple parallel sessions may exist in this checkout).
- [ ] 0.3 Flip `centinela-tenant-scoped-alerts` to `in_progress` in `feature_list.json` (only once
  the prior active change is `done`/`blocked`) and re-run `./init.sh`.

## Stage 1. `core/tenant_context.py` helpers (TDD)
- [ ] 1.1 Failing tests in new `apps/backend/tests/test_tenant_context_helpers.py`:
  - `test_require_tenant_id_returns_value` — passthrough for a valid tenant_id string.
  - `test_require_tenant_id_raises_on_none` — `TenantResolutionError`; message contains the
    `context` argument.
  - `test_require_tenant_id_raises_on_empty_string` — same for `""`.
  - `test_resolve_caller_tenant_uses_resolved_tenant` — returns `resolved_tenant_id`; mock client's
    `table()` is never called.
  - `test_resolve_caller_tenant_staging_resolves_cliente_cero` — staging user dict → queries
    `tenants.is_cliente_cero` via the mock client, returns its id.
  - `test_resolve_caller_tenant_unresolved_returns_none_never_cliente_cero` — non-staging
    authenticated user with no tenant → returns `None`; mock client raises `AssertionError` if its
    `table()` is touched.
- [ ] 1.2 Implement `TenantResolutionError`, `require_tenant_id`, `resolve_caller_tenant` in
  `core/tenant_context.py`; add `STAGING_USER_ID = _STAGING_USER["id"]` in `core/deps.py`
  (no other change to `deps.py` — JWT/JWKS verification untouched).
- [ ] 1.3 Green: `pytest apps/backend/tests/test_tenant_context_helpers.py -v`.

## Stage 2. `CentinelaService.save_alerts` — fail-loud tenant guard (TDD)
- [ ] 2.1 Rewrite `apps/backend/tests/test_tenant_stamping.py`'s `TestSaveAlertsStampsTenantId`
  class (failing first):
  - `test_save_alerts_stamps_required_tenant_id` (replaces
    `test_stamps_resolved_tenant_id_on_each_alert`) — every inserted row's `tenant_id` equals the
    parameter; no `tenants` lookup performed.
  - `test_save_alerts_raises_without_tenant_id` (new) — `tenant_id=None` and `tenant_id=""` both
    raise `TenantResolutionError`; `insert` is never called.
  - `test_save_alerts_parameter_overrides_per_alert_tenant_id` (replaces
    `test_does_not_override_an_explicitly_provided_tenant_id`, inverted) — a per-alert `tenant_id`
    key is overwritten by the parameter.
  - Leave `TestEnqueueDraftStampsTenantId` untouched; add a comment marking it as the target of the
    sibling `approval-queue-tenant-scoped-writes` change (see design.md §9) — not in scope here.
- [ ] 2.2 Implement: `save_alerts(self, alerts, tenant_id: str)` — guard runs before the
  try/except; unconditional `{**alert, "tenant_id": tenant_id}` stamping; remove the old
  per-alert-key-wins branch; `resolve_cliente_cero_tenant_id()` call removed from this method.
- [ ] 2.3 Green: `pytest apps/backend/tests/test_tenant_stamping.py -v`.

## Stage 3. `get_alerts_for_company` — tenant-scoped reads (TDD)
- [ ] 3.1 Update `apps/backend/tests/test_centinela_alerts_get.py` (failing first): add
  `tenant_id=` to all existing calls; assert `.eq("tenant_id", ...)` appears in the mock query
  chain; add `test_get_alerts_raises_without_tenant_id` (`TenantResolutionError` before any client
  access).
- [ ] 3.2 Implement: `get_alerts_for_company(self, company_id, tenant_id, limit=20, severity=None)`
  — guard + `.eq("tenant_id", tenant_id)` added to the query; demo-profile fallback unchanged.
- [ ] 3.3 Green: `pytest apps/backend/tests/test_centinela_alerts_get.py -v`.

## Stage 4. Resolution poller stamping (TDD)
- [ ] 4.1 Update `apps/backend/tests/test_centinela_resolution_poller.py` (failing first): update
  `_alert_payload` call sites for the new `(company_id, tenant_id, discrepancy)` arity; add
  `test_alert_payload_includes_tenant_id` and `test_poll_raises_on_empty_tenant_id`
  (`TenantResolutionError`).
- [ ] 4.2 Implement: `_alert_payload(company_id, tenant_id, discrepancy)` includes
  `"tenant_id": tenant_id`; `poll_shadow_gl_discrepancies(tenant_id)` calls `require_tenant_id` at
  the top.
- [ ] 4.3 Fix arity fallout in `tests/test_slice2_e2e.py` and `tests/test_maestro_agent_protocol.py`
  (mechanical — pass `tenant_id` at their existing call sites).
- [ ] 4.4 Green: `pytest apps/backend/tests/test_centinela_resolution_poller.py
  apps/backend/tests/test_slice2_e2e.py apps/backend/tests/test_maestro_agent_protocol.py -v`.

## Stage 5. Endpoint auth + 3-branch wiring (TDD)
- [ ] 5.1 New `apps/backend/tests/test_centinela_endpoint_tenant_scoping.py`, mock tier (mirrors
  `test_financials_endpoint_tenant_scoping.py`'s monkeypatched-resolver style; direct function
  calls with fake user dicts — failing first):
  - `test_post_evaluate_saves_with_resolved_tenant`
  - `test_post_evaluate_staging_saves_with_explicit_cliente_cero`
  - `test_post_evaluate_authenticated_unresolved_skips_save` (asserts `save_alerts` never called;
    `saved_alert_ids == []`; `save_skipped_reason == "tenant_unresolved"`; Cliente Cero resolver
    monkeypatched to raise `AssertionError` if touched)
  - `test_post_evaluate_respects_save_alerts_false` (regression: no save even with resolved tenant)
  - `test_get_alerts_filters_by_caller_tenant`
  - `test_get_alerts_authenticated_unresolved_returns_empty_never_cliente_cero`
- [ ] 5.2 Implement: both endpoints in `presentation/centinela_endpoints.py` gain
  `user: dict = Depends(get_current_user)`; tenant resolved via `resolve_caller_tenant` before
  calling into the service (not inside the generic try/except); add
  `CentinelaEvaluateResponse.save_skipped_reason: Optional[str]`.
- [ ] 5.3 Green: `pytest apps/backend/tests/test_centinela_endpoint_tenant_scoping.py -v`.

## Stage 6. Pulso Diario / Radar reader fixes (TDD)
- [ ] 6.1 Update `apps/backend/tests/test_radar.py` (failing first): assert the alerts query
  includes `.eq("tenant_id", tenant_id)`.
- [ ] 6.2 Implement: `radar_service.py` adds the tenant filter (tenant already in hand at that call
  site).
- [ ] 6.3 New/updated test for `pulso_diario_service.py` (failing first, in `test_slice2_e2e.py` or
  a new `test_pulso_diario_tenant_fix.py`): asserts the query resolves
  `tenants.id → tenants.company_id` before filtering, AND filters by `tenant_id`.
- [ ] 6.4 Implement: `pulso_diario_service.py`'s alert-count query fixed (was
  `.eq("company_id", tenant_id)` — a bug that always matched nothing); now resolves the real
  `company_id` and filters both columns.
- [ ] 6.5 Green: `pytest apps/backend/tests/test_radar.py <pulso-diario-test-file> -v`.

## Stage 7. Integration scoping tests (env-gated)
- [ ] 7.1 New hermetic two-tenant fixture in
  `test_centinela_endpoint_tenant_scoping.py` (or a companion file), following the
  `test_financials_endpoint_tenant_scoping.py` pattern (disposable `tenants` rows, teardown
  deletes `centinela_alerts` then `tenants`), gated
  `@pytest.mark.skipif(not (os.getenv("RUN_CENTINELA_TENANT") and
  os.getenv("SUPABASE_SERVICE_ROLE_KEY")), reason=...)`.
- [ ] 7.2 `test_two_tenants_alerts_do_not_leak` — alert saved under tenant A with a shared
  `company_id`; tenant B's read is empty; tenant A's read shows it.
- [ ] 7.3 `test_saved_alert_row_has_correct_tenant_id` — DB row's `tenant_id` equals tenant A's
  UUID, not Cliente Cero's.
- [ ] 7.4 Run once with `RUN_CENTINELA_TENANT=1` if `SUPABASE_SERVICE_ROLE_KEY` is available
  locally; otherwise document the skip explicitly in the Stage 10 report (local `.env` currently
  has no service-role key).

## Stage 8. Migration 0033 — proposed backfill (write only, do NOT apply)
- [ ] 8.1 Create `apps/backend/migrations/0033_rescope_centinela_alerts_tenant.sql` per design.md
  §7 (header `-- STATUS: PROPOSED — DO NOT APPLY without founder approval`, audit query, ambiguity
  check, idempotent `UPDATE`, verify query).
- [ ] 8.2 **Explicit gate: do not run this migration against production or any live database in
  this task.** Applying it is a separate founder decision (may be run manually in the Supabase SQL
  editor, per the established pattern for data-mutating migrations in this repo).

## Stage 9. Review and Update Existing Unit Tests (MANDATORY)
- [ ] 9.1 Sweep the full `apps/backend/tests/` tree for any remaining references to the old
  `save_alerts(alerts)` / `get_alerts_for_company(company_id, ...)` / `_alert_payload(company_id,
  discrepancy)` signatures and update them.
- [ ] 9.2 Full targeted run: `pytest apps/backend/tests/test_tenant_context_helpers.py
  apps/backend/tests/test_tenant_stamping.py apps/backend/tests/test_centinela_alerts_get.py
  apps/backend/tests/test_centinela_resolution_poller.py
  apps/backend/tests/test_centinela_endpoint_tenant_scoping.py apps/backend/tests/test_radar.py
  apps/backend/tests/test_slice2_e2e.py apps/backend/tests/test_maestro_agent_protocol.py -v`
  — confirm no regressions.

## Stage 10. Run Unit Tests and Verify Database State (MANDATORY)
- [ ] 10.1 Capture pre-test baseline: `centinela_alerts` row count total and per-tenant (Cliente
  Cero vs. others) via a read-only query.
- [ ] 10.2 Run the Stage 9.2 targeted suite; record pass/fail/skipped counts and runtime.
- [ ] 10.3 Run the broader backend suite (`pytest apps/backend -q`) and record the summary.
- [ ] 10.4 Re-check `centinela_alerts` counts post-run; restore any state mutated by
  non-hermetic tests (the Stage 7 fixture already self-cleans; verify no residual rows).
- [ ] 10.5 Create report:
  `openspec/changes/centinela-tenant-scoped-alerts/reports/YYYY-MM-DD-step-10-unit-test-and-db-verification.md`
  (template per `docs/openspec-tasks-mandatory-steps.md`), explicitly calling out the Pulso
  alert-count change (0 → real numbers, §6 of design.md) so it isn't read as a regression.
- [ ] 10.6 Mark this stage complete only after the report exists and tests pass (or documented
  exceptions, e.g. Stage 7 skipped locally for lack of `SUPABASE_SERVICE_ROLE_KEY`).

## Stage 11-A. Manual Endpoint Testing with curl (MANDATORY — AGENT MUST EXECUTE)
- [ ] 11a.1 Start the backend locally; confirm `AUTH_ENFORCED` value.
- [ ] 11a.2 `POST /api/v1/centinela/evaluate` tokenless (staging identity path, local
  `AUTH_ENFORCED=False`): verify alerts save under the explicitly-resolved Cliente Cero tenant;
  delete the created test rows afterward to restore state.
- [ ] 11a.3 `POST /api/v1/centinela/evaluate` with `"save_alerts": false`: verify no rows are
  created.
- [ ] 11a.4 `GET /api/v1/centinela/alerts/{company_id}` tokenless: verify Cliente-Cero-scoped
  results only.
- [ ] 11a.5 Simulate `AUTH_ENFORCED=True` (env override) and repeat both calls tokenless: verify
  `401`.
- [ ] 11a.6 Document all commands + responses; confirm DB state restored (11a.2's rows deleted).

## Stage 12. Update Technical Documentation (MANDATORY)
- [ ] 12.1 Update the tokenless curl examples in `specs/T5-CENTINELA-E2E-TESTS.md` and the
  `specs/E2E-TESTING-*` docs that hit `/centinela/evaluate` / `/centinela/alerts` to include an
  auth header (or an explicit "requires `AUTH_ENFORCED=False`" note for local runs).
- [ ] 12.2 Extend `ARCHITECTURE.md` **Decisión #13** (append, do not create a new numbered
  decision — same principle, new surface) with:

  > **Extensión (centinela-tenant-scoped-alerts):** el mismo patrón de 3 ramas aplica a Centinela —
  > `POST /api/v1/centinela/evaluate` y `GET /api/v1/centinela/alerts/{company_id}` resuelven el
  > tenant del llamador vía `core/tenant_context.py::resolve_caller_tenant()`;
  > `CentinelaService.save_alerts()` exige `tenant_id` explícito y lanza `TenantResolutionError` si
  > falta (fail-loud — Cliente Cero jamás se estampa por defecto). Un cliente autenticado sin
  > tenant resuelto puede evaluar pero **no persiste** alertas
  > (`save_skipped_reason="tenant_unresolved"`) y lee una lista vacía. Los helpers
  > `require_tenant_id`/`resolve_caller_tenant` son el contrato reusable para Approval Queue y la
  > cola Hermes.

## Stage 13. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: `main`
- Frontend URL: https://contexia.online/app/bunker (no frontend change in this delta; verify no
  regression)
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 13.1 git commit + push to main (via PR from `feature/centinela-tenant-scoped-alerts`).
- [ ] 13.2 Vercel build complete (green ✅) — no frontend surface changed, but confirm the build
  still passes.
- [ ] 13.3 Railway deploy active — confirm via `/api/v1/health` + deployment logs.
- [ ] 13.4 Production URL: live smoke of both endpoints. Expected pass condition: tokenless
  requests now return `401` (production has `AUTH_ENFORCED=True`) — this is the fix working, not a
  failure. With a real client bearer token, `/evaluate` and `/alerts` return tenant-scoped results.
- [ ] 13.5 Create report: `openspec/changes/centinela-tenant-scoped-alerts/reports/YYYY-MM-DD-deployment.md`.
- [ ] 13.6 Sync delta spec into main specs (`opsx:sync` / `openspec-sync-specs`) before archiving.
- [ ] 13.7 Archive the change (`opsx:archive` / `openspec-archive-change`) only after 13.1–13.6 are
  complete and confirmed live.

## Harness note

Implementation runs under `HARNESS.md`'s leader → implementer → reviewer loop: the leader reads
this file plus the canon, delegates one stage at a time to the implementer (TDD, writes
`progress/impl_<stage-id>.md`), and the reviewer validates against `ARCHITECTURE.md` +
`DEPLOYMENT_STAGE/CHECKPOINTS.md` before any stage is marked done (`progress/review_<stage-id>.md`).
