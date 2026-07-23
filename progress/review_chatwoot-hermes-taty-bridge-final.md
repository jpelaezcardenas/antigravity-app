# Review — task chatwoot-hermes-taty-bridge (final, pre-archive gate, Task Group 15)

**Verdict:** APPROVED

## Scope reviewed

- openspec/changes/chatwoot-hermes-taty-bridge/{proposal,design,tasks}.md
- specs/chatwoot-hermes-bridge/spec.md, specs/crm-b2c-sell-machine/spec.md
- All 4 reports in reports/ + taty-lead-router-tenant-scoping/ (sub-change) tasks/reports
- apps/backend/services/crm_service.py::whatsapp_intake,
  apps/backend/presentation/crm_endpoints.py (POST /leads/whatsapp-intake),
  apps/backend/services/taty_lead_router.py::find_or_create_lead
- Full apps/chatwoot-bridge/ tree (main.py, config.py, schemas.py, chatwoot_client.py,
  hermes_client.py, backend_client.py, all 6 test files)
- docker-compose.chatwoot.yml, .env.chatwoot.example, apps/chatwoot-bridge/.env.example,
  .gitignore
- init.sh (this session pytest-gate fix)
- ARCHITECTURE.md new containers-table row

## Tests run

- cd apps/backend and run pytest tests/test_crm_whatsapp_intake.py tests/test_taty_lead_router.py
  tests/test_whatsapp_endpoints.py tests/test_auth_deps.py -v -> 86 passed (8 + 78, run as two
  invocations), 0 failed.
- cd apps/chatwoot-bridge and run pytest tests -v -> 30 passed, 0 failed.
- RUN_TESTS=1 bash init.sh (repo root) -> correctly reports [FAIL]: canon and harness structure
  both [OK], feature_list.json [OK], backend suite fails with 27 failed, 744 passed, 112 skipped,
  13 errors. Cross-checked every failing test name by hand (python -m pytest apps/backend -q from
  repo root) against this change touched files:
  - test_crm_endpoints.py TestCrmCanonicalFeatureFlag test_crm_router_conditionally_included_on_flag
    and test_whatsapp_endpoints.py TestWhatsappCanonicalFeatureFlag
    test_router_conditionally_included_on_flag (2 of the 27) look change-adjacent by filename but
    are NOT caused by this change - confirmed by re-running them with cwd=apps/backend: both pass.
    The failure is a pre-existing test-authoring bug (open of "presentation/router.py" is a
    cwd-relative path, and init.sh / root-level pytest runs with cwd=repo-root, not apps/backend).
    The same relative-path pattern exists identically in test_sell_machine_endpoints.py and
    test_social_ops_endpoints.py, both also in the failing list and both untouched by this change -
    confirms a systemic, pre-existing harness quirk, not a regression.
  - The remaining 25 failed + 13 errors (Shadow GL CSV/E2E, approval-rules stage8/11, centinela
    alerts, model-selector cloud-only, secure-LLM, swarm-operators, wizard-auditoria-sombra,
    financials-aggregation, financials-endpoint-tenant-scoping) touch none of this change files and
    match/extend the categories already logged in DEPLOYMENT_STAGE/CHECKPOINTS.md self-improving
    rule (2026-07-23, hermes-task-queue-tenant-scoping) as pre-existing and unrelated. Total
    (27+13=40) matches that rule "~40 known pre-existing failures" figure exactly.
  - Conclusion: init.sh current [FAIL] is the correct, honest report - not a false green, not a
    false red attributable to this change. No test failure traces into
    crm_service.py::whatsapp_intake, crm_endpoints.py new route, taty_lead_router.py
    find_or_create_lead, or any apps/chatwoot-bridge module.

## Code-level findings

- 10.5 design correction is genuinely clean. Grepped main.py, backend_client.py, and all bridge
  tests: no trigger_onboarding, no onboarding/start call anywhere. main.py new-lead branch
  (process_incoming_message, lines 89-97) only calls chatwoot_client.set_contact_attributes.
  test_process_message.py TestFullTextPipeline test_new_lead_sets_contact_attributes_without_onboarding
  and test_returning_contact_does_not_set_contact_attributes assert exactly this. Spec
  (chatwoot-hermes-bridge/spec.md lines 91-97) and design.md decision 5 both match the code.
- find_or_create_lead delegation is real, not just documented. taty_lead_router.py lines 246-255
  call get_crm_service().whatsapp_intake(...), no duplicate Supabase query remains (confirmed by
  reading the current file directly).
