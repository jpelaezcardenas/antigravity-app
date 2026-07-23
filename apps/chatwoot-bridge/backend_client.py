"""Client for the Contexia backend, reused (not duplicated) for CRM lead
intake and onboarding trigger (design.md decision 5).

Auth: HS256 JWT signed with the shared CONTEXIA_JWT_SECRET, following the
exact contract already documented for Hermes operators in
openspec/changes/hermes-multi-tenant-wrapper/HERMES_CONFIG.md Step 3
(`sub`, `tenant_id`, `exp`) and matching the literal default `workspace_id`
Contexia's own `create_access_token` uses ("contexia-org-1", see
apps/backend/core/identity_resolver.py) — so TenantContextMiddleware and
Supabase RLS need zero backend-side changes (design.md decision 6).

Fail-soft contract (design.md decision 7): whatsapp_intake and
trigger_onboarding never raise. Any failure (network, non-200) is logged and
swallowed so a down CRM/onboarding service never blocks the WhatsApp reply.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from jose import jwt

from config import settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 30.0

# Matches the literal default `workspace_id` Contexia's own JWT issuance uses
# for the single-tenant Cliente Cero deployment (see module docstring above).
_TENANT_ID = "contexia-org-1"


def sign_tenant_jwt() -> str:
    """Sign a short-lived (30 min) HS256 JWT with sub/tenant_id/exp claims,
    matching the Hermes-operator contract exactly."""
    payload = {
        "sub": "chatwoot-bridge",
        "tenant_id": _TENANT_ID,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.CONTEXIA_JWT_SECRET, algorithm="HS256")


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {sign_tenant_jwt()}"}


async def whatsapp_intake(phone: str) -> Optional[dict[str, Any]]:
    """Find-or-create the CRM lead for this WhatsApp phone number. Returns
    the backend's response ({lead_id, is_new, stage}), or None on any
    failure — never raises."""
    url = f"{settings.CONTEXIA_API_URL}/crm/leads/whatsapp-intake"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url, headers=_headers(), json={"whatsapp_phone": phone}
            )
        if response.status_code != 200:
            logger.error(
                "whatsapp_intake returned non-200: %s %s",
                response.status_code,
                response.text,
            )
            return None
        return response.json()
    except Exception:
        logger.exception("whatsapp_intake call failed")
        return None


async def trigger_onboarding() -> None:
    """Kick off the existing onboarding flow for a new WhatsApp lead. Fails
    soft — logs and swallows any error, never raises."""
    url = f"{settings.CONTEXIA_API_URL}/social-ops/onboarding/start"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=_headers(), json={})
        if response.status_code >= 400:
            logger.error(
                "trigger_onboarding returned an error: %s %s",
                response.status_code,
                response.text,
            )
    except Exception:
        logger.exception("trigger_onboarding call failed")
