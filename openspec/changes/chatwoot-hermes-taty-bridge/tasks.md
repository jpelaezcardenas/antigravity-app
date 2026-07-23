## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Create feature branch `feature/chatwoot-hermes-taty-bridge` from `main`
- [x] 0.2 Verify branch creation and current branch status (`git status`, `git branch --show-current`)

## 1. Backend: CRM WhatsApp Intake Endpoint (TDD)

- [x] 1.1 Write failing tests in `apps/backend/tests/test_crm_whatsapp_intake.py` mirroring
      `test_crm_service_b2b_writes.py` style: new phone creates lead (`stage: "NUEVOS"`,
      `is_new: true`), known phone is found not duplicated (`is_new: false`), unauthenticated call
      is rejected
- [x] 1.2 Add `whatsapp_intake(whatsapp_phone: str) -> dict` to `apps/backend/services/crm_service.py`,
      reusing the existing `crm_leads` tenant-scoping pattern from `b2c_pipeline`/`advance_lead`
- [x] 1.3 Add `POST /api/v1/crm/leads/whatsapp-intake` to `apps/backend/presentation/crm_endpoints.py`,
      protected by the existing `Depends(get_current_user)` / tenant JWT pattern
- [x] 1.4 Run `apps/backend/tests/test_crm_whatsapp_intake.py` and confirm all tests pass

## 2. Backend: Review and Update Existing Unit Tests (MANDATORY)

- [x] 2.1 Review `apps/backend/tests/test_crm_service.py` and
      `apps/backend/tests/test_crm_service_b2b_writes.py` for any assumptions the new method
      touches (e.g. shared fixtures, mocked Supabase client); update if needed — reviewer confirmed
      no shared fixtures were touched and the full regression run (26 passed, 4 pre-existing skips)
      shows no impact; no changes needed

## 3. Backend: Run Unit Tests and Verify Database State (MANDATORY)

- [x] 3.1 Capture pre-test database baseline for `crm_leads` (row count for the Cliente Cero tenant)
      — N/A, tests use a mocked Supabase client, no real DB touched
- [x] 3.2 Run targeted tests: `pytest apps/backend/tests/test_crm_whatsapp_intake.py -v` — 5 passed
- [x] 3.3 Run required broader suite (from `apps/backend/` cwd) — 26 passed, 4 pre-existing skips
- [x] 3.4 Verify post-test `crm_leads` row count matches baseline (tests use mocked/test Supabase
      client, not production data) and restore if any unintended mutation occurred — N/A, mocked
- [x] 3.5 Create report
      `openspec/changes/chatwoot-hermes-taty-bridge/reports/2026-07-22-step-3-unit-test-and-db-verification.md`
- [x] 3.6 Mark this step complete only after tests pass and the report exists

## 4. Backend: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [x] 4.1 Start the backend server locally (`uvicorn` on `:8080`, `CRM_CANONICAL=true` to mount the
      router) — done, health-checked, cleanly stopped afterward (port 8080 confirmed free)
- [x] 4.2 `curl -X POST .../whatsapp-intake` with a fresh `whatsapp_phone` — reached the real
      Supabase call and failed only on a missing local `SUPABASE_SERVICE_ROLE_KEY` env var (a
      pre-existing local dev-environment gap, confirmed to affect the already-shipped
      `b2c/pipeline` endpoint identically, not a regression from this change — see report)
- [x] 4.3 (blocked by the same env gap as 4.2, see report — logic-level create/lookup/tenant-scoping
      is verified by the automated suite in Step 3 instead)
- [x] 4.4 Call without an `Authorization` header (`AUTH_ENFORCED=true`) → verified 401; also tested
      an invalid/garbage bearer token → verified 401
- [x] 4.5 Restore database state — N/A, no `crm_leads` row was created (every write attempt failed
      before reaching Supabase, per 4.2)
- [x] 4.6 Document all curl commands and responses in
      `openspec/changes/chatwoot-hermes-taty-bridge/reports/2026-07-22-step-4-curl-verification.md`

## 5. Bridge: Project Scaffold

- [x] 5.1 Create `apps/chatwoot-bridge/` with `main.py`, `config.py`, `schemas.py`,
      `chatwoot_client.py`, `hermes_client.py`, `backend_client.py`, `tests/`, `requirements.txt`,
      `.env.example`, `README.md`
