# Review — task hermes-task-queue-tenant-scoping

**Verdict:** APPROVED

## Scope reviewed

`git diff main..feature/hermes-task-queue-tenant-scoping --stat` (19 files, +1625/-34):
`apps/backend/config.py`, `apps/backend/core/tenant_context.py`,
`apps/backend/presentation/sell_machine_endpoints.py`,
`apps/backend/services/operator_task_service.py`, 3 test files, `AGENTES.md`,
`openspec/specs/bunker-pwa-auth/spec.md`, `feature_list.json`, plus OpenSpec change artifacts
(proposal/design/tasks/spec/reports) and `progress/` files. No `.claude/` or `.cursor/` files
touched — symlink integrity confirmed clean.

## Spec conformance (specs/hermes-manus-execution-bridge/spec.md delta)

Every MODIFIED/ADDED requirement and scenario is implemented exactly as specified, verified by
reading the actual diffs (not just tasks.md checkmarks):

- `list_pending_tasks()` (operator_task_service.py:88-102): explicit projection
  `"id, tenant_id, task_type, payload, status, created_at"` (not `select("*")`), optional
  `tenant_id` filter applied only via `.eq("tenant_id", ...)` when passed.
- `create_task()` (operator_task_service.py:36-85): explicit `tenant_id` validated via
  `tenant_exists`, rejected with `"tenant {id} not found"` (maps to 404 via `_raise_for_error`
  substring match on "not found") when unknown, resolver never called. Omitted `tenant_id` falls
  back to Cliente Cero + `logger.warning`. Omitted plus resolver returns `None` gives an explicit
  rejection, no insert. All three branches correctly distinguished, matching spec scenarios
  exactly.

- `require_hermes_bridge_token` (sell_machine_endpoints.py:44-55): reads
  `settings.HERMES_BRIDGE_TOKEN` at call time (inside the function body, not captured at
  import/module load), no-op when unset, `hmac.compare_digest` bearer check, 401 on
  missing/malformed/mismatched header.
- `dispatch_campaign_package()` (operator_task_service.py:174-212): derives `tenant_id` from
  `getattr(decision, "tenant_id", None)`; falls back to Cliente Cero + warning only when falsy.
  `ApprovalDecision.tenant_id` genuinely exists on `main` today (`models/approval_decisions.py:44`,
  from the already-merged `hermes-multi-tenant-wrapper` change) — this change's dependency claim
  is real, not aspirational.
- Attached via `Depends(...)` to exactly the 5 operator-task routes (`/tasks/pending`, `/tasks`,
  `/campaigns/{id}/dispatch`, `/tasks/{id}/status`, `/tasks/{id}/result`) — confirmed by diff, no
  other routes in the file gained this dependency.
- The 4 mutating endpoints call `agent_operations_logger.record(..., agent_name="hermes-bridge",
  user_id="machine:hermes", ...)` after a successful service call; the poll endpoint
  (`GET /tasks/pending`) does not — confirmed by diff and by
  `TestAuditRecording::test_list_pending_tasks_does_not_record_audit_entry`.

## Specific checks requested

- `core/tenant_context.py`: `resolve_cliente_cero_tenant_id` untouched (diff shows only an
  addition of `tenant_exists`, zero lines changed in the existing function) — additive-only
  confirmed, does not collide with the concurrent `hermes-multi-tenant-wrapper` change.
- No hardcoded secrets: `HERMES_BRIDGE_TOKEN: Optional[str] = None` in `config.py` — env-only, no
  literal default value anywhere in non-test code (grep across `apps/backend` confirms only the
  `None` default and the two read sites). Test files use obviously-fake literals
  (secret-token, test-token-123) only inside test/monkeypatch scope, never shipped.
- English-only: all touched code/tests/docs are English. Spot-checked operator_task_service.py,
  sell_machine_endpoints.py, tenant_context.py — no stray Spanish.
- `require_hermes_bridge_token` reads settings at call time: confirmed — `expected =
  settings.HERMES_BRIDGE_TOKEN` is the first line inside the function body, and
  `TestHermesBridgeToken` monkeypatches `settings.HERMES_BRIDGE_TOKEN` directly (not the module
  attribute) across 4 scenarios, all green.
- `list_pending_tasks()` explicit projection: confirmed, not `select("*")`.
- `create_task`/`dispatch_campaign_package` branch distinction: confirmed correct — explicit
  invalid tenant returns 404 via `_raise_for_error`; omitted tenant falls back to Cliente Cero
  plus warning; omitted tenant with no Cliente Cero configured gives an explicit error, no insert.
  All three paths have dedicated, meaningful tests (not just checking that no exception is raised).
- Audit logging split (4 mutating vs. 1 poll): confirmed both in code and in TestAuditRecording
  (5 tests, one per endpoint, explicit assert_not_called for the poll endpoint).
- Test coverage / `_fake_decision()` MagicMock truthiness fix: confirmed genuinely fixed for every
  pre-existing test, not just the new ones — `_fake_decision()`'s signature default changed to
  `tenant_id=None` and the body unconditionally sets `decision.tenant_id = tenant_id`
  (test_operator_task_service.py diff), so every existing call site that does not pass an
  explicit `tenant_id` now gets a real `None` rather than a truthy auto-attribute Mock. This is
  the correct fix location (the factory, not each call site), so it cannot regress silently if a
  new test is added later without remembering the trap.
- Symlink integrity: no `.claude/` or `.cursor/` files in the diff — confirmed via
  `git diff main..feature/hermes-task-queue-tenant-scoping -- .claude .cursor` (empty).

## ARCHITECTURE.md conformance

