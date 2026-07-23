# Review — task chatwoot-hermes-taty-bridge (Task Groups 5-10)

**Verdict:** CHANGES_REQUESTED

## Scope reviewed
`apps/chatwoot-bridge/{main.py,config.py,schemas.py,chatwoot_client.py,hermes_client.py,backend_client.py}`
and `apps/chatwoot-bridge/tests/*` (5 test modules, 31 tests), against
`openspec/changes/chatwoot-hermes-taty-bridge/design.md` (decisions 1-9) and
`specs/chatwoot-hermes-bridge/spec.md` (7 ADDED requirements). Tests re-run
independently: `cd apps/chatwoot-bridge && python -m pytest tests -v` gave
**31 passed, 1 warning (pre-existing, unrelated python_multipart
deprecation)** — matches the implementer's report exactly.

## Checkpoints (Stage 5 - Implementacion, per DEPLOYMENT_STAGE/CHECKPOINTS.md)
- Codigo compilable / sin syntax errors: [x]
- Tests existentes pasan (backend suite untouched, out of scope here): [x] not touched this session
- Tests nuevos pasan: [x] 31/31 green, independently re-run
- Linting/type checking: [x] full type hints throughout (from __future__ import annotations plus
  explicit param/return types in every module); no linter configured for this new app, none required
  by tasks.md
- Docs-sync (canon vivo): [N/A for this review] - ARCHITECTURE.md container-table row for
  apps/chatwoot-bridge/Chatwoot is Task 13.1, explicitly out of scope for Task Groups 5-10 per
  both the implementer's report and tasks.md's own structure. Flagging as a hard gate before
  archive: the change cannot be archived with 13.1 unchecked, since it did add a new container.
- No hardcoded secrets: [x] config.py - every secret (CHATWOOT_API_TOKEN, HERMES_API_KEY,
  CONTEXIA_JWT_SECRET, WEBHOOK_TOKEN) defaults to empty string, fail-closed; .env.example has no
  real values.
- All external calls httpx/respx-mocked in tests: [x] - grepped all 5 test files; every HTTP-touching
  test uses @respx.mock plus respx.get/post(...).mock(...); test_webhook_filter.py uses
  httpx.ASGITransport (in-process, no network) with process_incoming_message patched out. No
  unmocked network call found anywhere in the suite.

## Findings

### Blocking

1. Requirement "Health check reflects Hermes Gateway reachability" (spec.md lines 114-122) has
   zero test coverage. GET / is implemented in main.py:108-112 and does call
   hermes_client.check_models() and log the result, matching the requirement's prose. But grepping
   apps/chatwoot-bridge/tests/ for any reference to the health endpoint ("health", GET "/",
   client.get("/")) returns no matches. None of the 5 test files exercise GET / at all — not
   the "Health check succeeds -> HTTP 200 with a JSON body identifying the service" scenario, nor any
   assertion that hermes_client.check_models() is actually invoked/logged.
   This is a real, plausible-but-unverified requirement per the review brief's explicit instruction
   ("every ADDED requirement and scenario must be genuinely covered by a real test, not just
   plausibly covered"). The implementer's own report
   (progress/impl_chatwoot-hermes-taty-bridge-task5-10.md) lists a full TDD narrative for Task
   Groups 6-10 but never mentions writing a test for GET / — task 10.3 in tasks.md ("Implement
   GET / health check...") itself has no corresponding "write failing test" sub-item in 10.1, so
   this gap traces back to a task-list omission, not just an implementer oversight — but the review
   brief requires spec-scenario coverage regardless of what tasks.md enumerated.

   Required fix: add a test (e.g. in test_process_message.py or a new test_health.py) that calls
   GET / via ASGITransport/TestClient, asserts HTTP 200 and a JSON body identifying the service
   (service: "chatwoot-hermes-bridge" at minimum), and asserts hermes_client.check_models() was
   actually called (e.g. via patch.object + assert_awaited_once).

### Verified correct (no issues found)

- Token-before-parsing (spec.md lines 29-36): main.py:50-54 - _check_webhook_token(...) is
  called before body = await request.json(). Confirmed genuinely enforced, not just documented:
  tests/test_webhook_filter.py::test_token_check_happens_before_event_parsing posts
  content=b"not json at all" with no token and asserts 401 - a real adversarial test, not a happy
  path.
- bot_off short-circuits before any downstream call, not just Hermes: main.py:63-64 returns
  a paused status before background_tasks.add_task(process_incoming_message, ...) is
  ever scheduled - so no Hermes call, no backend_client call, and no Chatwoot reply happen, because
  process_incoming_message (which is the only place any of those three clients are invoked) is never
  even queued. Verified by reading both the label-check placement in webhook() and confirming
  process_incoming_message's body (lines 77-105) is the sole call site for
  backend_client.whatsapp_intake, chatwoot_client.get_recent_messages/send_reply, and
  hermes_client.invoke_chat_completion. Test test_bot_off_label_pauses_processing asserts
  mock_process.assert_not_called() - correct assertion target (the whole pipeline function, not a
  narrower Hermes-only mock).
- hermes_client.invoke_chat_completion/check_models never raise: both wrap their entire
  HTTP call plus response parsing (including the choices/message/content indexing, which could
  KeyError/IndexError on a malformed Hermes response) inside a single try/except Exception that
  logs via logger.exception and returns None. Confirmed by reading hermes_client.py:41-55 and
  58-77 directly, not just trusting the report.
- backend_client.whatsapp_intake/trigger_onboarding never raise: same pattern,
  backend_client.py:57-72 and 79-89, generic except Exception around the full HTTP call.
  Confirmed with adversarial tests (test_network_failure_returns_none_without_raising,
  test_failure_is_swallowed_not_raised) using respx side_effect=httpx.ConnectError.
- tenant_id set to the literal contexia-org-1 deviation is factually correct, not a misread.
  Verified directly in apps/backend/core/security.py:12-14 - create_access_token really does
  default to_encode tenant_id to contexia-org-1 when the caller does not supply one; this is the
  actual code path, not just identity_resolver.py's docstring paraphrase of it (which also
  matches). Further verified that crm_service.whatsapp_intake (services/crm_service.py:387-411)
  resolves the real Cliente Cero tenant UUID server-side via _resolve_cliente_cero_tenant_id(client),
  independent of the JWT's tenant_id claim - so the hardcoded literal only has to satisfy
  get_current_user's signature check (core/deps.py:53-76, which does not require resolved_tenant_id
  to be non-None to pass), not select tenant data. The implementer's judgment call holds up under
  direct source reading, not just trusting the report's citation.
