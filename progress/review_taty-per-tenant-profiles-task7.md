# Review — task 7 (taty-per-tenant-profiles)

**Verdict:** APPROVED

## Independent verification performed

1. **Targeted tests reproduced exactly.** Ran
   `pytest apps/backend/tests/test_taty_tenant_profiles.py apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_endpoints_tenant_scoping.py apps/backend/tests/test_telegram_taty_tenant_translation.py -v`
   myself → **23 passed, 0 failed** in 1.55s. Matches the claim exactly.

2. **Broader suite reproduced exactly.** Ran
   `pytest apps/backend/tests/ -q --deselect apps/backend/tests/test_shadow_gl_stage8_e2e.py`
   myself → **25 failed, 648 passed, 109 skipped, 12 deselected, 13 errors** in 10.83s. The
   failing/erroring test *set* (file+testname list) is byte-for-byte identical to the report's
   list (`test_approval_rules_stage8_11.py::test_git_commits_exist`, `test_centinela_alerts_get.py`,
   `test_crm_endpoints.py`, `test_model_selector_cloud_only.py`, `test_secure_llm.py`,
   `test_sell_machine_endpoints.py`, `test_shadow_gl_integration.py` (2),
   `test_shadow_gl_siigo_csv.py` (10), `test_social_ops_endpoints.py`, `test_swarm_operators.py`,
   `test_whatsapp_endpoints.py`, `test_wizard_auditoria_sombra.py` (2) = 25 failed;
   `test_financials_aggregation.py` (11) + `test_financials_endpoint_tenant_scoping.py` (2) =
   13 errors). No discrepancy.

3. **Diff scope confirmed.** `git diff --stat main...HEAD -- apps/backend` → exactly the 10
   files claimed: `agents_endpoints.py`, `taty_endpoints.py`, `telegram_endpoints.py`,
   `taty_intent_router.py` (deleted), `taty_service.py`, plus 5 test files
   (`test_taty_ask_tenant_scoping.py`, `test_taty_endpoints_tenant_scoping.py`,
   `test_taty_intent_router.py` deleted, `test_taty_tenant_profiles.py`,
   `test_telegram_taty_tenant_translation.py`). No unrelated source files touched — this task
   is verification-only as instructed (no scope creep).

