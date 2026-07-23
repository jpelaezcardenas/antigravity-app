# Implementation report — chatwoot-hermes-taty-bridge, Task Groups 5-10

## Scope
Implemented Task Groups 5 through 10 from
`openspec/changes/chatwoot-hermes-taty-bridge/tasks.md`: the standalone
`apps/chatwoot-bridge/` FastAPI service (webhook filtering/HITL, Chatwoot
client, Hermes client, backend client, orchestration). Task Groups 1-4
(backend `POST /api/v1/crm/leads/whatsapp-intake`) were already done prior
to this session. Task Groups 11-15 (Docker Compose, manual curl testing
against a live Chatwoot/Hermes stack, ARCHITECTURE.md doc row, Stage 11
deploy, review gate) are explicitly out of scope for this task and were not
touched.

## Files created

```
apps/chatwoot-bridge/
  main.py                  # POST /webhook, process_incoming_message, GET /
  config.py                # pydantic-settings Settings (all secrets empty-by-default)
  schemas.py                # ChatwootWebhookPayload + nested Chatwoot payload models
  chatwoot_client.py       # get_recent_messages, send_reply, set_contact_attributes
  hermes_client.py         # invoke_chat_completion, check_models (fail-soft)
  backend_client.py        # sign_tenant_jwt, whatsapp_intake, trigger_onboarding (fail-soft)
  requirements.txt
  .env.example
  README.md
  tests/
    __init__.py
    test_webhook_filter.py
    test_chatwoot_client.py
    test_hermes_client.py
    test_backend_client.py
    test_process_message.py
```

## TDD red -> green, per module

