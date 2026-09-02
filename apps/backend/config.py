from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
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
    # Supabase Auth's own JWT signing secret (Supabase Dashboard → Settings → API →
    # JWT Secret). Already set in Railway; declared here so get_current_user can verify
    # the same Supabase-issued session token middleware.ts already validates at the
    # Vercel edge (bunker-pwa-auth-enforcement) — a separate scheme from this backend's
    # own JWT_SECRET below.
    SUPABASE_JWT_SECRET: str = ""
    DATABASE_URL: str = ""
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30  # Short-lived tokens (was 1440 = 24h)
    # Auth enforcement flags (env-gated rollout — see core/deps.py).
    # AUTH_ENFORCED=False keeps the current permissive behavior so the live demo
    # is unaffected until the frontend is confirmed to send Authorization: Bearer.
    AUTH_ENFORCED: bool = False
    # DEMO_AUTH_ENABLED gates the demo-user login path in auth_service.
    # Keep True for the MVP demo; set False in production.
    DEMO_AUTH_ENABLED: bool = True
    # Password for the contexia.marketing@gmail.com demo-admin account. Never
    # hardcode a real value — empty default fails closed (see
    # remediate-gbrain-audit-findings, auth-demo-credentials spec).
    DEMO_ADMIN_PASSWORD: str = ""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:3002,https://contexia.online,https://www.contexia.online"

    # LLM Provider API Keys & Settings — free-tier cascade (2026-08-18, model names
    # verified live 2026-08-28). MiniMax M3, GLM 5.3, and MiMo were all dropped: this
    # backend serves production/automated requests, none of the paid plans are being
    # kept for it, and MiMo's ToS explicitly forbids "application backend" use (it's
    # reserved for Hermes/Houston, which are interactive coding-tool sessions).
    #
    # Cascade order reflects what was CONFIRMED WORKING via live curl against the
    # actual Railway production keys on 2026-08-28, not aspirational ordering:
    #   1. Groq (openai/gpt-oss-120b) — confirmed 200.
    #   2. OpenRouter free (nvidia/nemotron-3-super-120b-a12b:free) — confirmed 200.
    #      The old default (openai/gpt-oss-120b:free) was retired from OpenRouter's
    #      free tier (404 "use the paid slug instead").
    #   3. Cerebras (gpt-oss-120b) — confirmed reachable but the account still returns
    #      402 Payment required (verified again 2026-08-28 with a freshly-generated
    #      key — it's the account's billing/tier status, not a stale key). Needs a
    #      human to activate/pay for the free tier in the Cerebras dashboard.
    #      (The old model name, llama-3.3-70b, no longer exists in Cerebras's
    #      catalog either — /v1/models now only lists gpt-oss-120b and gemma-4-31b.)
    #   4. NVIDIA NIM (openai/gpt-oss-120b) — fixed 2026-08-28: NVIDIA_API_KEY added
    #      to Railway, and the old model (meta/llama-3.3-70b-instruct) was swapped
    #      out after it hit end-of-life 2026-08-26 (410 Gone). Confirmed 200 live.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b:free"

    CEREBRAS_API_KEY: str = ""
    CEREBRAS_MODEL: str = "gpt-oss-120b"

    NVIDIA_API_KEY: str = ""
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "openai/gpt-oss-120b"

    # Legacy keys — retained for backward compatibility, no longer in active cascade
    MISTRAL_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "openai/gpt-oss-120b"

    # Feature Flags (Task 4.4: Social Ops canonical endpoints)
    SOCIAL_OPS_CANONICAL: bool = False

    # CRM B2B retainers cockpit (change crm-b2b-retainers-cockpit) — default off, flip
    # after Stage 11 prod smoke-test, same playbook as SOCIAL_OPS_CANONICAL.
    CRM_CANONICAL: bool = False

    # Sell Machine creative swarm (change sell-machine-creative-swarm) — default off, flip
    # after Stage 11 prod smoke-test, same playbook as SOCIAL_OPS_CANONICAL.
    SELL_MACHINE_CANONICAL: bool = False

    # Hermes bridge machine-token auth (change hermes-task-queue-tenant-scoping) — optional
    # bearer token gating the 5 operator-task routes in sell_machine_endpoints.py. Unset (None)
    # by default: routes remain open exactly as before this change (fail-open, deliberate — see
    # design.md D5/D7). Activation requires coordinating the Hermes-side poller first.
    HERMES_BRIDGE_TOKEN: Optional[str] = None

    # Jarvis personal bot (change hermes-jarvis-contexia, Fase A).
    # TELEGRAM_BOT_TOKEN_JARVIS: token for the founder's personal Jarvis bot (separate from Taty).
    # TELEGRAM_WEBHOOK_SECRET_JARVIS: X-Telegram-Bot-Api-Secret-Token value set via setWebhook.
    # TELEGRAM_JUAN_DAVID_CHAT_ID: founder's personal chat_id — messages from other chat_ids are
    #   silently ignored (200 OK, no action) so unknown users cannot query Hermes via the bot.
    # All fail-open (empty string): the webhook handler logs a warning and skips auth rather than
    #   crashing, letting Railway deploy succeed even before the Telegram bot exists.
    TELEGRAM_BOT_TOKEN_JARVIS: str = ""
    TELEGRAM_WEBHOOK_SECRET_JARVIS: str = ""
    TELEGRAM_JUAN_DAVID_CHAT_ID: str = ""

    # WHATSAPP_CANONICAL was retired by taty-channel-consolidation. The flag guarded a public
    # webhook that is now the production ingress from Meta (reachable as
    # contexia.online/api/v1/channels/whatsapp/webhook via vercel.json's rewrite), so gating it
    # behind a flag only risked a silent outage. Its authenticity is enforced by signature
    # verification instead.
    #
    # Meta credentials. All fail closed: an empty value rejects every request rather than falling
    # back to a guessable built-in default (the previous code defaulted the verify tokens to
    # "contexia-whatsapp-webhook" / "contexia-meta-webhook" in source).
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = ""
    META_APP_SECRET: str = ""

    # Multi-tenant feature gate (Phase 1: MVP)
    MULTI_TENANT_ENABLED: bool = True  # Enable JWT tenant_id extraction
    JWT_TENANT_CLAIM: str = "tenant_id"  # JWT claim name for tenant identifier
    KNOWN_TENANTS: str = "contexia-org-1,client-xyz,client-abc"  # Comma-separated list

    # Wompi (Bancolombia) payment gateway — change wompi-payment-integration.
    # WOMPI_ENV selects sandbox vs production; keys must match that environment
    # (see validate_wompi_config). No hardcoded defaults for secrets — empty
    # values fail closed, never silently fall back to sandbox in production.
    WOMPI_ENV: str = "sandbox"  # "sandbox" | "production"
    WOMPI_PUBLIC_KEY: str = ""
    WOMPI_PRIVATE_KEY: str = ""
    WOMPI_INTEGRITY_SECRET: str = ""
    WOMPI_EVENTS_SECRET: str = ""
    WOMPI_BASE_URL: str = "https://sandbox.wompi.co/v1"

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

    def validate_wompi_config(self) -> None:
        """
        Fail-closed validation for Wompi payment settings. Called during app
        startup. Never allows a sandbox/production key mismatch, and requires
        all four Wompi credentials when WOMPI_ENV=production.
        """
        if self.WOMPI_ENV not in ("sandbox", "production"):
            raise ValueError(f"WOMPI_ENV must be 'sandbox' or 'production', got '{self.WOMPI_ENV}'.")

        prod_prefixes = ("pub_prod_", "prv_prod_")
        test_prefixes = ("pub_test_", "prv_test_")
        keys = [self.WOMPI_PUBLIC_KEY, self.WOMPI_PRIVATE_KEY]

        if self.WOMPI_ENV == "sandbox":
            for key in keys:
                if key and key.startswith(prod_prefixes):
                    raise ValueError(
                        "WOMPI_ENV=sandbox but a production-prefixed Wompi key "
                        "(pub_prod_/prv_prod_) is configured. Refusing to start."
                    )

        if self.WOMPI_ENV == "production":
            for key in keys:
                if key and key.startswith(test_prefixes):
                    raise ValueError(
                        "WOMPI_ENV=production but a sandbox-prefixed Wompi key "
                        "(pub_test_/prv_test_) is configured. Refusing to start."
                    )
            missing = [
                name
                for name, value in (
                    ("WOMPI_PUBLIC_KEY", self.WOMPI_PUBLIC_KEY),
                    ("WOMPI_PRIVATE_KEY", self.WOMPI_PRIVATE_KEY),
                    ("WOMPI_INTEGRITY_SECRET", self.WOMPI_INTEGRITY_SECRET),
                    ("WOMPI_EVENTS_SECRET", self.WOMPI_EVENTS_SECRET),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    f"WOMPI_ENV=production requires all Wompi credentials to be set. "
                    f"Missing: {', '.join(missing)}."
                )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    def __init__(self, **data):
        # Ensure environment variables always take precedence.
        # In Railway/production, .env may not exist or be outdated.
        # Explicitly check os.environ for critical values like GROQ_API_KEY.
        if not data.get('GROQ_API_KEY'):
            env_groq_key = os.environ.get('GROQ_API_KEY')
            if env_groq_key:
                data['GROQ_API_KEY'] = env_groq_key
                logger.info("✓ GROQ_API_KEY loaded from environment variable")
        super().__init__(**data)


settings = Settings()

# Generate a random JWT_SECRET for development if not set
if settings.DEBUG and not settings.JWT_SECRET:
    settings.JWT_SECRET = secrets.token_urlsafe(32)
    logger.warning(
        "⚠️  JWT_SECRET not set — using auto-generated secret for development. "
        "This will change on every restart. Set JWT_SECRET in .env for persistence."
    )
