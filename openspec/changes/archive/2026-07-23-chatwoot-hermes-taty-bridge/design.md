## Context

Taty (`taty-v1`) already runs as a local Hermes Gateway profile (verified live: `hermes-agent v0.17.0` responding on `127.0.0.1:8642`, `GET /v1/models` returns the served profile, `API_SERVER_KEY` set in `profile.yaml`/`config.yaml`). No WhatsApp channel exists yet. The Telegram bridge (`apps/backend/presentation/telegram_endpoints.py`) is the closest precedent for a chat-channel-to-backend integration: signature/token check → event filter → background processing → reply dispatch.

**Correction to the originally proposed design**: an early draft assumed Hermes exposes `POST /api/v1/agents/taty/invoke`. Live probing shows this path does not exist (404). Hermes's `API_SERVER_ENABLED: true` config exposes an **OpenAI-compatible** surface instead: `POST /v1/chat/completions` (confirmed `405` on GET, i.e. route exists), `GET /v1/models` (confirmed `200` with bearer auth). The bridge must speak this contract, not a bespoke `/invoke` endpoint. Hermes owns model routing internally (`taty-v1` → GLM 5.2 interactive, per ARCHITECTURE.md decision #7) — the bridge never talks to Ollama or any LLM provider directly.

Constraint: this runs today on the founder's single laptop (Core i7, 16GB RAM, 1TB SSD, Windows 11 + WSL2 + Docker Desktop, no GPU) sharing resources with Hermes Gateway, Next.js dev server, and the local backend. Local ports already in use: `:3000` (Next.js / Hermes Workspace UI), `:8080` (local backend dev), `:8642` (Hermes Gateway).

## Goals / Non-Goals

