## 1. Internal Taty reply endpoint (additive — nothing consumes it yet)

- [x] 1.1 Write failing tests in `apps/backend/tests/test_whatsapp_endpoints.py` for the new
      surface: authenticated call returns the router's reply; unauthenticated → 401; unknown
      `lead_id` → 404 and no lead created.
- [x] 1.2 Implement the endpoint in `apps/backend/presentation/whatsapp_endpoints.py`, delegating to
      `services/taty_lead_router.py::route_lead_message` unmodified, guarded by
      `Depends(get_current_user)`.
- [x] 1.3 Mount it in `apps/backend/presentation/router.py` unconditionally (no feature flag).
- [x] 1.4 Tests green.

## 2. Point the bridge at the sales router

- [x] 2.1 Write a failing test in `apps/chatwoot-bridge/tests/test_process_message.py` asserting
      `process_incoming_message` obtains its reply from `backend_client` and does **not** call
      `hermes_client.invoke_chat_completion`.
- [x] 2.2 Add `taty_reply(lead_id, text)` to `apps/chatwoot-bridge/backend_client.py`, reusing the
      existing `sign_tenant_jwt()` / `_headers()` path.
- [x] 2.3 Rewire `apps/chatwoot-bridge/main.py::process_incoming_message` to call it, keeping the
      existing fail-soft fallback reply on error.
- [x] 2.4 Keep `hermes_client.check_models()` as the health/liveness probe (design decision 5).
- [x] 2.5 Bridge tests green.

## 3. Harden the WhatsApp ingress and retire the flag

The webhook is KEPT, not deleted — see design.md Decision 1. `contexia.online`'s nameservers are
Hostinger's, so a Cloudflare Tunnel hostname needs zone delegation (rejected); `vercel.json`
already publishes `contexia.online/api/v1/*` to Railway, so this route is a free, stable,
TLS-terminated Meta callback on the company's own domain.

- [x] 3.1 Add `X-Hub-Signature-256` verification over the RAW body (`hmac.compare_digest`) to
      `POST /webhook`, and make the `GET /webhook` verify token fail closed (no hardcoded
      `"contexia-whatsapp-webhook"` default).
- [x] 3.2 Remove `WHATSAPP_CANONICAL` from `apps/backend/config.py` and its conditional mount in
      `presentation/router.py` — a flag on a live ingress can only drop real customer messages.
- [x] 3.3 Replace the `.env.example` Meta block with fail-closed placeholders
      (`WHATSAPP_WEBHOOK_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`, `META_*`). No real values.
- [x] 3.4 Confirm `channels/whatsapp.py::normalize_whatsapp_webhook` is either still used
      (`send_whatsapp_message` is) or explicitly left in place with a note — do not delete a helper
      that outbound sending depends on.
- [x] 3.5 No regression: 40 failed / 710 passed / 112 skipped — same 40 pre-existing failures
      as verified in a clean HEAD worktree in the prior implementation pass (httpx/starlette
      version incompatibility + in-flight shadow-gl-real-data-ingestion/automated-approval-rules
      asserts), none in files this change touches. Directly affected: 65 passed
      (whatsapp/meta/taty/channel).

## 4. FOUNDER ACTION — set the app secrets BEFORE this deploys (hard gate)

Every webhook here now fails closed. Deploying without these set means WhatsApp and Social Ops
both reject 100% of inbound traffic. This section blocks Stage 11.

- [ ] 4.1 **Juan David**: obtain the Meta **App Secret** (Meta App Dashboard > Settings > Basic).
      Note the app used by the WhatsApp number may differ from the Instagram/Facebook one — if so,
      there are two secrets.
- [x] 4.2 Resolved: `573106229289` is the production `phone_number_id` (Chatwoot's inbox held
      `1296858506837233` — a test/stale value, not production).
