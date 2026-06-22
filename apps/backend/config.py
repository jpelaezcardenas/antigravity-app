from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import secrets
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    DATABASE_URL: str = ""
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30  # Short-lived tokens (was 1440 = 24h)
    # Auth enforcement flags (env-gated rollout — see core/deps.py).
    # AUTH_ENFORCED=False keeps the current permissive behavior so the live demo
    # is unaffected until the frontend is confirmed to send Authorization: Bearer.
    AUTH_ENFORCED: bool = False
    # DEMO_AUTH_ENABLED gates the hardcoded demo-user login path in auth_service.
    # Keep True for the MVP demo; set False in production.
    DEMO_AUTH_ENABLED: bool = True
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:3002,https://contexia.online,https://www.contexia.online"

    # LLM Provider API Keys & Settings
    GROQ_API_KEY: str = ""
    CEREBRAS_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # Feature Flags (Task 4.4: Social Ops canonical endpoints)
    SOCIAL_OPS_CANONICAL: bool = False

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    def validate_production_config(self) -> None:
        """
        Validates that critical settings are properly configured.
        Called during app startup to fail fast if misconfigured.
        """
        if not self.DEBUG and self.ENVIRONMENT == "production":
            if not self.JWT_SECRET or self.JWT_SECRET == "dev-secret-key-change-me-in-production":
                raise ValueError(
                    "JWT_SECRET must be set to a strong random value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            if len(self.JWT_SECRET) < 32:
                raise ValueError("JWT_SECRET must be at least 32 characters long.")
            if not self.SUPABASE_URL or not self.SUPABASE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in production.")

    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

# Generate a random JWT_SECRET for development if not set
if settings.DEBUG and not settings.JWT_SECRET:
    settings.JWT_SECRET = secrets.token_urlsafe(32)
    logger.warning(
        "⚠️  JWT_SECRET not set — using auto-generated secret for development. "
        "This will change on every restart. Set JWT_SECRET in .env for persistence."
    )