**Goals:**
- Stand up a self-hosted Chatwoot inbox wired to the official WhatsApp Cloud API, so no client conversation data leaves sovereign infrastructure (ARCHITECTURE.md decision #1 applies transitively — Taty's brain is local Hermes, and the inbox must be local too for the same reason).
- Build a FastAPI bridge that is a thin, stateless transport layer: Chatwoot event → filter/HITL check → history → Hermes chat-completion → Chatwoot reply. No business logic duplicated from the backend.
- Register new WhatsApp contacts as leads and kick off the existing onboarding flow, reusing `crm_service.py` and `social_ops_endpoints.py` rather than inventing parallel state.
- Make every environment-specific value (Chatwoot URL, Hermes URL, backend URL, future Whisper URL) an env var, so migrating to the future AI Workstation/NAS is a config change, never a code change.
- Fail closed on secrets (empty env var ⇒ refuse to start or refuse the call, never a hardcoded fallback secret) — mirrors ARCHITECTURE.md decision #11 (demo-admin password incident).

**Non-Goals (this change):**
- Audio/voice-note transcription (FFmpeg + Faster-Whisper). No GPU on this laptop; the bridge detects `file_type == "audio"` and replies with a fixed Spanish fallback message instead of attempting transcription. The env var `LOCAL_WHISPER_URL` is reserved (documented, unused) so phase 2 doesn't require re-touching config plumbing.
- Instagram or other Chatwoot channels — WhatsApp only.
- Provisioning the actual AI Workstation/NAS hardware, or a live migration — only the *capability* to migrate via env vars is designed in.
- Exposing the local Chatwoot webhook publicly (Cloudflare Tunnel setup) — documented as a manual deployment step, not built/automated here.

## Decisions

1. **Hermes contract = OpenAI-compatible chat completions, not a bespoke `/invoke` route.**
   `POST {HERMES_GATEWAY_URL}/v1/chat/completions` with `Authorization: Bearer {HERMES_API_KEY}`, body `{"model": "taty-v1", "messages": [...history, current], "stream": false}`. Alternative considered: a custom `/api/v1/agents/taty/invoke` route added to Hermes itself — rejected because it requires touching Hermes's own codebase (out of this repo, out of scope) when the standard API already does the job.

2. **Bridge lives at `apps/chatwoot-bridge/` inside the monorepo**, not a sibling repo. Alternative considered: sibling repo (like `contexia-brain`), isolating it from the Vercel/Railway auto-deploy-on-push pipeline. Rejected: unlike GBrain (which auto-commits on a schedule and would trigger unwanted deploys), this bridge is developed like normal application code and never deploys to Railway/Vercel at all — it has no auto-deploy trigger to avoid. Monorepo placement keeps it under the same OpenSpec/harness governance as everything else and matches the `apps/backend` precedent.

3. **Loop-prevention & HITL are enforced in the webhook handler, before any background work is scheduled.** Truth table:
   | event | message_type | private | `bot_off` label | Action |
   |---|---|---|---|---|
   | `message_created` | `incoming` | false | absent | process (Hermes) |
   | `message_created` | `incoming` | false | present | `{"status":"paused"}`, no Hermes call |
   | `message_created` | `incoming` | true | — | skip (agent private note) |
   | `message_created` | `outgoing` | — | — | skip (would create an infinite loop) |
   | anything else | — | — | — | skip |
   Alternative considered: filtering only on `event`/`message_type` (as in the original prompt) — insufficient, because Chatwoot also fires `message_created` for **private notes** agents leave for each other; without the `private` check those would be sent to Hermes as if they were customer messages.

4. **Webhook authenticity**: Chatwoot does not sign webhook payloads by default. The bridge requires a shared `WEBHOOK_TOKEN` passed as a query param or `X-Webhook-Token` header (configured on the Chatwoot webhook URL), rejecting with `401` on mismatch. This is deliberately simple (matches Chatwoot's actual capabilities) rather than inventing HMAC verification Chatwoot doesn't send.

5. **New-lead intake reuses, not duplicates, CRM state — and does NOT trigger company onboarding.** `POST /api/v1/crm/leads/whatsapp-intake` does a tenant-scoped find-or-create against the same `leads` table `b2c_pipeline`/`advance_lead` already operate on (`crm_service.py`), keyed on normalized `whatsapp_phone`. On creation, the bridge only tags the Chatwoot contact's custom attributes (`tipo_lead`, `estado: "nuevo"`) — it does **not** call `POST /api/v1/social-ops/onboarding/start`.
   **Correction (2026-07-23, pre-archive):** the original version of this decision had the bridge call `onboarding/start` on first WhatsApp contact. That endpoint's `OnboardingStartRequest` (`company_name`, `customer_email`, `payment_reference`) is the **B2B/paid-customer 21-day workspace onboarding** flow (creates a workspace, seeds `telegram`/`instagram`/`linkedin` channels) — it runs *after* a sale closes, not when a lead's very first WhatsApp message arrives. A brand-new `NUEVOS`-stage B2C lead has none of those fields yet, so the call always 422s (confirmed: `apps/chatwoot-bridge/backend_client.py`'s `trigger_onboarding()` posts an empty body and relies on the fail-soft contract in decision 7 to swallow the resulting error — functionally a silent no-op). The fix is not "relax the endpoint's required fields" or "have the bridge collect more info first" — it's that this call point is simply wrong: a fresh WhatsApp lead should just have a normal qualifying conversation with Taty (via Hermes), the same as any other B2C channel. Company/workspace onboarding belongs at the point a sale actually closes (the `approve_payment` step in `crm-b2c-sell-machine`, where `payment_reference` genuinely exists) — wiring that up is out of scope for this change and left as a separate future change against `crm-b2c-sell-machine`, not something the WhatsApp bridge should own or attempt.

6. **Bridge → backend auth**: HS256 JWT with a `tenant_id` claim, signed with a shared secret (`CONTEXIA_JWT_SECRET`), following the exact contract already documented for Hermes operators in `openspec/changes/hermes-multi-tenant-wrapper/HERMES_CONFIG.md` (`sub`, `tenant_id`, `exp`). Reusing this contract means `TenantContextMiddleware` and Supabase RLS need zero changes.

7. **Graceful degradation over hard failure.** If the CRM intake call or onboarding trigger fails, the bridge logs and continues to the Hermes reply — a WhatsApp conversation must never go silent because an internal service is down. If Hermes itself times out (60s) or errors, the bridge sends a fixed Spanish apology message rather than leaving the customer with no reply at all.

8. **Port plan**: Chatwoot `:3020` (avoids Next.js/Hermes Workspace `:3000`), bridge `:8090` (avoids backend dev `:8080`), Hermes Gateway stays on its existing `:8642`. All overridable via env vars.

9. **RAM budget on the laptop**: Chatwoot (web + worker) + Postgres + Redis inside Docker Desktop/WSL2 ≈ 3–3.5GB; bridge ≈ 150MB. No local LLM inference is added by this change (Hermes already routes `taty-v1` to cloud GLM 5.2), so this change adds orchestration load only, not inference load — safe within the existing 16GB budget alongside Next.js dev + backend dev + Hermes Gateway.

## Risks / Trade-offs

- **[Risk] Hermes Gateway not running `taty-v1` when the bridge starts** (a different profile could be active, since only one profile serves `:8642` at a time) → **Mitigation**: bridge logs `GET /v1/models` at startup and on each Hermes call failure, making a wrong-profile gateway immediately visible in logs; deployment runbook documents starting Hermes with `-p taty-v1` explicitly.
- **[Risk] Chatwoot webhook reachability from Meta's WhatsApp Cloud API requires a public tunnel** (Cloudflare Tunnel), which is a manual, non-automated step and a single point of failure for the whole channel → **Mitigation**: documented explicitly as a Stage 11 deployment step with a health-check command; out of scope to automate in this change.
- **[Risk] No audio support in phase 1** may frustrate WhatsApp users who default to voice notes → **Mitigation**: bridge replies with a clear, friendly Spanish message asking for text, rather than silently dropping the message; `LOCAL_WHISPER_URL` reserved so phase 2 is additive.
- **[Risk] Single point of laptop failure** (no redundancy, no supervisor) — if the bridge or Chatwoot crashes, WhatsApp goes dark with no automatic restart → **Mitigation**: out of scope for MVP; documented as a known limitation, revisit when migrating to the Workstation (systemd/Docker restart policies, following the `gbrain-autopilot.service` `Restart=always` precedent).
- **[Trade-off] JWT shared-secret auth (not OAuth) between bridge and backend** — simpler, consistent with the existing Hermes-operator contract, but requires careful secret handling (env var only, never committed) — accepted, matches existing pattern.

## Migration Plan

1. Land backend endpoint first (independently testable, deploys via normal Railway pipeline on merge to `main` — no coordination needed with the bridge).
2. Bring up `docker-compose.chatwoot.yml` locally, complete Chatwoot's one-time setup wizard, create the WhatsApp Cloud API inbox.
3. Start the bridge locally, point its `.env` at the running Chatwoot + Hermes Gateway (`-p taty-v1`) + backend (local or Railway).
4. Wire the Chatwoot webhook URL (via a Cloudflare Tunnel once ready) with the shared `WEBHOOK_TOKEN`.
5. End-to-end smoke test per proposal's verification plan before enabling the WhatsApp number for real traffic.
6. Rollback: stop the bridge process and/or remove the Chatwoot webhook URL — Chatwoot keeps queuing/showing messages for human takeover with zero bot involvement; no data loss.

## Open Questions

- Exact WhatsApp Cloud API phone number / Meta Business verification status — assumed already provisioned per the original request; if not, that's a prerequisite outside this change's scope.
- Whether Chatwoot's Postgres should use a dedicated pgvector image now or plain Postgres (Chatwoot itself doesn't require pgvector for core inbox features) — defaulting to plain `postgres:15` unless a later Chatwoot feature requires vector search, to keep the image lighter on this laptop.
