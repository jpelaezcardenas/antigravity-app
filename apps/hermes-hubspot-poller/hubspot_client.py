"""Thin client for the HubSpot CRM v3 API (Contacts, Deals, Companies).

Fail-soft, same contract as apps/hermes-manus-poller/manus_client.py: nothing raises, failures
return None and are logged, so a HubSpot blip costs one record rather than crashing the tick.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(settings.HUBSPOT_ACCESS_TOKEN)


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _url(path: str) -> str:
    return f"{settings.HUBSPOT_API_BASE_URL.rstrip('/')}{path}"


def _upsert_object(
    object_type: str, object_id: Optional[str], properties: Dict[str, Any]
) -> Optional[str]:
    """Creates the object if object_id is None/empty, otherwise updates it (PATCH).
    Returns the HubSpot object id on success, None on any failure."""
    if not is_configured():
        return None
    try:
        if object_id:
            response = httpx.patch(
                _url(f"/crm/v3/objects/{object_type}/{object_id}"),
                headers=_headers(),
                json={"properties": properties},
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
        else:
            response = httpx.post(
                _url(f"/crm/v3/objects/{object_type}"),
                headers=_headers(),
                json={"properties": properties},
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
        if response.status_code not in (200, 201):
            logger.error(
                "%s upsert HTTP %s: %s", object_type, response.status_code, response.text[:300]
            )
            return None
        body = response.json()
        return body.get("id")
    except Exception as exc:
        logger.error("%s upsert failed: %s", object_type, exc)
        return None


def upsert_contact(contact_id: Optional[str], properties: Dict[str, Any]) -> Optional[str]:
    return _upsert_object("contacts", contact_id, properties)


def upsert_company(company_id: Optional[str], properties: Dict[str, Any]) -> Optional[str]:
    return _upsert_object("companies", company_id, properties)


def upsert_deal(deal_id: Optional[str], properties: Dict[str, Any]) -> Optional[str]:
    return _upsert_object("deals", deal_id, properties)