- Decision #1 (Hermes local-only): unaffected — this change only touches the cloud-side backend
  bridge that Hermes polls; no code moves Hermes compute to Railway/cloud.
- Decision #13 (per-tenant scoping): this change directly implements the spirit of #13 for the
  `operator_tasks` queue, which was previously tenant-blind. Correctly distinguishes "no tenant
  resolved" (reject, no data leak) from "explicit Cliente Cero fallback with a logged warning"
  (staging/legacy convenience path) — consistent with the existing Decision #13 pattern for
  `GET /api/v1/financials`.
- No new container or external dependency was introduced (env var only) — no ARCHITECTURE.md
  edit was required, and the implementer correctly verified and documented this (Task 8.3)
  rather than silently skipping it.

## Tests — genuinely run, not trusted blindly

Ran directly (not just read the implementer's report):

    cd apps/backend && python -m pytest tests/test_operator_task_service.py \
      tests/test_operator_task_endpoints.py tests/test_tenant_context.py -v

Result: 47 passed, 0 failed (matches implementer's Step 6 report exactly).

Also ran the full backend suite myself (excluding the 3 modules with a pre-existing,
change-unrelated ModuleNotFoundError collection error, same exclusion the implementer used):

    python -m pytest -q --ignore=tests/test_profile_support.py \
      --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py

Result: 628 passed, 40 failed, 109 skipped — identical counts to the implementer's Step 6
report. Verified by name that all 40 failures are in files this change never touches (Shadow GL
CSV parsing, approval-rules stage acceptance/migration-file-exists checks, wizard endpoints,
centinela alerts endpoint, secure-LLM anonymization, cloud-only model selector) — no new failure
introduced by this change.

Both reports (reports/2026-07-23-step-6-unit-test-and-db-verification.md and
reports/2026-07-23-step-7-curl-testing.md) show real, specific command output (actual PIDs,
actual tracebacks quoting real line numbers/file paths, actual HTTP status/body pairs for all 5
routes across 3 auth states) — not hypothetical or fabricated output. The curl report genuinely
demonstrates: (a) token-unset fail-open behavior (500 credential-gap, not 401) preserved on all
routes, (b) token-set 401 for missing/wrong Authorization header on all 5 routes, and (c)
token-set correct-bearer passes the auth gate and reaches service-layer/DB-credential-gap code on
all 5 routes. This is credible, first-hand evidence, not a fabricated summary.

## RUN_TESTS=1 bash init.sh — NOT genuinely green (repo-wide pre-existing issue)

I ran RUN_TESTS=1 bash init.sh myself. Canon (section 1), harness structure (section 2), and
feature_list.json (section 3) all pass. Section 4 (pytest apps/backend -q, no --ignore)
reported [FAIL] Backend tests failed (exit code 1) — consistent with the same 40 pre-existing,
change-unrelated failures found in my direct run above (init.sh runs the unfiltered suite,
which also collects the 3 known-broken modules as errors).
Separately, I observed test_shadow_gl_stage8_e2e.py spawning repeated nested
"python -m pytest apps/backend/tests/test_shadow_gl_stage8_e2e.py -q" subprocesses roughly every
20-30s for 10+ minutes during the init.sh run (process list confirmed via
Get-CimInstance Win32_Process) — a pre-existing runaway-subprocess condition in a file this
change does not touch, which I had to terminate manually to get a final read. This is a
repo-tooling gap, not something this change introduced or can fix within its own scope.

Because of this, per my instructions, I am leaving tasks.md 10.1/10.2 unchecked — I did not
obtain a genuinely green RUN_TESTS=1 bash init.sh run, and I will not check the box to make it
look otherwise. This should NOT block Stage 11 for this specific change: the change's own tests
are 100% green (47/47), the full-suite delta (40 failed both before and after this change,
identical count/names) shows zero regressions introduced, and the pre-existing failures plus the
runaway-subprocess issue are unrelated, already-documented (implementer's own Step 6 report),
repo-wide conditions that predate this branch.

Recommended CHECKPOINTS.md addition (self-improving loop): init.sh's RUN_TESTS=1 gate
currently runs the unfiltered full backend suite and will report [FAIL] for any change,
regardless of what it touches, as long as these roughly 40 pre-existing failures and the
test_shadow_gl_stage8_e2e.py runaway-subprocess issue remain unfixed. Recommend either (a)
fixing/quarantining those pre-existing failures repo-wide, or (b) evolving init.sh to diff
failure counts/names against a tracked baseline rather than requiring absolute exit-code 0. Until
then, reviewers should independently confirm "no new failures introduced" (as done here) rather
than relying on init.sh's raw exit code alone.

## Checkpoints

- C1 (Setup): [x]
- C2 (Proposal/Design/Spec/Tasks): [x]
- C3 (Implementation — code compiles, existing+new tests pass, docs-sync): [x]
- C4 (Review — no hardcoded secrets, no FIXME/HACK without issue, security review): [x]
- C5 (Deploy readiness — Stage 11 not yet run, out of scope for this review): [ ] — N/A for this
  review pass; Stage 11 (tasks 9.1-9.5) is separate from this Review Gate (task 10)
- Docs-sync: no container/external-dependency change occurred (env var only), so ARCHITECTURE.md
  was correctly left untouched (verified, not just asserted, by the implementer's Task 8.3 note
  and by my own re-check of the Decisiones list)

## Required changes

None for the code under review. One process note (not a code change) for the founder / next
session self-improving loop: reconcile init.sh's RUN_TESTS=1 gate with the repo's actual
pre-existing test-failure baseline per the recommendation above.
