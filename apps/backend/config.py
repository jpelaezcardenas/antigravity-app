from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import secrets
import logging
import os

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    # Service-role key for governance operations that must bypass RLS in a
    # controlled way (agent access-control reads of user_tenants/user_roles and
    # agent_operations audit writes). Never exposed to request input. See
    # change agent-operations-multitenant-security, design D6.
    SUPABASE_SERVICE_ROLE_KEY: str = ""
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

    # GLM (Z.AI / Zhipu) — interactive agents via GLM 5.2 subscription.
    # Endpoint/model mirror the validated local Hermes config (open.bigmodel.cn).
    # The endpoint is OpenAI-compatible, so the OpenAI SDK calls it via base_url.
    GLM_API_KEY: str = ""
    GLM_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"
    GLM_MODEL: str = "glm-5.2"

    # Feature Flags (Task 4.4: Social Ops canonical endpoints)
    SOCIAL_OPS_CANONICAL: bool = False

    # Multi-tenant feature gate (Phase 1: MVP)
    MULTI_TENANT_ENABLED: bool = True  # Enable JWT tenant_id extraction
    JWT_TENANT_CLAIM: str = "tenant_id"  # JWT claim name for tenant identifier
    KNOWN_TENANTS: str = "contexia-org-1,client-xyz,client-abc"  # Comma-separated list

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

    def __init__(self, **data):
        # Ensure environment variables always take precedence.
        # In Railway/production, .env may not exist or be outdated.
        # Explicitly check os.environ for critical values like GLM_API_KEY.
        if not data.get('GLM_API_KEY'):
            env_glm_key = os.environ.get('GLM_API_KEY')
            if env_glm_key:
                data['GLM_API_KEY'] = env_glm_key
                logger.info("✓ GLM_API_KEY loaded from environment variable")
        super().__init__(**data)


settings = Settings()

# Generate a random JWT_SECRET for development if not set
if settings.DEBUG and not settings.JWT_SECRET:
    settings.JWT_SECRET = secrets.token_urlsafe(32)
    logger.warning(
        "⚠️  JWT_SECRET not set — using auto-generated secret for development. "
        "This will change on every restart. Set JWT_SECRET in .env for persistence."
    )
