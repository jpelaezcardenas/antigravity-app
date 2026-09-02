# Design: hermes-jarvis-contexia

**Change:** hermes-jarvis-contexia  
**Date:** 2026-09-01  
**Status:** design

---

## Context

Contexia's backend (Railway `-175a`) already handles a Telegram bot for Taty (`telegram_endpoints.py`). Hermes runs locally on WSL with a cloudflared tunnel whose URL rotates on restart; `tunnel_persistent.ps1` auto-publishes the current URL to a Supabase table (`hermes_tunnel[id='current']`). The Búnker's "agentic-os" section renders a `ComingSoonSection`. `plan_features.py` has `freemium`, `starter`, `growth`, `enterprise` keys but Growth and Enterprise expose the same features as Starter — the pricing page already differentiates them.

This change adds three things on top of that foundation:
1. A personal Jarvis bot on Telegram that proxies to Hermes and sends a proactive morning brief
2. A real "Agentic OS" section in the Búnker with Hermes status, chat, and cron monitor
3. Proper feature flags (`jarvis_chat`, `jarvis_voice`) and display names per tier

---

## Goals / Non-Goals

**Goals:**
- Founder can message a Telegram bot and get a Hermes-powered response
- Founder receives a daily brief at 9:00 AM COT aggregating financial + commercial context
- Búnker "Agentic OS" renders real components (not "coming soon") for admin and tier-gated for clients
- `plan_features.py` differentiates `starter` vs `growth` vs `enterprise` correctly
- Frontend shows correct display names ("GPS Financiero", "Contexia Total") per tier

**Non-Goals:**
- Customer Jarvis routing (Fase D) — separate change after Fase A validates roundtrip
- DB key rename (`growth` → `pro`) — separate migration
- VoiceBox local proxy — Phase 2 after Fase B ships
- Write-back to Hermes from the Búnker chat (this change is read + ask only)
- Full bidirectional Hermes ↔ Manus Command Center — separate change

---

## Decisions

### D1 — Hermes gateway URL: dynamic Supabase lookup, not a static env var

**Decision:** Railway backend resolves the Hermes tunnel URL at request time by reading `hermes_tunnel` from Supabase using `SUPABASE_ANON_KEY`. URL is cached in-process for 30 seconds (same pattern as the Vercel `api/hermes/status` route described in the proposal).

**Why not a static `HERMES_GATEWAY_URL` env var?** The cloudflared tunnel rotates on restart. A static env var requires a Railway redeploy every time the tunnel restarts — which defeats the purpose of the auto-restart VBS in Windows Startup. The Supabase lookup adds ~50ms per cache miss (every 30s), negligible compared to Hermes inference latency (~2-10s).

**Auth for the lookup:** uses `SUPABASE_SERVICE_ROLE_KEY` (already present in Railway as `SUPABASE_SERVICE_ROLE_KEY`). No new env var needed. `hermes_tunnel` contains only the gateway URL — no client data — so service-role is acceptable here.

**Implementation:**
```python
# apps/backend/core/hermes_gateway.py  (new helper, ~30 lines)
import time, httpx
from core.supabase_client import get_supabase_service

_cache: dict = {"url": None, "ts": 0}
CACHE_TTL = 30  # seconds

async def resolve_hermes_gateway_url() -> str:
    if time.time() - _cache["ts"] < CACHE_TTL and _cache["url"]:
        return _cache["url"]
    client = get_supabase_service()  # uses SUPABASE_SERVICE_ROLE_KEY (already in Railway)
    row = client.table("hermes_tunnel").select("url").eq("id", "current").single().execute()
    url = row.data["url"]
    _cache.update({"url": url, "ts": time.time()})
    return url
```

**Fallback:** if `hermes_tunnel` has no row or Supabase is unreachable, raise `503` — never fall back to a stale static URL, since the tunnel URL changes per restart.

---

### D2 — Telegram webhook auth: HMAC-SHA256 secret header (same as Taty)

