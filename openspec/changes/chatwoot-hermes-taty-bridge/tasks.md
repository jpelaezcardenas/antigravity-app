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
- [x] 10.5 **Design correction (2026-07-23, pre-archive, per CLAUDE.md §7):** remove the
      `POST /api/v1/social-ops/onboarding/start` call from `process_incoming_message` — it targets
      the B2B/paid-customer 21-day workspace onboarding endpoint (`company_name`/`customer_email`/
      `payment_reference` required), not a fresh B2C WhatsApp lead, and always 422s today (silently
      swallowed by the fail-soft contract). Remove `backend_client.trigger_onboarding()` (dead code
      once nothing calls it), update `main.py`'s new-lead branch to only call
      `chatwoot_client.set_contact_attributes`, and update/remove the now-incorrect
      onboarding-trigger assertions in `tests/test_process_message.py` and
      `tests/test_backend_client.py`. `design.md` decision 5 and
      `specs/chatwoot-hermes-bridge/spec.md`'s lead-intake requirement already updated to reflect
      this. Re-run `pytest apps/chatwoot-bridge/tests -v` and confirm all pass.

## 11. Local Infrastructure: Chatwoot Docker Compose

- [x] 11.1 Create `docker-compose.chatwoot.yml` at repo root: `postgres` (plain `postgres:15` per
      design.md open question), `redis`, `chatwoot-web` (`${CHATWOOT_PORT:-3020}:3000`),
      `chatwoot-worker` (sidekiq), named volumes (`chatwoot_postgres`, `chatwoot_redis`,
      `chatwoot_storage`). Also added `.env.chatwoot.example` (secrets template, `.gitignore`d real
      file) since the compose file requires `CHATWOOT_DB_PASSWORD`/`CHATWOOT_SECRET_KEY_BASE`.
- [x] 11.2 Documented the one-time `rails db:chatwoot_prepare` init command and `SECRET_KEY_BASE`
      generation in `apps/chatwoot-bridge/README.md` (new "Chatwoot one-time setup" section). Also
      corrected a stale instruction in the same README that referenced a non-existent `hermes-ws`
      WSL distro — the actual gateway runs under the `Ubuntu` distro as a systemd user service
      (discovered during the earlier tunnel/webhook investigation this session).
- [ ] 11.3 **BLOCKED — Docker is not installed on this laptop** (confirmed: not found natively on
      Windows, not found in WSL Ubuntu either — `docker --version` fails in both). This contradicts
      CLAUDE.md's stated environment ("Windows 11 with WSL2 / Docker Desktop"). Cannot bring the
      stack up, complete the Chatwoot setup wizard, or generate a real `CHATWOOT_API_TOKEN` until
      Docker Desktop is installed. Task 12 (manual curl against a live Chatwoot) is transitively
      blocked by this too. Flagged to the user; not silently skipped or faked.

## 12. Bridge: Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

**Partially blocked by 11.3 (Docker not installed)** — everything not requiring a live Chatwoot was
executed; see `reports/2026-07-23-step-12-curl-verification.md` for full detail.

- [x] 12.1 Started the bridge locally against the real, running Hermes Gateway (`HERMES_MODEL`
      pointed at whichever profile is actually active today — `contexia`, confirmed via
      `GET /v1/models` — since `taty-v1` is a configurable value, not hardcoded)
- [x] 12.2 `curl http://127.0.0.1:8090/` → 200, confirmed real Hermes connectivity
- [ ] 12.3 **BLOCKED** — needs a live Chatwoot conversation to verify (see 11.3)
- [x] 12.4 `outgoing` payload → `{"status":"skipped"}`, verified
- [ ] 12.5 **BLOCKED** — needs the real Chatwoot API to toggle `bot_off` (see 11.3)
- [x] 12.6 Missing/wrong `WEBHOOK_TOKEN` → 401, verified (both cases)
- [x] 12.7 Documented in
      `openspec/changes/chatwoot-hermes-taty-bridge/reports/2026-07-23-step-12-curl-verification.md`
- [ ] 12.8 **N/A** — no real Chatwoot conversation/lead was created this session (see report)

## 13. Documentation

- [x] 13.1 Added a row for Chatwoot + `apps/chatwoot-bridge` to the containers table in
      `ARCHITECTURE.md`, noting the local-only deploy target and the Docker-not-installed blocker
- [x] 13.2 `apps/chatwoot-bridge/README.md`: env var reference, local startup sequence (including
      the Chatwoot one-time setup added this session), port map, troubleshooting (wrong Hermes
      profile, webhook token mismatch) — all present

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
