"""Environment-driven settings for the hermes-gmail-poller.

Secrets default to empty (fail closed). The poller reads Gmail via the Gmail API
using OAuth2 tokens stored locally (never in Railway), resolves tenant from
gmail_sender_map in Supabase, and calls /internal/ingest/file on Railway.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gmail OAuth2 — stored as a JSON file locally (never Railway)
    # Generate via: python -m gmail_client --auth  (one-time OAuth2 flow)
    GMAIL_OAUTH_TOKEN_PATH: str = "token.json"
    GMAIL_CREDENTIALS_PATH: str = "credentials.json"
    # Gmail address whose inbox to poll (Taty's email)
    GMAIL_INBOX_ADDRESS: str = ""
    # Label to search for unprocessed emails (default: INBOX, unread, has attachment)
    GMAIL_PROCESSED_LABEL: str = "contexia-processed"

    # Supabase (direct — poller reads gmail_sender_map, never goes through Railway)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Railway backend for file ingestion
    RAILWAY_BACKEND_URL: str = "https://antigravity-app-production-175a.up.railway.app"
    INTERNAL_API_KEY: str = ""

    # Behavior
    DRY_RUN: bool = False
    HTTP_TIMEOUT_SECONDS: float = 60.0
    # Max attachments to process per tick (avoid rate limiting)
    MAX_ATTACHMENTS_PER_TICK: int = 20
    # Supported MIME types for attachment download
    SUPPORTED_MIME_TYPES: str = (
        "text/csv,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "application/xml,text/xml,"
        "application/pdf"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def supported_mime_types_list(self) -> list[str]:
        return [t.strip() for t in self.SUPPORTED_MIME_TYPES.split(",") if t.strip()]


settings = Settings()