- trigger_onboarding's empty-body deviation cannot block the Hermes reply. Confirmed
  trigger_onboarding() (backend_client.py:75-89) is wrapped in a blanket try/except Exception
  block that logs and returns, with no re-raise, and is awaited directly (not wrapped in another
  try) at main.py:95 inside process_incoming_message - since it cannot raise, the subsequent
  history fetch and Hermes call on lines 100-105 are unconditionally reached regardless of
  onboarding's real HTTP outcome. The documented gap (real endpoint likely 422s on an empty JSON
  body, so onboarding functionally never succeeds today for WhatsApp leads) is real but is a
  product-completeness gap, not a code-safety defect, and the report flags it honestly as a
  follow-up requiring an OpenSpec-level decision - that is a sufficient safeguard for this task's
  scope given design.md decision 7's literal text (the bridge SHALL call and SHALL log the failure
  and continue), which does not require the call to succeed. Non-blocking, but see follow-up below.

## Non-blocking follow-ups (not required to approve this task, but should be tracked)

1. trigger_onboarding() posts an empty JSON body against an endpoint whose OnboardingStartRequest
   requires company_name/customer_email/payment_reference - it will 422 against the real backend
   today. Onboarding is effectively a no-op for WhatsApp leads until a follow-up OpenSpec change
   either adds a WhatsApp-specific onboarding-start variant or the bridge collects more info first.
   Already flagged by the implementer; needs a tracked decision before this is relied upon in
   production.
2. test_new_lead_triggers_onboarding_and_sets_contact_attributes only asserts the estado attribute
   equals nuevo, not the tipo_lead attribute, even though the spec text and the code (main.py:96-98)
   both set both attributes. Low-value gap - the code is correct, the test is just slightly
   under-asserted.
3. requirements.txt pins respx==0.20.2 but the environment actually resolves/runs respx-0.23.1
   (per the pytest plugin banner). Not a correctness issue today, but worth reconciling so
   pip install -r requirements.txt reproduces exactly what CI/local runs against.
4. Task 13.1 (ARCHITECTURE.md containers-table row for apps/chatwoot-bridge) is still unchecked -
   correctly out of scope for this task, but this change cannot be archived until it's done
   (docs-sync hard rule, CLAUDE.md section 0 and ARCHITECTURE.md's own living-doc rule).

## Required changes (blocking)

1. Add a real test asserting GET / returns HTTP 200 with an identifying JSON body and asserting
   hermes_client.check_models() is actually invoked (not just implemented) - covering
   specs/chatwoot-hermes-bridge/spec.md's Health-check-reflects-Hermes-Gateway-reachability
   requirement and its Health-check-succeeds scenario, which currently has zero coverage.