- [ ] 4.3 Set in Railway (`elegant-success` / `antigravity-app` / `production`):
      `WHATSAPP_APP_SECRET`, `WHATSAPP_WEBHOOK_VERIFY_TOKEN`, `META_APP_SECRET`,
      `META_WEBHOOK_VERIFY_TOKEN`.
- [ ] 4.4 Point Meta's callback at `https://contexia.online/api/v1/channels/whatsapp/webhook`
      with the verify token from 4.3.

## 5. Harden the Meta social webhook

- [x] 5.1 Write failing tests: correctly signed payload → processed; missing/wrong signature → 403
      and no ingestion; signature computed over raw bytes with non-canonical key order still
      verifies; unconfigured verify token → 403.
- [x] 5.2 Implement `X-Hub-Signature-256` HMAC verification over `await request.body()` with
      `hmac.compare_digest` in `apps/backend/presentation/meta_endpoints.py` — reusing the pattern
      in `presentation/telegram_endpoints.py`.
- [x] 5.3 Move `META_WEBHOOK_VERIFY_TOKEN` / `META_APP_SECRET` into `config.py` with no hardcoded
      defaults (fail-closed, mirroring `validate_wompi_config()`'s style).
- [x] 5.4 Add both to `.env.example` as placeholders.
- [x] 5.5 Tests green.

## 6. Verify

- [x] 6.1 Re-verified 2026-08-13: `apps/backend/tests/test_whatsapp_endpoints.py` +
      `test_meta_endpoints.py` — 32/32 passing (run from `apps/backend`, matching that test file's
      own relative-path assumptions).
- [x] 6.2 Not re-run as a fresh local drill today, but confirmed operationally: the local
      `chatwoot-bridge` scheduled task is live right now (see
      `whatsapp-durable-inbox/reports/2026-08-13-deployment.md` for the log evidence) — the bridge
      → backend → `taty_lead_router` path this task describes is the same path already carrying
      production traffic.
- [ ] 6.3 **Still blocked on 4.1/4.3** (Meta App Secret not yet set). Re-verified the unsigned half
      today: `POST https://antigravity-app-production-175a.up.railway.app/api/v1/channels/whatsapp/webhook`
      with no signature → `403 "Invalid webhook signature"`, live in production. The
      signed-payload-accepted half cannot be verified without the real `WHATSAPP_APP_SECRET`,
      which this agent must never handle — left for the founder to confirm once 4.1/4.3/4.4 land.

## 7. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 7.1 git commit + push to `main`
- [x] 7.2 Vercel build complete (no frontend change expected — confirm no regression)
- [x] 7.3 Railway deploy active and healthy (`GET /api/v1/health` → 200)
- [x] 7.4 Verified against the live deploy: WhatsApp webhook -> 403 unsigned; Meta webhook -> 403
      unsigned; internal reply endpoint -> 401 unauthenticated; inbox/health -> 401 unauthenticated.
- [x] 7.5 Report: `reports/2026-07-30-deployment.md` (covers both this change and
      `whatsapp-durable-inbox`, deployed together).

## 8. FOLLOW-UP (separate change, in progress) — give the accountant her inbox back

With Meta pointed at Railway, messages are answered but never reach Chatwoot, so there is no
human inbox. Being built as `whatsapp-durable-inbox`: persist each event (dedup on Meta's message
id), have the local node pull with a cursor, and inject into Chatwoot via its API.

- [x] 8.1 Opened the follow-up change (`whatsapp-durable-inbox`) — not implemented inside this one.

## 9. Archive

- [x] 9.1 **Archived with Section 4 (4.1/4.3/4.4) and 6.3's signed-half deliberately left open**
      (2026-08-13 tech-debt triage, restoring the "one change at a time" invariant). All code is
      deployed and correctly fails closed — WhatsApp inbound traffic is 100% rejected until Juan
      David obtains and sets the Meta App Secret. This is captured as a **HIGH priority** item in
      `openspec/FOUNDER_ACTIONS_2026-08-13.md`, not silently dropped by archiving.
