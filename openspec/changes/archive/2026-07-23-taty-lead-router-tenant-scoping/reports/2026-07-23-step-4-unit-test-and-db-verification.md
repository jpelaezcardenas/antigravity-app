# Step 4 Report - Unit Tests and Database Verification

- Date: 2026-07-23
- Change: taty-lead-router-tenant-scoping
- Agent: leader (Claude Sonnet 5), building on implementer/reviewer subagent work

## Commands Executed

- `cd apps/backend && python -m pytest tests/test_crm_whatsapp_intake.py tests/test_taty_lead_router.py tests/test_whatsapp_endpoints.py -v` (targeted, independently re-run by both implementer and reviewer)
- `cd apps/backend && python -m pytest tests -v` (full suite, run twice by the reviewer: once with this change's diff applied, once with it stashed against the unmodified `feature/chatwoot-hermes-taty-bridge` tip)

## Unit Test Results

- Targeted (3 files): **58 passed**, 0 failed
- Full suite with this change applied: **588 passed, 40 failed, 109 skipped** (+3 files that fail at
  collection with a pre-existing `ModuleNotFoundError: No module named 'apps'`, unrelated to this
  change, excluded from the count above)
- Full suite with this change's diff stashed (unmodified branch tip): **585 passed, 40 failed, 109
  skipped** — the reviewer independently confirmed the 40 failed test names are byte-identical
  between both runs; the only delta is the 3 new tests this change adds (588 - 585 = 3)
- Root cause of the 40 pre-existing failures: an `httpx`/`starlette.TestClient` version mismatch in
  the local dev environment (`TypeError: Client.__init__() got an unexpected keyword argument
  'app'`), affecting modules entirely unrelated to this change's scope (shadow_gl, secure_llm,
  approval_rules_stage3/4/8/11, centinela_alerts, model_selector, wizard_auditoria_sombra) — none
  touch `crm_service.py`, `taty_lead_router.py`, `whatsapp_endpoints.py`, or their tests

## Database State Verification

- All tests in scope (targeted + the delegation logic itself) use a mocked `CrmService`/Supabase
  client — no real database connection is made.
- Pre-test baseline / post-test validation: N/A (no real DB touched)
- State restored: Yes (nothing to restore)

## Outcome

- Step 4 status: PASS
- Blocking issues: none
- The 40 pre-existing full-suite failures are a known, unrelated local-environment issue (dependency
  version mismatch) — confirmed identical before and after this change by direct comparison, not
  introduced or worsened by this work.
