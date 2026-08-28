"""Environment-driven settings for the Hermes->Manus operator-task poller.

Every secret defaults to an empty string (fail closed — no hardcoded fallback secrets, per
ARCHITECTURE.md decision #11 / CLAUDE.md incident rules). With MANUS_API_KEY unset the poller
exits without claiming any task, so the scheduled task can be registered before the founder
has created the key (design.md D3).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Manus API v2 (contract confirmed 2026-08-12 from open.manus.ai/docs/v2) ---
    MANUS_API_BASE_URL: str = "https://api.manus.ai"
    # Fail-closed: empty means "not configured" and the poller stays inert.
    MANUS_API_KEY: str = ""
    # Manus agent profile; overridable without a code change if Manus ships a newer one.
    MANUS_AGENT_PROFILE: str = "manus-1.6"
    # Optional Manus project to file tasks under (the founder's CTX-* projects).
    MANUS_PROJECT_ID: str = ""

    # --- Contexia backend (Railway) ---
    CONTEXIA_API_URL: str = "https://antigravity-app-production-175a.up.railway.app"
    # Shared secret matching the backend's `HERMES_BRIDGE_TOKEN` (require_hermes_bridge_token).
    # Empty means the /tasks/* routes are called with no Authorization header, matching the
    # backend guard's own no-op-when-unset behavior.
    HERMES_BRIDGE_TOKEN: str = ""

    # --- Behavior ---
    # Max operator tasks claimed per tick. Small by default: each one costs Manus credits, and
    # the 1-minute cadence drains a backlog quickly enough without a thundering herd.
    MAX_TASKS_PER_TICK: int = 3
    HTTP_TIMEOUT_SECONDS: float = 30.0
    # When true, log what would happen and make no state-changing call (neither Manus nor backend).
    DRY_RUN: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
