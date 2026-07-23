# Tasks — Centinela Fiscal: Tenant-Scoped Alert Writes and Reads

> Registered as `pending` in `feature_list.json` (this artifacts-only session did not flip
> `active` — `chatwoot-hermes-taty-bridge` remains `in_progress`). A future session picks this up
> under the harness (leader → implementer → reviewer, per `HARNESS.md`), verifies `./init.sh`, and
> works through the stages below in order, TDD per stage (failing test first).

## Stage 0. Setup (MANDATORY — FIRST STEP)
- [x] 0.1 Feature branch `feature/centinela-tenant-scoped-alerts` — implemented in an isolated
  `git worktree` (`antigravity-app-centinela-impl`), not the shared main checkout, after a real
  cross-session race there during the artifacts commit (recovered via cherry-pick; see prior
  session notes). `./init.sh` green throughout.
- [x] 0.2 Verified `git branch --show-current` before each commit.
- [ ] 0.3 **Not flipped** — `feature_list.json`'s `active` slot is occupied by
  `hermes-task-queue-tenant-scoping` (`in_progress`), owned by a concurrent session. Implementation
  proceeded in the isolated worktree without touching the shared `feature_list.json`'s `active`
  pointer, per explicit founder instruction ("implementar ahora" while leaving the slot alone).
  This stays `pending` in `feature_list.json` until the founder reconciles the one-change-at-a-time
  invariant across concurrent sessions.

## Stage 1. `core/tenant_context.py` helpers (TDD) — DONE (commit `5964bc3`)
- [x] 1.1 Failing tests in new `apps/backend/tests/test_tenant_context_helpers.py`:
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
- [x] 1.2 Implement `TenantResolutionError`, `require_tenant_id`, `resolve_caller_tenant` in
  `core/tenant_context.py`; add `STAGING_USER_ID = _STAGING_USER["id"]` in `core/deps.py`
  (no other change to `deps.py` — JWT/JWKS verification untouched).
- [x] 1.3 Green: 6/6 passed.

## Stage 2. `CentinelaService.save_alerts` — fail-loud tenant guard (TDD) — DONE (commit `52b1494`)
- [x] 2.1 Rewrite `apps/backend/tests/test_tenant_stamping.py`'s `TestSaveAlertsStampsTenantId`
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
- [x] 2.2 Implement: `save_alerts(self, alerts, tenant_id: str)` — guard runs before the
  try/except; unconditional `{**alert, "tenant_id": tenant_id}` stamping; remove the old
  per-alert-key-wins branch; `resolve_cliente_cero_tenant_id()` call removed from this method.
- [x] 2.3 Green: 5/5 passed (both `TestSaveAlertsStampsTenantId` and untouched
  `TestEnqueueDraftStampsTenantId`).

## Stage 3. `get_alerts_for_company` — tenant-scoped reads (TDD) — DONE (commit `a4160ca`)
- [x] 3.1 Update `apps/backend/tests/test_centinela_alerts_get.py` (failing first): add
  `tenant_id=` to all existing calls; assert `.eq("tenant_id", ...)` appears in the mock query
  chain; add `test_get_alerts_raises_without_tenant_id` (`TenantResolutionError` before any client
  access).
- [x] 3.2 Implement: `get_alerts_for_company(self, company_id, tenant_id, limit=20, severity=None)`
  — guard + `.eq("tenant_id", tenant_id)` added to the query; demo-profile fallback unchanged.
- [x] 3.3 Green: 4/4 service-level tests passed. **Deviation noted**:
  `TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape` (HTTP-level smoke test via
  `TestClient`) fails in this environment — confirmed pre-existing via `git stash` comparison
  against the unmodified baseline (`httpx`/`starlette` `TestClient` version incompatibility,
  unrelated to this change). See Stage 10 report.

## Stage 4. Resolution poller stamping (TDD) — DONE (commit `f035b24`)
- [x] 4.1 Update `apps/backend/tests/test_centinela_resolution_poller.py` (failing first): update
  `_alert_payload` call sites for the new `(company_id, tenant_id, discrepancy)` arity; add
  `test_alert_payload_includes_tenant_id` and `test_poll_raises_on_empty_tenant_id`
  (`TenantResolutionError`). **Deviation**: the file's pre-existing `autouse=True` fixture was
  module-level, which broke the new pure-mock tests (tried to connect to real Supabase) — nested
  it inside `TestPollShadowGlDiscrepancies` instead of leaving it module-scoped.
- [x] 4.2 Implement: `_alert_payload(company_id, tenant_id, discrepancy)` includes
  `"tenant_id": tenant_id`; `poll_shadow_gl_discrepancies(tenant_id)` calls `require_tenant_id` at
  the top.
- [x] 4.3 No arity fallout found in `tests/test_slice2_e2e.py` /
  `tests/test_maestro_agent_protocol.py` — `poll_shadow_gl_discrepancies(tenant_id)`'s external
  signature is unchanged (only its internal call to `_alert_payload` gained a parameter), so no
  caller needed updating. Verified by running both files: 9 passed, 1 skipped (unrelated gate).
- [x] 4.4 Green: 2 passed, 2 correctly skipped (no `RUN_SHADOW_GL=1`).

