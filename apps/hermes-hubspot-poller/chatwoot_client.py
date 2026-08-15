"""Minimal Chatwoot REST client for this poller — find a contact by phone, set cross-reference
custom attributes. Deliberately NOT a shared import from apps/chatwoot-bridge/: the two apps are
independent Hermes-local services (design.md Decision #1).

Fail-soft, same contract as hubspot_client.py: nothing raises, failures return None/False and
are logged.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(settings.CHATWOOT_URL and settings.CHATWOOT_API_TOKEN)


def _headers() -> dict:
    return {"api_access_token": settings.CHATWOOT_API_TOKEN}


def _base_url() -> str:
    return f"{settings.CHATWOOT_URL.rstrip('/')}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}"


def find_contact_by_phone(phone: str) -> Optional[int]:
    """Returns the Chatwoot contact id matching this phone, or None if not found/on failure.
    Never creates a contact (design.md Decision #2)."""
    if not is_configured():
        return None
    try:
        response = httpx.get(
            f"{_base_url()}/contacts/search",
            headers=_headers(),
            params={"q": phone},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error(
                "find_contact_by_phone HTTP %s: %s", response.status_code, response.text[:300]
            )
            return None
        matches = response.json().get("payload") or []
        return matches[0]["id"] if matches else None
    except Exception as exc:
        logger.error("find_contact_by_phone failed: %s", exc)
        return None


def set_cross_reference_attributes(
    contact_id: int, supabase_customer_id: str, hubspot_contact_id: str
) -> bool:
    """Merges supabase_customer_id/hubspot_contact_id into the contact's custom_attributes."""
    if not is_configured():
        return False
    try:
        response = httpx.patch(
            f"{_base_url()}/contacts/{contact_id}",
            headers=_headers(),
            json={
                "custom_attributes": {
                    "supabase_customer_id": supabase_customer_id,
                    "hubspot_contact_id": hubspot_contact_id,
                }
            },
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error(
                "set_cross_reference_attributes HTTP %s: %s",
                response.status_code,
                response.text[:300],
            )
            return False
        return True
    except Exception as exc:
        logger.error("set_cross_reference_attributes failed: %s", exc)
        return False