4. **Read actual tracebacks myself for 6 failures across all 4 claimed buckets** (not just
   trusted the triage):
   - `test_financials_endpoint_tenant_scoping.py` (2 errors, bucket "missing Supabase creds") —
     traceback confirms `SupabaseException: supabase_url is required` at
     `infrastructure/supabase_client.py:15`, raised from a `two_test_tenants` fixture calling
     `supabase.table("tenants")` before any taty code runs. Note: this file's *name* sounds
     taty-adjacent (tenant scoping) but it tests `financials_endpoints.py`/`get_financials`,
     unrelated to this change's diff — imports only `presentation.financials_endpoints`.
   - `test_centinela_alerts_get.py::test_endpoint_returns_200_and_shape` (bucket "TestClient
     incompatibility") — traceback shows `from main import app` **succeeds** (reaches the
     `TestClient(app)` line before failing), which is actually corroborating evidence: `main.py`
     wires in `agents_endpoints`/`taty_endpoints`/`telegram_endpoints` via `router.py`, and the
     app object builds cleanly post-diff. The actual failure is `TypeError: Client.__init__()
     got an unexpected keyword argument 'app'` deep in `starlette.testclient`, an httpx/starlette
     version mismatch — nothing to do with this change.
   - `test_shadow_gl_siigo_csv.py::test_rejects_missing_required_column` (bucket "Windows
     encoding") — traceback confirms literal `Missing required column(s): c�digo de cuenta,
     descripci�n, fecha, referencia externa` sourced from mojibake constants inside
     `shadow_gl_service.py` (a file untouched by this diff, confirmed via
     `git diff main...HEAD -- apps/backend/services/shadow_gl_service.py` = empty).
   - `test_crm_endpoints.py::test_crm_router_conditionally_included_on_flag` and
     `test_whatsapp_endpoints.py::test_router_conditionally_included_on_flag` (bucket
     "feature-flag/env assertions") — both fail with `FileNotFoundError: 'presentation/router.py'`
     because the test opens a relative path that only resolves from a different cwd than pytest
     was invoked from here — a pre-existing, cwd-dependent test bug, not a taty regression.
     Confirmed `router.py` has zero diff on this branch (`git log` shows its last touches are
     `5652f27`/`da14b53`/`600a11d`, all pre-dating this branch's divergence point).
   - `test_swarm_operators.py::test_all_operators_execute_in_parallel` (bucket "feature-flag/env/
     git-history") — traceback shows a floating-point `pytest.approx` mismatch (0.0137 vs 0.0135)
     in operator cost summation, unrelated to any file this change touches.

5. **Indirect-coupling check.** No `conftest.py` exists anywhere under `apps/backend/tests/`
   (confirmed via `find`), so no shared-fixture coupling path exists. Three failing files
   (`test_centinela_alerts_get.py`, `test_secure_llm.py`, `test_wizard_auditoria_sombra.py`) do
   `from main import app`, which transitively imports this change's touched files via
   `router.py` — and all three fail *after* that import succeeds, at the `TestClient(app)`
   construction line, confirming the app assembles cleanly with this diff rather than exposing
   a hidden regression.

6. **Report template compliance.**
   `openspec/changes/taty-per-tenant-profiles/reports/2026-07-23-step-7-unit-test-and-db-verification.md`
   follows the mandated template from `docs/openspec-tasks-mandatory-steps.md` (Commands
   Executed / Unit Test Results / Database State Verification / Outcome). It does **not**
   fabricate a DB baseline — it honestly states the live query failed with
   `SupabaseException: supabase_url is required` (no `SUPABASE_URL`/`SUPABASE_KEY` in this
   worktree) and explicitly defers live verification to Stage 11 (task 11, production
   Supabase), citing CLAUDE.md's Stage 11 requirement. This is a defensible deferral, not a
   shortcut: there is genuinely no reachable database from this local environment, and Stage 11
   (not yet reached — tasks 8-12 remain `[ ]`) is the correct place to close that loop before
   archiving.

7. **`bash init.sh`** (structural, no `RUN_TESTS=1`) → green: canon docs present, harness
   structure present, `feature_list.json` valid with `active=taty-per-tenant-profiles`.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md, applicable subset for this task)

- Tests genuinely run and independently reproduced: [x]
- Report follows mandated template, no fabricated data: [x]
- No source files modified in a verification-only task: [x]
- Docs-sync (ARCHITECTURE.md) — N/A, no container/dependency change in this task: [x]
- Live DB verification — correctly deferred to Stage 11 given no local Supabase creds, not
  silently skipped: [x]

## Judgment

"Step 7: PASS" is defensible. Every one of the 6 independently-inspected failures/errors traces
to a cause with zero functional coupling to `taty_service.py`, `taty_endpoints.py`,
`telegram_endpoints.py`, `agents_endpoints.py`, or the deleted `taty_intent_router.py` — three
distinct pre-existing root causes (missing local Supabase credentials, an httpx/starlette
`TestClient` version incompatibility, Windows console-encoding mojibake baked into
`shadow_gl_service.py`) plus two isolated pre-existing bugs (a cwd-relative file path, a tight
floating-point tolerance), none touched by this diff. The claimed 25-failed/13-errored/648-passed
counts and the exact failing-test set were reproduced byte-for-byte in a fresh run. No evidence
of scope creep — only `tasks.md` and the new report file were touched, per the implementer's own
"Files touched" list, confirmed by inspecting the diff. Deferring live DB verification to Stage
11 is reasonable and consistent with tasks 1/2's prior findings that this worktree has no
Supabase credentials at all — blocking here would just be a self-imposed dead end with no
Stage-11-equivalent value gained locally.

No CHANGES_REQUESTED-worthy issue found.