- [x] 5.2 `config.py`: pydantic-settings `Settings` class reading all env vars from design.md
      (`CHATWOOT_URL`, `CHATWOOT_API_TOKEN`, `CHATWOOT_ACCOUNT_ID`, `HERMES_GATEWAY_URL`,
      `HERMES_MODEL`, `HERMES_API_KEY`, `CONTEXIA_API_URL`, `CONTEXIA_JWT_SECRET`, `PAUSE_LABEL`,
      `MAX_HISTORY`, `WEBHOOK_TOKEN`, `PORT`), all empty-by-default (fail closed, no hardcoded
      secrets)
- [x] 5.3 `requirements.txt`: `fastapi`, `uvicorn`, `httpx`, `pydantic-settings`, `python-jose`;
      dev: `pytest`, `pytest-asyncio`, `respx`

## 6. Bridge: Webhook Filtering & HITL (TDD)

- [x] 6.1 Write failing tests in `apps/chatwoot-bridge/tests/test_webhook_filter.py` covering the
      full truth table from `specs/chatwoot-hermes-bridge/spec.md`: incoming+not-private (process),
      outgoing (skip), private (skip), non-`message_created` event (skip), missing/invalid
      `WEBHOOK_TOKEN` (401), `bot_off` label present (paused, no Hermes call)
- [x] 6.2 Implement `POST /webhook` in `main.py`: token check → event/type/private filter →
      `bot_off` label check → schedule `BackgroundTasks` processing
- [x] 6.3 Run `pytest apps/chatwoot-bridge/tests/test_webhook_filter.py -v` and confirm all pass

## 7. Bridge: Chatwoot Client (history fetch + reply dispatch + contact attributes)

- [x] 7.1 Write failing tests in `apps/chatwoot-bridge/tests/test_chatwoot_client.py` (respx-mocked
      HTTP) for: fetch last `MAX_HISTORY` messages mapped to `{role, content}`, post outgoing
      reply, set contact custom attributes
- [x] 7.2 Implement `chatwoot_client.py`: `get_recent_messages`, `send_reply`,
      `set_contact_attributes`, using a shared `httpx.AsyncClient(follow_redirects=True,
      timeout=60.0)` (covers Active Storage 302s)
- [x] 7.3 Run tests and confirm pass

## 8. Bridge: Hermes Client (OpenAI-compatible chat completions)

- [x] 8.1 Write failing tests in `apps/chatwoot-bridge/tests/test_hermes_client.py` (respx-mocked):
      correct request shape (`model: "taty-v1"`, `messages`, `stream: false`, bearer auth), 60s
      timeout triggers fallback path, non-200 triggers fallback path, `GET /v1/models` startup check
- [x] 8.2 Implement `hermes_client.py`: `invoke_chat_completion(history, message) -> str`,
      `check_models() -> dict | None` for the startup log
- [x] 8.3 Run tests and confirm pass

## 9. Bridge: Backend Client (lead intake + onboarding trigger)

- [x] 9.1 Write failing tests in `apps/chatwoot-bridge/tests/test_backend_client.py` (respx-mocked):
      JWT is signed with `tenant_id` claim, intake call maps response correctly, onboarding trigger
      only fires when `is_new: true`, failures are caught and logged (not raised)
- [x] 9.2 Implement `backend_client.py`: `sign_tenant_jwt()`, `whatsapp_intake(phone) -> dict`,
      `trigger_onboarding()`, all wrapped to degrade gracefully per design.md decision 7
- [x] 9.3 Run tests and confirm pass

## 10. Bridge: Orchestration (audio fallback + full pipeline)

- [x] 10.1 Write failing tests in `apps/chatwoot-bridge/tests/test_process_message.py`: audio
      attachment → fixed fallback reply, no Hermes call; text message → full pipeline
      (intake → history → Hermes → reply) called in order; Hermes failure → fallback reply sent
- [x] 10.2 Implement the background `process_incoming_message` orchestration in `main.py` wiring
      steps 7–9 together per design.md decisions 5 and 7
- [x] 10.3 Implement `GET /` health check including the Hermes `check_models()` log — test coverage
      added in `tests/test_health.py` after a reviewer round-trip (initial pass missed it)
- [x] 10.4 Run `pytest apps/chatwoot-bridge/tests -v` (full suite) and confirm all pass — 32 passed

## 11. Local Infrastructure: Chatwoot Docker Compose

- [ ] 11.1 Create `docker-compose.chatwoot.yml` at repo root: `postgres` (plain `postgres:15` per
      design.md open question), `redis`, `chatwoot-web` (`${CHATWOOT_PORT:-3020}:3000`),
      `chatwoot-worker` (sidekiq), named volumes (`chatwoot_postgres`, `chatwoot_redis`,
      `chatwoot_storage`)
