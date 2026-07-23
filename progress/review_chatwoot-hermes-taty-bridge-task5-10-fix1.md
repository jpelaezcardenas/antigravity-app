# Review — task chatwoot-hermes-taty-bridge (fix1: GET / health check coverage)

**Verdict:** APPROVED

## Scope reviewed
`apps/chatwoot-bridge/tests/test_health.py` (new file) as the sole fix for the one blocking
finding from `progress/review_chatwoot-hermes-taty-bridge-task5-10.md` — zero test coverage
for `GET /` (main.py:108-112).

## Verification

1. **Test is real, not a stub.**
   `tests/test_health.py::TestHealthCheck::test_health_check_succeeds_and_invokes_hermes_liveness_check`:
   - Uses `httpx.ASGITransport(app=main_module.app)` (same in-process pattern as
     `test_webhook_filter.py`) to call `GET /`.
   - Asserts `response.status_code == 200`.
   - Asserts the JSON body matches what `main.py:108-112`'s `health()` handler actually
     returns: `service == "chatwoot-hermes-bridge"`, `status == "ok"`,
     `hermes_models == fake_models` — read directly against main.py, not guessed. Verified
     by reading main.py:108-112 myself: the handler returns exactly
     `{"status": "ok", "service": "chatwoot-hermes-bridge", "hermes_models": models}`.
   - Patches `main_module.hermes_client.check_models` with `AsyncMock` and asserts
     `mock_check_models.assert_awaited_once_with()` — this proves `check_models()` was
     genuinely invoked during the request (the mock is patched onto the actual object the
     handler calls, `hermes_client.check_models()` at main.py:110), not merely present in
     source. If the handler didn't call it, `assert_awaited_once_with()` would fail.

2. **Full suite re-run independently:**
   `cd apps/chatwoot-bridge && python -m pytest tests -v` → **32 passed, 1 warning**
   (the warning is the same pre-existing, unrelated `python_multipart`
   `PendingDeprecationWarning` noted in the prior review). Matches the implementer's report
   exactly; all 31 prior tests remain green plus the 1 new health-check test.

3. **No scope creep.** `git status --porcelain -- apps/chatwoot-bridge` shows the whole
   directory as a single untracked block (never committed yet), so `git diff` can't isolate
   the fix by itself. Cross-checked via file mtimes instead: every file in
   `apps/chatwoot-bridge/` (main.py, config.py, schemas.py, chatwoot_client.py,
   hermes_client.py, backend_client.py, requirements.txt, README.md, and all prior test
   files) clusters at timestamps 19:21:21–19:26:43; `tests/test_health.py` is the only file
   modified afterward (19:35:54). Confirms only the new test file was touched — `main.py`,
   `hermes_client.py`, and `tasks.md` are untouched, as the implementer's report claims.

## Checkpoints (Stage 5 — Implementacion, per DEPLOYMENT_STAGE/CHECKPOINTS.md)
- Codigo compilable / sin syntax errors: [x]
- Tests nuevos pasan: [x] 32/32 green, independently re-run
- Blocking finding from prior review resolved: [x] GET / now has genuine coverage of both
  the HTTP 200 + identifying JSON body scenario and the "Hermes liveness check actually
  invoked" assertion
- No scope creep: [x] confirmed via mtime cross-check (git diff unusable — dir still
  untracked as a whole)
- No hardcoded secrets introduced: [x] N/A, test-only file, no secrets touched

## Non-blocking follow-ups (unchanged from prior review — not re-litigated)
1. `trigger_onboarding()` posts an empty body that would 422 against the real backend —
   tracked, non-blocking.
2. `test_new_lead_triggers_onboarding_and_sets_contact_attributes` under-asserts
   (`tipo_lead` not checked) — tracked, non-blocking.
3. `requirements.txt` pins `respx==0.20.2` but environment resolves `respx-0.23.1` — tracked,
   non-blocking.
4. Task 13.1 (ARCHITECTURE.md containers-table row for `apps/chatwoot-bridge`) still
   unchecked — must be done before archive (docs-sync hard rule), not before this task.

## Required changes
None. All findings from this fix are resolved.
