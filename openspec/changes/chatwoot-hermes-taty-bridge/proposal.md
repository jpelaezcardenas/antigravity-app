## Why

Taty (the conversational operator) currently reaches WhatsApp only through Telegram-adjacent tooling; there is no first-class, self-hosted WhatsApp channel. Contexia's data-sovereignty decision (ARCHITECTURE.md #1) rules out SaaS inbox tools (HubSpot-style) that would route PyME financial conversations through third-party clouds. This change stands up a local WhatsApp channel — Chatwoot (official Meta WhatsApp Cloud API) bridged to the already-running local Hermes Gateway `taty-v1` profile — so leads and clients can talk to Taty 24/7 with a human (Tatiana/Juan David) able to take over any conversation instantly via a `bot_off` label. It runs today on the founder's MVP laptop and is built to migrate to the future AI Workstation/NAS by env-var swap only, with zero code changes.

## What Changes

- New local infra: `docker-compose.chatwoot.yml` (Chatwoot web + worker + postgres/pgvector + redis), ports chosen to avoid collision with existing local services (Chatwoot `:3020`; Hermes Gateway already on `:8642`; backend dev `:8080`).
- New service `apps/chatwoot-bridge/`: a FastAPI webhook bridge that filters Chatwoot events (incoming-only, loop prevention), honors an `bot_off` HITL pause label, fetches recent conversation history, invokes Hermes Gateway's OpenAI-compatible `/v1/chat/completions` API under the `taty-v1` model/profile, and dispatches the reply back to Chatwoot.
- New backend endpoint `POST /api/v1/crm/leads/whatsapp-intake` (find-or-create a lead by `whatsapp_phone`, tenant-scoped) so a first-time WhatsApp contact is registered and routed into the existing onboarding flow (`/api/v1/social-ops/onboarding/start`).
- `ARCHITECTURE.md` containers table gains a row for the Chatwoot + bridge components.
- **Non-goal for this change** (explicitly deferred): audio/voice-note transcription (FFmpeg + Faster-Whisper) — this laptop has no GPU; the bridge replies with a graceful Spanish fallback to voice notes for now. Instagram channel and actual Workstation/NAS hardware migration are also out of scope; only env-var-driven portability is designed in.
- No **BREAKING** changes — this is new, additive surface area.

## Capabilities

### New Capabilities
- `chatwoot-hermes-bridge`: webhook ingestion from Chatwoot, event filtering/loop prevention, `bot_off` HITL pause, conversation-history assembly, Hermes `taty-v1` invocation, reply dispatch, graceful degradation (Hermes/CRM unreachable, audio attachments).

### Modified Capabilities
- `crm-b2c-sell-machine`: adds a WhatsApp-lead intake requirement (find-or-create by `whatsapp_phone`, tenant-scoped, triggers onboarding for new contacts) alongside existing lead-pipeline requirements.

## Impact

- New: `docker-compose.chatwoot.yml`, `apps/chatwoot-bridge/**` (FastAPI app + tests + `.env.example`).
- Modified: `apps/backend/presentation/crm_endpoints.py`, `apps/backend/services/crm_service.py`, `apps/backend/tests/` (new test file), `ARCHITECTURE.md`.
- Dependencies: Chatwoot (self-hosted Docker), local Hermes Gateway (`taty-v1` profile, already running at `127.0.0.1:8642`), Supabase (`leads` table via `crm_service.py`), Meta WhatsApp Cloud API (via Chatwoot inbox config, requires a Cloudflare Tunnel to expose the local Chatwoot webhook — not built in this change, documented as a deployment step).
- Deploy split: the new backend endpoint deploys normally to Railway `-175a` on push to `main`; Chatwoot + the bridge deploy **locally** to this laptop (their production target, per the sovereignty decision) — Stage 11 for this change documents the local runbook instead of a Vercel/Railway checklist for those two pieces.