- [ ] 11.2 Document the one-time `rails db:chatwoot_prepare` init command and `SECRET_KEY_BASE`
      generation in `apps/chatwoot-bridge/README.md`
- [ ] 11.3 Bring the stack up locally (`docker compose -f docker-compose.chatwoot.yml up -d`),
      complete the Chatwoot setup wizard, create the WhatsApp Cloud API inbox, generate a
      `CHATWOOT_API_TOKEN`

## 12. Bridge: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 12.1 Start the bridge locally (`uvicorn main:app --port 8090`) against the running Chatwoot +
      Hermes Gateway (verify `taty-v1` is the active profile via
      `curl -H "Authorization: Bearer $HERMES_API_KEY" http://127.0.0.1:8642/v1/models`)
- [ ] 12.2 `curl http://127.0.0.1:8090/` → verify 200 health response
- [ ] 12.3 `curl -X POST http://127.0.0.1:8090/webhook` with a simulated Chatwoot
      `message_created`/`incoming` payload and correct `WEBHOOK_TOKEN` → verify
      `{"status":"processing_started"}` and that an outgoing reply lands in the Chatwoot conversation
      (check via Chatwoot API)
- [ ] 12.4 `curl -X POST http://127.0.0.1:8090/webhook` with an `outgoing` payload → verify
      `{"status":"skipped"}` and no reply is sent
- [ ] 12.5 Add the `bot_off` label to the test conversation via Chatwoot API, repeat 12.3 → verify
      `{"status":"paused",...}` and no Hermes call (check bridge logs), then remove the label
- [ ] 12.6 `curl -X POST http://127.0.0.1:8090/webhook` without the correct `WEBHOOK_TOKEN` → verify
      401
- [ ] 12.7 Document all curl commands and responses in
      `openspec/changes/chatwoot-hermes-taty-bridge/reports/YYYY-MM-DD-step-12-curl-verification.md`
- [ ] 12.8 Clean up test conversation/lead data created during manual testing

## 13. Documentation

- [ ] 13.1 Add a row for Chatwoot + `apps/chatwoot-bridge` to the containers table in
      `ARCHITECTURE.md` (living-doc rule, same change), noting the local-only deploy target
- [ ] 13.2 Write `apps/chatwoot-bridge/README.md`: env var reference, local startup sequence, port
      map, troubleshooting (wrong Hermes profile, webhook token mismatch)

## 14. Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

**Split deploy target** (per design.md): the new backend endpoint deploys via the normal Railway
pipeline; Chatwoot + the bridge deploy **locally to this laptop**, which is their sovereign
production target (ARCHITECTURE.md decision #1) — not Vercel/Railway.

- [ ] 14.1 `git commit` + push `feature/chatwoot-hermes-taty-bridge` to `main` (backend endpoint
      change only triggers Railway; Chatwoot/bridge are not deployed by this push)
- [ ] 14.2 Railway `-175a` deploy active and green for the backend change; verify
      `POST /api/v1/crm/leads/whatsapp-intake` responds correctly against the production URL with a
      valid token (then clean up any test lead created)
- [ ] 14.3 Local deployment runbook executed and verified end-to-end on this laptop:
      ```
      docker compose -f docker-compose.chatwoot.yml up -d
      wsl -d hermes-ws -- hermes -p taty-v1 gateway run
      cd apps/chatwoot-bridge && uvicorn main:app --port 8090
      ```
      (Cloudflare Tunnel exposure of Chatwoot's `:3020` webhook to Meta's WhatsApp Cloud API is
      documented as a manual follow-up step, not automated in this change — see design.md Risks)
- [ ] 14.4 Confirm a real WhatsApp message round-trips through Meta → Chatwoot → bridge → Hermes →
      Chatwoot → WhatsApp reply (requires the tunnel from 14.3 to be live)
- [ ] 14.5 Create report:
      `openspec/changes/chatwoot-hermes-taty-bridge/reports/YYYY-MM-DD-deployment.md`

## 15. Review Gate

- [ ] 15.1 `reviewer` agent validates the full change against
      `specs/chatwoot-hermes-bridge/spec.md`, `specs/crm-b2c-sell-machine/spec.md`,
      `DEPLOYMENT_STAGE/CHECKPOINTS.md`: 60s timeout handling, health check, loop-prevention truth
      table, no hardcoded secrets, English-only artifacts, symlink integrity untouched
- [ ] 15.2 `RUN_TESTS=1 bash init.sh` green before marking the change ready to archive
