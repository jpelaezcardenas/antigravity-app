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


def _create_object(object_type: str, properties: Dict[str, Any]) -> Optional[str]:
    response = httpx.post(
        _url(f"/crm/v3/objects/{object_type}"),
        headers=_headers(),
        json={"properties": properties},
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    )
    if response.status_code not in (200, 201):
        logger.error(
            "%s create HTTP %s: %s", object_type, response.status_code, response.text[:300]
        )
        return None
    return response.json().get("id")


def _upsert_object(
    object_type: str, object_id: Optional[str], properties: Dict[str, Any]
) -> Optional[str]:
    """Creates the object if object_id is None/empty, otherwise updates it (PATCH).
    Returns the HubSpot object id on success, None on any failure.

    A stored id can go stale (confirmed live 2026-08-15: HubSpot's own contact dedup/merge
    silently retired ids the poller had stored, turning every subsequent PATCH into a 404) — a
    404 on PATCH falls back to creating a fresh object instead of failing the whole lead's sync,
    same self-healing contract as "object_id was never set"."""
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
            if response.status_code == 404:
                logger.warning(
                    "%s %s no longer exists in HubSpot (stale id) — creating a new one",
                    object_type,
                    object_id,
                )
                return _create_object(object_type, properties)
            if response.status_code != 200:
                logger.error(
                    "%s upsert HTTP %s: %s", object_type, response.status_code, response.text[:300]
                )
                return None
            return response.json().get("id")
        return _create_object(object_type, properties)
    except Exception as exc:
        logger.error("%s upsert failed: %s", object_type, exc)
        return None


def upsert_contact(contact_id: Optional[str], properties: Dict[str, Any]) -> Optional[str]:
    return _upsert_object("contacts", contact_id, properties)


def upsert_company(company_id: Optional[str], properties: Dict[str, Any]) -> Optional[str]:
    return _upsert_object("companies", company_id, properties)


def upsert_deal(deal_id: Optional[str], properties: Dict[str, Any]) -> Optional[str]:
    return _upsert_object("deals", deal_id, properties)


# HubSpot's default association type ids (HUBSPOT_DEFINED category) for standard object pairs.
# See https://developers.hubspot.com/docs/api/crm/associations — stable, documented values.
_ASSOC_NOTE_TO_CONTACT = 202
_ASSOC_TASK_TO_DEAL = 216


def create_note(contact_id: str, body: str) -> Optional[str]:
    """Creates a HubSpot Note engagement associated with a Contact. Returns the note id, or
    None on any failure (fail-soft, same contract as _upsert_object)."""
    if not is_configured():
        return None
    try:
        response = httpx.post(
            _url("/crm/v3/objects/notes"),
            headers=_headers(),
            json={
                "properties": {"hs_note_body": body, "hs_timestamp": _now_millis()},
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": _ASSOC_NOTE_TO_CONTACT,
                            }
                        ],
                    }
                ],
            },
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code not in (200, 201):
            logger.error("create_note HTTP %s: %s", response.status_code, response.text[:300])
            return None
        return response.json().get("id")
    except Exception as exc:
        logger.error("create_note failed: %s", exc)
        return None


def has_open_task(deal_id: str) -> bool:
    """True if the Deal has at least one associated Task that isn't COMPLETED/DEFERRED.
    Fails closed (False) on any error, so a HubSpot blip risks a duplicate task rather than
    silently never creating one."""
    if not is_configured():
        return False
    try:
        response = httpx.get(
            _url(f"/crm/v3/objects/deals/{deal_id}/associations/tasks"),
            headers=_headers(),
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error("has_open_task HTTP %s: %s", response.status_code, response.text[:300])
            return False
        task_ids = [r["id"] for r in response.json().get("results", []) if r.get("id")]
        if not task_ids:
            return False
        return _any_task_incomplete(task_ids)
    except Exception as exc:
        logger.error("has_open_task failed: %s", exc)
        return False


def _any_task_incomplete(task_ids: list) -> bool:
    """Batch-reads tasks and returns True if any has a non-terminal hs_task_status."""
    try:
        response = httpx.post(
            _url("/crm/v3/objects/tasks/batch/read"),
            headers=_headers(),
            json={
                "properties": ["hs_task_status"],
                "inputs": [{"id": task_id} for task_id in task_ids],
            },
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return False
        for result in response.json().get("results", []):
            status = result.get("properties", {}).get("hs_task_status")
            if status not in ("COMPLETED", "DEFERRED"):
                return True
        return False
    except Exception as exc:
        logger.error("_any_task_incomplete failed: %s", exc)
        return False


def create_task(deal_id: str, subject: str) -> Optional[str]:
    """Creates a HubSpot Task associated with a Deal. Returns the task id, or None on failure."""
    if not is_configured():
        return None
    try:
        response = httpx.post(
            _url("/crm/v3/objects/tasks"),
            headers=_headers(),
            json={
                "properties": {
                    "hs_task_subject": subject,
                    "hs_task_status": "NOT_STARTED",
                    "hs_timestamp": _now_millis(),
                },
                "associations": [
                    {
                        "to": {"id": deal_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": _ASSOC_TASK_TO_DEAL,
                            }
                        ],
                    }
                ],
            },
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code not in (200, 201):
            logger.error("create_task HTTP %s: %s", response.status_code, response.text[:300])
            return None
        return response.json().get("id")
    except Exception as exc:
        logger.error("create_task failed: %s", exc)
        return None


def _now_millis() -> str:
    from datetime import datetime, timezone

    return str(int(datetime.now(timezone.utc).timestamp() * 1000))
