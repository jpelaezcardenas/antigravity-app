"""Environment-driven settings for the Hermes->HubSpot sync poller.

Every secret defaults to an empty string (fail closed — no hardcoded fallback secrets, per
ARCHITECTURE.md decision #11 / CLAUDE.md incident rules). With HUBSPOT_ACCESS_TOKEN or
SUPABASE_SERVICE_ROLE_KEY unset the poller exits without touching either system.

This poller talks DIRECTLY to Supabase and to HubSpot's API — never through Railway. The
HubSpot Private App Access Token and the Supabase service-role key both stay local to Hermes
(never a Railway/Vercel env var), per openspec/changes/hubspot-sync-renta-natural/design.md
Decision #2.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- HubSpot (Private App Access Token, confirmed live 2026-08-15: accountId 51867201,
    # STANDARD/free tier, single default pipeline) ---
    HUBSPOT_API_BASE_URL: str = "https://api.hubapi.com"
    # Fail-closed: empty means "not configured" and the poller stays inert.
    HUBSPOT_ACCESS_TOKEN: str = ""
    HUBSPOT_DEAL_PIPELINE: str = "default"

    # --- Supabase (direct, service-role — this poller does not go through Railway) ---
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # --- Behavior ---
    MAX_RECORDS_PER_TICK: int = 50
    HTTP_TIMEOUT_SECONDS: float = 30.0
    # When true, log what would happen and make no state-changing call (neither HubSpot nor Supabase).
    DRY_RUN: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
