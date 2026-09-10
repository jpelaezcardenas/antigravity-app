"""Environment-driven settings for the hermes-cadence-poller (taty-followup-cadence).

Secrets default to empty (fail closed). The poller reads crm_leads directly from Supabase (its
own service-role credentials, never through Railway) to decide who is due, and calls
POST /internal/cadence/send-touch on Railway to actually send — mirrors
apps/hermes-gmail-poller/config.py.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase (direct — poller reads crm_leads to decide who's due, never through Railway)
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Railway backend for the actual send
    RAILWAY_BACKEND_URL: str = "https://antigravity-app-production-175a.up.railway.app"
    INTERNAL_API_KEY: str = ""

    # Behavior
    DRY_RUN: bool = False
    HTTP_TIMEOUT_SECONDS: float = 30.0
    # Max leads processed per tick (avoid a single tick sending hundreds of messages at once)
    MAX_LEADS_PER_TICK: int = 100

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