**Decision:** Validate the `X-Telegram-Bot-Api-Secret-Token` header (Telegram's built-in webhook secret mechanism) using `TELEGRAM_WEBHOOK_SECRET_JARVIS`. Reuse the same HMAC comparison pattern from `telegram_endpoints.py`.

**Why separate secret from Taty?** Two bots, two webhook URLs, two secret tokens. Sharing a secret between bots reduces blast radius of a leak — a leaked Jarvis secret doesn't compromise Taty's webhook.

**Jarvis-specific auth addition:** after validating the Telegram secret, check that the `chat.id` of the incoming message matches `TELEGRAM_JUAN_DAVID_CHAT_ID`. Unknown chat IDs get a 200 OK with no action (Telegram expects 200; returning 4xx causes retries). This prevents any Telegram user who discovers the bot from getting Hermes responses.

---

### D3 — Hermes call protocol: POST /api/run (non-streaming for Telegram, streaming for Búnker chat)

**Decision:**  
- **Telegram webhook path (Fase A):** call `POST <gateway>/api/run` with a JSON body containing the user message and a system prompt identifying the caller as the founder with admin context over all tenants. Wait for the full response (non-streaming). Hermes response time is ~2-10s — within Telegram's 60s webhook timeout. Acceptable.
- **Búnker chat path (Fase B):** call `POST <gateway>/api/run` and stream the response via Server-Sent Events to the browser. The SSE endpoint in the backend (`POST /api/v1/jarvis/chat`) opens a streaming `httpx` connection to Hermes and relays chunks.

**Why not streaming for Telegram?** Telegram's Bot API doesn't support SSE or streaming replies — you can only send one message per `sendMessage` call. To simulate streaming, you'd have to `editMessage` repeatedly, which adds complexity for no UX gain. Full-response is simpler and reliable within the 60s timeout.

**Why SSE (not WebSocket) for Búnker?** The Búnker is a Next.js static export — no persistent server-side state. SSE fits the unidirectional "server pushes chunks to browser" pattern perfectly. WebSocket would require either a WS-capable deployment (not static Vercel) or a relay, adding unnecessary complexity.

---

### D4 — Jarvis endpoint layout: one file, four routes

**Decision:** create a single `apps/backend/presentation/jarvis_endpoints.py` with prefix `/channels/jarvis` for the Telegram webhook, and prefix `/jarvis` for the chat/status/brief API routes. Registered in `router.py` with two `include_router` calls (one per prefix).

```
POST /api/v1/channels/jarvis/webhook   → receive Telegram update, reply via sendMessage
POST /api/v1/jarvis/chat               → proxy message to Hermes, SSE streaming, gated by jarvis_chat
GET  /api/v1/jarvis/status             → proxy to Hermes /health, admin-only
POST /api/v1/jarvis/brief              → aggregate financial context, called by Hermes cron
```

**Why not two files?** The Telegram webhook and the Búnker chat share the same `resolve_hermes_gateway_url()` dependency. One file avoids circular imports and keeps all Jarvis logic in one place — easier to deprecate later when Fase D absorbs this into Taty routing.

---

### D5 — Brief aggregation: parallel calls, Manus fail-graceful

**Decision:** `POST /api/v1/jarvis/brief` makes two async calls concurrently:
1. **Financial context** — reads from Railway's own DB (Supabase) via service-role: Caja Real across all tenants, active Centinela alerts, pending Approval Queue items. This NEVER fails silently — if the DB is unreachable, the brief endpoint returns `503`.
2. **Commercial context** — `GET http://localhost:<MANUS_PORT>/api/brief/context` (or the confirmed Manus endpoint). This call has a 5s timeout and is fail-graceful: if Manus doesn't respond, the brief omits the commercial section with a note "Manus no disponible."

**Why not always require Manus?** Manus is a separate process on a separate machine (or the same laptop). A network partition or Manus restart shouldn't block the founder from seeing their financial brief. The financial data is the critical path; the commercial context is additive.

**Note:** `MANUS_INTERNAL_URL` is a new env var on Railway pointing to Manus's HTTP endpoint. Its value must be confirmed with Manus before implementation of the brief cron (Task 7c). The brief endpoint guards against this: if `MANUS_INTERNAL_URL` is not set, the commercial section is simply omitted.

---

### D6 — Frontend: AgenticOsSection feature-gated, not admin-only

**Decision:** "agentic-os" is NOT added to `ADMIN_ONLY_SECTIONS` in `BunkerSidebar.tsx`. Per ARCHITECTURE.md Decision #18, B2B clients see Dashboard + Agentic OS + Configuración. The feature gate is inside `AgenticOsSection.tsx` based on the tenant's `plan_tier` from `fetchTenantMe()`.

```
freemium / starter → <JarvisLockedState> with upgrade CTA
growth             → <JarvisChatInterface> (text only)
enterprise         → <JarvisChatInterface> + <VoiceToggle>
admin              → <JarvisChatInterface> + <VoiceToggle> + <CronJobsMonitor> (admin-only card)
```

`AgenticOsSection` calls `fetchTenantMe()` on mount (already used by `TenantInfoCard` — same endpoint, no new API call shape). Deduplication: if `TenantInfoCard` is visible on the same page, both components independently fetch `/api/v1/tenant/me` — acceptable, since this endpoint is fast (~50ms) and read-only.

---

### D7 — VoiceToggle: browser Web Speech API only (Phase 1)

**Decision:** `VoiceToggle.tsx` uses `window.SpeechRecognition` (Chrome/Edge) or `window.webkitSpeechRecognition` for input, and `window.speechSynthesis` for output. Zero external dependencies, zero configuration. Degrades gracefully on Firefox (button hidden if `SpeechRecognition` is unavailable).

**Why not VoiceBox in this change?** VoiceBox runs on Windows at port `17493` — the Búnker runs in a browser that cannot reach `localhost:17493` from Vercel's origin. A local CORS proxy script is a Phase 2 addition. Browser speech is sufficient for the initial UX validation.

---

### D8 — plan_features.py: additive change, no key renames

**Decision:** add `jarvis_chat` and `jarvis_voice` to the feature sets; differentiate tiers by removing features from lower tiers that should only be in higher ones. DB keys (`freemium`, `starter`, `growth`, `enterprise`) are NOT renamed in this change.

```python
PLAN_FEATURES = {
    "freemium":   frozenset({"pulso_diario"}),
    "starter":    frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge"}),
    "growth":     frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge", "jarvis_chat"}),
    "enterprise": frozenset({"pulso_diario", "centinela_alerts", "liquidity_bridge", "jarvis_chat", "jarvis_voice"}),
}
```

**Why not rename keys now?** A DB key rename requires a migration touching `tenants.plan_tier` + `b2b_clients.plan_tier` + all code references. That's a separate, higher-risk change. The display name change (UI only, no DB) is safe to do here.

---

## Sequence Diagrams

### Fase A — Telegram message roundtrip

```
User → Telegram → POST /api/v1/channels/jarvis/webhook (Railway)
                          │
                    validate HMAC secret
                    validate chat_id == TELEGRAM_JUAN_DAVID_CHAT_ID
                          │
                    resolve_hermes_gateway_url()  ← Supabase hermes_tunnel
                          │
                    POST <gateway>/api/run
                       {message, system_prompt: "You are Jarvis, admin context"}
                          │ (2-10s Hermes inference)
                          │
                    POST api.telegram.org/sendMessage
                       {chat_id, text: hermes_response}
                          │
                   return 200 OK to Telegram
```

### Fase A — Morning brief cron

```
Hermes cron (9:00 AM COT)
  └─ jarvis-morning-brief.sh
       ├─ POST Railway /api/v1/jarvis/brief
       │    ├─ GET Supabase: caja_real per tenant (service_role)
       │    ├─ GET Supabase: centinela_alerts (active, all tenants)
       │    └─ GET Supabase: approval_queue (pending)
       │
       ├─ GET Manus /api/brief/context  [timeout: 5s, fail-graceful]
       │    ├─ HubSpot pipeline summary
       │    ├─ Gmail priority threads
       │    └─ Meta Ads last 24h
       │
       └─ Hermes aggregates both payloads → drafts brief
            └─ POST api.telegram.org/sendMessage → TELEGRAM_JUAN_DAVID_CHAT_ID
```

### Fase B — Búnker chat (SSE streaming)

```
Browser (AgenticOsSection)
  └─ POST /api/v1/jarvis/chat  {message: "..."}
       │  Authorization: Bearer <token>
       │  has_feature(tenant, "jarvis_chat") check
       │
  Railway backend opens SSE response
       └─ POST <gateway>/api/run  (streaming httpx)
            └─ chunk by chunk → SSE events → browser
                └─ JarvisChatInterface appends to chat bubble
```

---

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Hermes tunnel URL stale (30s cache) | Cache miss triggers fresh lookup; 30s window is acceptable for interactive chat (worst case: first message after tunnel restart takes 1 extra Supabase round-trip) |
| Manus endpoint unknown / changes | `MANUS_INTERNAL_URL` env var + fail-graceful; brief still works without commercial context. Task 7a is explicitly gated on founder confirming the endpoint shape with Manus before implementation |
| Hermes inference timeout on Telegram (60s hard limit) | Hermes on Phi-4 / Qwen 3 8B responds in 2-10s for typical questions. If it exceeds 60s, Telegram retries the webhook. Mitigation: set a 55s `httpx` timeout on the Hermes call; on timeout, send a Telegram message "Tardando más de lo habitual..." and let the retry complete |
| `chat_id` allowlist too rigid | Initially only `TELEGRAM_JUAN_DAVID_CHAT_ID` is allowed. Adding other trusted chats requires a new env var or a `hermes_jarvis_allowed_chats` Supabase table — documented as a follow-up, not in scope here |
| SSE streaming not supported in older browsers | VoiceToggle degrades gracefully; SSE has broad support (Chrome, Firefox, Safari, Edge). Fallback: if SSE fails, client retries as a regular POST and displays the full response on completion |
| Plan features change breaks existing clients | `plan_features.py` change is additive (new features added to Growth/Enterprise). Starter clients lose nothing — they didn't have `jarvis_chat` before, and they still don't. Test: run existing test suite against updated `plan_features.py` before deploy |

---

## Migration Plan

No DB migrations required for this change.

**Deploy order (Stage 11):**

1. Backend: add new env vars to Railway → deploy `jarvis_endpoints.py` + updated `plan_features.py` + updated `config.py`
2. Verify: `POST /api/v1/jarvis/status` returns 200 with Hermes health (requires tunnel running)
3. Register Telegram webhook (founder action): `curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook -d 'url=https://antigravity-app-production-175a.up.railway.app/api/v1/channels/jarvis/webhook&secret_token=<SECRET>'`
4. Smoke test Fase A: send message to Jarvis bot → confirm Hermes response in Telegram
5. Frontend: deploy updated `contexia-app` with AgenticOsSection components, `page.tsx` change, display name updates
6. Verify: login to Búnker → Agentic OS section visible → HermesStatusCard shows gateway health
7. Hermes (WSL): create `jarvis-personal.md` skill + `jarvis-morning-brief.sh` + register cron in `jobs.json`
8. Smoke test brief: trigger cron manually → confirm Telegram message received

**Rollback:**
- Backend: remove jarvis router registration from `router.py` + redeploy (2 min). Gateway resolution helper is pure utility — safe to leave in place.
- Frontend: revert `page.tsx` to add "agentic-os" back to `PLACEHOLDER_SECTIONS` + redeploy.
- Telegram: `deleteWebhook` on the Jarvis bot token.

---

## Open Questions

| # | Question | Blocking? | Owner |
|---|---|---|---|
| OQ1 | What is the exact Manus endpoint shape for `GET /api/brief/context`? What fields does it return? | Blocks Task 7c (brief cron, commercial section) | Fundador confirms with Manus |
| OQ2 | ~~Does `SUPABASE_ANON_KEY` exist as a Railway env var?~~ **CLOSED (2026-09-01):** `SUPABASE_ANON_KEY` does NOT exist in Railway; decision is to use `SUPABASE_SERVICE_ROLE_KEY` (already present) for the `hermes_tunnel` lookup. D1 updated accordingly. | ~~Blocks D1~~ **Resolved** | — |
| OQ3 | What Hermes model / profile should `jarvis-personal.md` target? (MiMo, or the OmniRoute fallback chain?) | Blocks Task 6 (Hermes skill) | Fundador decides; default: inherit from `contexia` profile |
| OQ4 | Should `CronJobsMonitor` read cron job status from a Supabase table (requires Hermes to write last-run timestamps) or from a static `jobs.json` endpoint? | Blocks Task 9 (Búnker UI) | Design preference; recommendation: static `jobs.json` served by the backend for now |