- **Task Group 6 (webhook filter/HITL)** — `tests/test_webhook_filter.py`
  written first against a not-yet-existing `main.py`; confirmed failing with
  `ModuleNotFoundError: No module named 'main'` for all 9 cases. Implemented
  `POST /webhook` in `main.py` (token check before any parsing -> event/type/
  private filter -> `bot_off` label check -> `BackgroundTasks.add_task`).
  Full truth table from the spec passes: incoming+not-private -> `processing_started`,
  outgoing -> `skipped`, private -> `skipped`, non-`message_created` -> `skipped`,
  missing/wrong token -> `401` (including malformed-body case, proving the
  token check runs before JSON parsing), `bot_off` present -> `paused` with no
  downstream call, `bot_off` absent -> normal processing. One assertion
  correction during green: with `httpx.ASGITransport`, `BackgroundTasks`
  execute synchronously within the same call stack before the client sees the
  response, so the correct assertion is "called once" rather than "not
  called inline" — updated the two affected test bodies to reflect that
  (behavior itself, i.e. scheduling via `BackgroundTasks` rather than an
  inline `await`, is unchanged and matches the task's design).

- **Task Group 7 (Chatwoot client)** — `tests/test_chatwoot_client.py`
  (respx-mocked) written first; failed with `ModuleNotFoundError:
  chatwoot_client`. Implemented `get_recent_messages` (maps `message_type: 0`
  -> `role: "user"`, anything else -> `role: "assistant"`, slices to the last
  `MAX_HISTORY`), `send_reply` (`message_type: "outgoing"`),
  `set_contact_attributes`, all via a shared
  `httpx.AsyncClient(follow_redirects=True, timeout=60.0)`. One test's
  expected mapping had to be corrected during green (my own test fixture
  math for `message_type` alternation was off — fixed the expectation, not
  the implementation, since the implementation's mapping already matched the
  spec's rule). All 4 tests pass.

- **Task Group 8 (Hermes client)** — `tests/test_hermes_client.py`
  (respx-mocked) written first; failed on missing module. Implemented
  `invoke_chat_completion` (`POST /v1/chat/completions`, `model` from
  `settings.HERMES_MODEL`, `stream: false`, bearer auth, 60s timeout, catches
  all exceptions and non-200 responses, logs with `logger.exception`, returns
  `None` — never raises) and `check_models` (`GET /v1/models`, same fail-soft
  contract, used for the startup/health liveness log). All 5 tests pass on
  first implementation attempt (correct request shape, timeout -> `None`,
  non-200 -> `None`, `check_models` success/failure).

- **Task Group 9 (backend client)** — `tests/test_backend_client.py`
  (respx-mocked) written first; failed on missing module. Implemented
  `sign_tenant_jwt` (HS256 via `python-jose`, claims `sub: "chatwoot-bridge"`,
  `tenant_id`, `exp` = now + 30 min, signed with `settings.CONTEXIA_JWT_SECRET`),
  `whatsapp_intake` (`POST {CONTEXIA_API_URL}/crm/leads/whatsapp-intake`,
  fail-soft -> `None`), `trigger_onboarding` (`POST
  {CONTEXIA_API_URL}/social-ops/onboarding/start`, fail-soft, swallows and
  logs). All 7 tests pass on first implementation attempt.

- **Task Group 10 (orchestration)** — `tests/test_process_message.py`
  written first (mocking every client function via `patch.object` on the
  imported modules); failed on missing `main.process_incoming_message`.
  Implemented `process_incoming_message(conversation_id, content,
  attachments, contact_id, phone)`: audio attachment short-circuits to a
  fixed Spanish fallback reply with no Hermes call; otherwise calls
  `backend_client.whatsapp_intake(phone)` (continuing on `None`/failure per
  design.md decision 7), triggers onboarding + sets Chatwoot contact
  attributes only when `is_new: True`, fetches history, calls
  `hermes_client.invoke_chat_completion`, falls back to a fixed Spanish
  apology if that returns `None`, and always dispatches via
  `chatwoot_client.send_reply`. `GET /` health check added, logging
  `hermes_client.check_models()`'s result. All 6 orchestration tests pass on
  first implementation attempt.

## Final full-suite run

```
$ cd apps/chatwoot-bridge && python -m pytest tests -v
...
31 passed, 1 warning in 11.29s
```

(Warning is a pre-existing, unrelated `PendingDeprecationWarning` from
`starlette.formparsers` about `python_multipart` — not caused by this
change, same warning appears in the backend's own test suite.)

Also re-ran from the repo root exactly as specified in the task
(`pytest apps/chatwoot-bridge/tests -v`) — same result, 31 passed.

## Deviations / judgment calls (documented, none touch out-of-scope code)

1. **`tenant_id` claim value for `sign_tenant_jwt()`.**
   `openspec/changes/hermes-multi-tenant-wrapper/HERMES_CONFIG.md` documents
   the JWT *shape* (`sub`, `tenant_id`, `exp`, HS256) for Hermes operators
   but its example tenant id (`contexia-org-1`) is illustrative for that
   doc's example org, not necessarily authoritative for a new non-Hermes
   caller. I resolved this by grepping the backend's own JWT issuance code
   (`apps/backend/core/identity_resolver.py`): its docstring states
   `create_access_token` **defaults `workspace_id` to the literal
   `"contexia-org-1"`** for the single-tenant Cliente Cero deployment. I used
   that same literal as a fixed constant in `backend_client.py` (documented
   inline) rather than inventing a new env var, since (a) it is the
   established, already-in-production convention for exactly this
   single-tenant setup, and (b) the task's env var list for `config.py`
   deliberately does not include a `CONTEXIA_TENANT_ID` var, so adding one
   would have gone beyond the specified scaffold. Note that `crm_service.py`'s
   `whatsapp_intake` itself resolves the real Cliente Cero tenant UUID
   server-side (`_resolve_cliente_cero_tenant_id`) independent of the JWT's
   `tenant_id` claim — the claim's role here is only to satisfy
   `get_current_user`'s auth check, not to select which tenant's data is
   touched.

2. **`trigger_onboarding()`'s request body.** The real
   `POST /api/v1/social-ops/onboarding/start` endpoint's `OnboardingStartRequest`
   requires `company_name`, `customer_email`, and `payment_reference` —
   none of which are available from a bare WhatsApp inbound message. Per the
   task's explicit instruction ("same fail-soft contract, logs and swallows
   errors") and design.md decision 7 (graceful degradation over hard
   failure), I implemented `trigger_onboarding()` to `POST` with an empty
   JSON body and let the fail-soft path (log + swallow on any `>=400`) handle
   the resulting `422` gracefully — this is within Task Group 9's stated
   contract and does not touch `apps/backend/**` (out of scope for this
   task). Flagging this for the leader/reviewer: a follow-up change may want
   either (a) a WhatsApp-specific onboarding-start variant with relaxed
   required fields, or (b) the bridge collecting more info before calling
   onboarding. Not resolved here since it requires an OpenSpec-level
   decision and backend changes, both out of this task's scope.

## Standards checklist

- TDD: every module's tests were written and confirmed failing (module not
  found) before implementation, per module, as itemized above.
- Full type hints throughout (`from __future__ import annotations` used for
  forward-ref-friendly modern hints on Python 3.11).
- English only in all code, comments, docstrings, and test names.
- No hardcoded secrets or URLs beyond the documented defaults in
  `config.py`/`.env.example` (all secrets default to `""`, i.e. fail closed).
- Every external call (Chatwoot, Hermes, backend) goes through
  `httpx.AsyncClient`; all three client test modules use `respx` — no real
  network calls in the suite.
- `apps/backend/**` untouched in this session.
- `openspec/changes/chatwoot-hermes-taty-bridge/tasks.md` not modified by me
  (left for the leader to mark 5.x-10.x complete after review).

## Session bookkeeping
- `feature_list.json`: `active` set to `chatwoot-hermes-taty-bridge`
  (`in_progress`), replacing the prior `null` — no other change was
  `in_progress`, so the one-change-at-a-time invariant holds.
- `progress/current.md`: appended a "Sesión activa (2026-07-22)" section
  noting the task and plan.