## Stage 5. Endpoint auth + 3-branch wiring (TDD) — DONE (commit `401b51d`)
- [x] 5.1 New `apps/backend/tests/test_centinela_endpoint_tenant_scoping.py`, mock tier (mirrors
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
- [x] 5.2 Implement: both endpoints in `presentation/centinela_endpoints.py` gain
  `user: dict = Depends(get_current_user)`; tenant resolved via `resolve_caller_tenant` before
  calling into the service (not inside the generic try/except); add
  `CentinelaEvaluateResponse.save_skipped_reason: Optional[str]`.
- [x] 5.3 Green: 6/6 passed.

## Stage 6. Pulso Diario / Radar reader fixes (TDD) — DONE (commit `b90d3ea`)
- [x] 6.1 **Deviation**: `test_radar.py` is entirely integration-gated (`RUN_SHADOW_GL`), no
  mock-level tests existed to update in place. Instead: extracted a small pure function
  `_count_centinela_alerts_this_month(supabase, tenant_id, month_start, today)` out of
  `calculate_risk_score`'s inline factor-3 block, and wrote a new
  `test_radar_alert_count_tenant_scoping.py` (2 pure-mock tests, no Supabase needed) asserting
  `.eq("tenant_id", ...)` alongside the existing `.eq("company_id", ...)`.
- [x] 6.2 Implement: `radar_service.py`'s alert-count query now filters by tenant_id (company_id
  resolution was already correct).
- [x] 6.3 **Deviation**: same pattern for `pulso_diario_service.py` — extracted
  `_count_alerts_generated(supabase, tenant_id, date)`, new
  `test_pulso_diario_alert_count_tenant_scoping.py` (2 pure-mock tests) asserting company_id
  resolution + tenant_id filter, and a regression guard against the old bug's exact broken filter.
- [x] 6.4 Implement: fixed the real bug — was `.eq("company_id", tenant_id)` (tenant UUID passed
  into the text company_id column, always matched nothing, so `alerts_generated` was silently
  always 0). Now resolves `tenants.company_id` first (same pattern as
  `centinela_resolution_service._resolve_company_id`) and filters both columns.
- [x] 6.5 Green: 4/4 new tests passed. Confirmed `test_radar.py` / `test_pulso_diario.py` (the
  pre-existing gated integration files) still collect and skip cleanly (10 skipped, 0 errors).

## Stage 7. Integration scoping tests (env-gated) — DONE (commit `34a6ec1`)
- [x] 7.1 New hermetic two-tenant fixture in a new file,
  `tests/test_centinela_tenant_scoping_integration.py` (companion file, not appended to the
  endpoint-scoping test file, to keep the mock and integration tiers cleanly separate), gated
  `@pytest.mark.skipif(not (os.environ.get("RUN_CENTINELA_TENANT") == "1" and
  os.environ.get("SUPABASE_SERVICE_ROLE_KEY")), reason=...)`.
- [x] 7.2 `test_two_tenants_alerts_do_not_leak` — written.
- [x] 7.3 `test_saved_alert_row_has_correct_tenant_id` — written.
- [x] 7.4 **Not run** — local `.env` has no `SUPABASE_SERVICE_ROLE_KEY` (confirmed by direct
  check). Documented in the Stage 10 report; file confirmed to collect and skip cleanly
  (2 skipped, 0 errors).

## Stage 8. Migration 0033 — proposed backfill (write only, do NOT apply) — DONE (commit `cfaad63`)
- [x] 8.1 Created `apps/backend/migrations/0033_rescope_centinela_alerts_tenant.sql` per design.md
  §7 (PROPOSED header, audit query, ambiguity check, verify query). **Extra safety beyond plan**:
  the actual `UPDATE` (Step 1) is additionally commented out in the file itself, not just guarded
  by the header comment — confirmed no automated runner in this repo scans
  `apps/backend/migrations/` to auto-apply files, so this is inert either way, but the comment-out
  is defense-in-depth.
- [x] 8.2 Not applied. No live database was touched.

## Stage 9. Review and Update Existing Unit Tests (MANDATORY) — DONE
- [x] 9.1 Swept `apps/backend/` via `grep` for `get_alerts_for_company(`, `.save_alerts(`,
  `_alert_payload(` — all call sites found already use the new signatures (endpoint, service,
  resolution service, and all test files). No stale references found.
- [x] 9.2 Full targeted run (superset of the planned command, including the new Stage 6/7 test
  files): 36 passed, 15 skipped (all env-gated), 1 failed (pre-existing, unrelated — see Stage 10
  report). No regressions.

## Stage 10. Run Unit Tests and Verify Database State (MANDATORY) — DONE
- [x] 10.1 No live Supabase connection available locally — N/A, documented in the report (nothing
  to baseline since no live writes occur without `SUPABASE_SERVICE_ROLE_KEY`).
- [x] 10.2 Targeted suite run and recorded: 36 passed / 15 skipped / 1 failed, ~14s.
- [x] 10.3 Full backend suite run and recorded (excluding 3 files with pre-existing, unrelated
  `ModuleNotFoundError: apps` collection errors): 612 passed, 40 failed, 111 skipped, 13 errors,
  ~100s. Every failure/error manually reviewed and confirmed pre-existing/unrelated (grepped for
  references to this change's modules).
- [x] 10.4 N/A — no live DB state was mutated (all real-Supabase tests are env-gated and were
  skipped).
- [x] 10.5 Report created:
  `openspec/changes/centinela-tenant-scoped-alerts/reports/2026-07-23-step-10-unit-test-and-db-verification.md`,
  explicitly calling out the Pulso alert-count fix (0 → real numbers) plus an in-session git
  incident (accidental file revert + cross-session stash-pop conflict, both caught and resolved
  without data loss) for full transparency.
- [x] 10.6 Complete — report exists, tests pass modulo documented pre-existing exceptions.

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
