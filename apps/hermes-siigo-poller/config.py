"""Environment-driven settings for the hermes-siigo-poller.

Secrets default to empty (fail closed — no hardcoded fallbacks, per ARCHITECTURE.md rule).
With RAILWAY_BACKEND_URL or INTERNAL_API_KEY unset the poller exits without calling Railway.

This poller talks to Railway's backend (POST /internal/siigo-sync/run) — it never calls
Supabase or Siigo directly. Siigo credentials live in Railway env vars, never here.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Railway backend URL — production default
    RAILWAY_BACKEND_URL: str = "https://antigravity-app-production-175a.up.railway.app"

    # Machine-to-machine token (INTERNAL_API_KEY in Railway env vars)
    # Must match what the backend expects in X-Internal-Api-Key header.
    INTERNAL_API_KEY: str = ""

    # How many days back to sync on each run (default: yesterday only)
    SIIGO_SYNC_DAYS_BACK: int = 1

    # Behavior
    DRY_RUN: bool = False
    HTTP_TIMEOUT_SECONDS: float = 60.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
