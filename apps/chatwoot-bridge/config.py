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

    # HITL / conversation behavior
    PAUSE_LABEL: str = "bot_off"
    MAX_HISTORY: int = 10

    # Webhook auth (design.md decision 4)
    WEBHOOK_TOKEN: str = ""

    PORT: int = 8090

    # Reserved for phase 2 (audio transcription) — documented, unused (design.md Non-Goals).
    LOCAL_WHISPER_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