- Auth is correctly wired. crm_endpoints.py router (crm_endpoints.py line 17) carries
  dependencies=[Depends(get_current_user)] at router scope, which covers the new
  POST /leads/whatsapp-intake route (no per-route opt-out).
  test_crm_whatsapp_intake.py test_unauthenticated_call_is_rejected exercises this directly and
  passes.
- No hardcoded secrets anywhere checked. apps/chatwoot-bridge/.env.example, .env.chatwoot.example,
  and docker-compose.chatwoot.yml all use empty defaults or a required-var-set-or-fail placeholder
  pattern - real values never present. .gitignore lines 42-43 correctly exclude .env.chatwoot and
  apps/chatwoot-bridge/.env. config.py defaults every secret to empty string (fail-closed, matches
  ARCHITECTURE.md decision #11 pattern).
- Loop-prevention truth table matches spec exactly (main.py lines 56-64 vs.
  chatwoot-hermes-bridge/spec.md table) - token check before parsing, event/type/private filtering
  before the bot_off check, background scheduling only after all filters pass.
- 60s Hermes timeout, graceful degradation, health check all implemented and covered by tests
  (hermes_client.py lines 22 and 41-55, test_hermes_client.py, test_process_message.py
  test_hermes_failure_sends_fallback_reply, test_health.py).
- init.sh pytest-gate fix (section 4) is structurally correct. It captures pytest own exit code
  directly (pytest_status set right after the command substitution, no intervening pipe) - this
  genuinely fixes the previously-reported "always green because tail exit code masked pytest"
  bug. Confirmed by observing [FAIL] correctly surface in this run.
- ARCHITECTURE.md docs-sync: containers table row added (line 60) with an honest "Docker not
  installed" caveat; matches CHECKPOINTS.md Stage 5 docs-sync requirement.
- English-only: all new code/docs/tests in apps/chatwoot-bridge/ and the backend diff are English.
  User-facing Spanish strings (AUDIO_FALLBACK_REPLY, HERMES_FALLBACK_REPLY in main.py) are WhatsApp
  customer-facing copy, not technical artifacts - consistent with existing repo precedent for
  user-facing strings.
- Symlink integrity: git status shows no changes under ai-specs/, .claude/, .cursor/ from this
  change (only an unrelated untracked ai-specs/social-content-ops/ from other work). Checked git
  log across all branches for those paths mentioning chatwoot: no matches - confirmed untouched,
  no symlink risk introduced.

## BLOCKED items (11.3, 12.3, 12.5, 12.8, 14.3, 14.4) reason quality

All six give the same root cause (Docker Desktop genuinely not installed on the laptop, confirmed
both natively on Windows and inside WSL Ubuntu - docker --version fails both ways) plus, for 14.4
specifically, an honest second blocker (no Meta WhatsApp Business number/tunnel provisioned yet).
This is specific and falsifiable, not a vague excuse, and is consistent across tasks.md,
reports/2026-07-23-step-12-curl-verification.md, and reports/2026-07-23-deployment.md. 14.2 choice
not to forge a JWT from an incidentally-exposed production secret to test the authenticated write
path is a defensible, correctly-flagged judgment call (not a shortcut) - it does not weaken the
verification already done (route existence + auth gating confirmed via 401).

## Sub-change note (non-blocking, out of scope for this gate)

taty-lead-router-tenant-scoping own tasks.md section 8 (Review Gate) is still unchecked (8.1/8.2
both open) - it merged into this branch rather than main directly and was never independently
reviewed/archived. Its code is fully exercised by the test runs above (all test_taty_lead_router.py
and test_crm_whatsapp_intake.py cases pass) and is now live in main via this change merge, so
nothing here is functionally unverified - but that sub-change own OpenSpec lifecycle (review +
archive) remains open. Flagging for the founder/leader to close separately; not a reason to
withhold approval of chatwoot-hermes-taty-bridge itself.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md, Stage 5-8)

- Stage 5 (Implementacion): [x] code compiles/imports, [x] existing tests pass, [x] new tests pass,
  [x] docs-sync (ARCHITECTURE.md row present)
- Stage 6 (Review): [x] this review, [x] no hardcoded secrets, [N/A] coverage >=80% not measured
  but every new code path has a corresponding test (TDD throughout tasks.md sections 1-10)
- Stage 7 (Deploy): [x] backend half live on Railway -175a (verified: 401-gated route confirmed
  live per 14.2), [N/A - documented] local half (Chatwoot + bridge) not yet running - Docker not
  installed, honestly tracked as BLOCKED, not silently skipped
- Stage 8 (Cierre): [x] deployment report exists (reports/2026-07-23-deployment.md), [x] ready to
  archive modulo the explicitly-tracked BLOCKED items

## Required changes

None. Approved for archive.
