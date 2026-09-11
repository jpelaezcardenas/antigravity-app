"""Environment-driven settings for the Chatwoot <-> Hermes (Taty) bridge.

All secrets default to empty strings (fail closed — no hardcoded fallback
secrets, per antigravity-app's ARCHITECTURE.md decision #11 / CLAUDE.md
incident rules). Every environment-specific value (Chatwoot URL, Hermes URL,
backend URL) is an env var so migrating to the future AI Workstation/NAS is a
config change, never a code change (design.md Goals).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Chatwoot
    CHATWOOT_URL: str = ""
    CHATWOOT_API_TOKEN: str = ""
    CHATWOOT_ACCOUNT_ID: str = "1"
    # The WhatsApp Cloud API inbox events get injected into (whatsapp-durable-inbox). Empty by
    # default so the poller stays inert until explicitly configured — never guesses an inbox id.
    CHATWOOT_WHATSAPP_INBOX_ID: str = ""

    # whatsapp-durable-inbox: interval (seconds) between pulls of the backend's durable queue.
    # A few seconds is invisible on WhatsApp, which is not a synchronous medium.
    INBOX_POLL_INTERVAL_SECONDS: float = 5.0
    # Whether the poller runs at all. Default off so the bridge can still run standalone
    # (design.md 4.4) — e.g. before the founder has set WHATSAPP_APP_SECRET in Railway.
    INBOX_POLLER_ENABLED: bool = False

    # Hermes Gateway (OpenAI-compatible chat completions surface, see design.md decision 1)
    HERMES_GATEWAY_URL: str = "http://localhost:8642"
    # Intentionally configurable — never hardcode "taty-v1" anywhere else in this service.
    HERMES_MODEL: str = "taty-v1"
    HERMES_API_KEY: str = ""

    # Contexia backend (Railway/local FastAPI)
    CONTEXIA_API_URL: str = ""
    CONTEXIA_JWT_SECRET: str = ""

    # Origin of the backend's /internal/* surface (voice-note, whatsapp/document). Found live
    # 2026-09-11: this must NOT be derived from CONTEXIA_API_URL's origin in production, because
    # CONTEXIA_API_URL there is https://contexia.online/api/v1 — contexia.online is Vercel, whose
    # vercel.json rewrites ONLY /api/v1/* to Railway; /internal/* has no rewrite rule there by
    # design (so it's never exposed to the public internet), so a request built from
    # CONTEXIA_API_URL's origin 404s on Vercel's own catch-all. This must point at Railway's
    # domain directly. Empty default so a misconfigured environment fails loudly (503-shaped,
    # matching send_voice_note/submit_whatsapp_document's existing "key not set" fail-closed
    # posture) rather than silently 404ing against the wrong host again.
    INTERNAL_API_BASE_URL: str = ""

    # HITL / conversation behavior
    PAUSE_LABEL: str = "bot_off"
    MAX_HISTORY: int = 10

    # Webhook auth (design.md decision 4)
    WEBHOOK_TOKEN: str = ""

    PORT: int = 8090

    # Reserved for phase 2 (audio transcription) — documented, unused (design.md Non-Goals).
    # Still unused: voicebox-local-voice-adoption ships OUTBOUND voice only. Inbound customer audio
    # remains refused (AUDIO_FALLBACK_REPLY in main.py).
    LOCAL_WHISPER_URL: str = ""

    # --- Outbound voice notes (voicebox-local-voice-adoption) -----------------------------------
    # Off by default. VoiceBox runs on the local inference node, which does not exist yet; on this
    # CPU-only laptop synthesis takes 3-5 minutes per phrase. With this false the bridge behaves
    # exactly as it did before the feature landed.
    #
    # The backend is the authoritative switch: it only sets `voice_allowed` on a reply when ITS own
    # VOICE_ENABLED is on, and /internal/whatsapp/voice-note answers 503 otherwise. This flag just
    # stops the bridge from doing local work that would be rejected.
    VOICE_ENABLED: bool = False

    # Local VoiceBox REST API. Never a public address — synthesis is on-prem so the client's text,
    # the model and the cloned voice never leave the machine (same sovereignty principle as the
    # Hermes/GBrain/poller decisions in ARCHITECTURE.md).
    VOICEBOX_URL: str = "http://127.0.0.1:17493"
    # Cloned-voice profile id. Empty means voice is unavailable — never guessed, because a wrong id
    # would speak in a different voice. Differs per machine, hence config and not a constant.
    VOICEBOX_PROFILE_ID: str = ""
    # VoiceBox's own `engine` field. Verified against the live API: the value is `qwen`, not an
    # engine slug.
    VOICEBOX_ENGINE: str = "qwen"
    # VoiceBox defaults model_size to "1.7B", which Phase 0 measured at 30-60 min per phrase on
    # CPU. Always send this explicitly.
    VOICEBOX_MODEL_SIZE: str = "0.6B"
    # VoiceBox defaults language to "en". Always send this explicitly.
    VOICEBOX_LANGUAGE: str = "es"
    # Matches Hermes' own command-TTS default.
    VOICEBOX_TIMEOUT_SECONDS: int = 120

    # Shared secret for the backend's /internal/* surface (same key the Siigo and Gmail pollers
    # use). Empty fails closed on the backend side with a 503.
    INTERNAL_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
