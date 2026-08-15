"""Thin client for Supabase's PostgREST API — direct, service-role, no Railway hop.

This poller reads/writes crm_leads, crm_wompi_transactions, and b2b_clients straight against
Supabase, per design.md Decision #2 (Hermes polling, credentials never reach Railway/Vercel).
Fail-soft: nothing raises. Failures return [] / False and are logged.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


def _headers() -> Dict[str, str]:
    return {
        "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def _url(path: str) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1{path}"


def list_leads(limit: int) -> List[Dict[str, Any]]:
    """All crm_leads rows, most recently updated first (bounded by limit). Returns [] on failure.

    Every tick re-syncs every lead (design.md Decision #7, revised 2026-08-15): the founder's
    actual need is a live pipeline that reflects the lead's current conversation stage as Taty
    talks to them, not a one-time snapshot. An "only sync what changed" filter was tried and
    reverted — PostgREST can't compare two columns of the same row in its filter query string
    (confirmed live: `.gt.last_synced_at` is parsed as a literal, not a column reference, and
    400s), and the client-side fallback (`updated_at > last_synced_at`) self-perpetuated because
    the very PATCH that stamps `last_synced_at` bumps `updated_at` via the table trigger. At this
    scale (~20 rows) a full upsert every 5-minute tick is trivially cheap and correctly keeps
    dealstage in sync with the real conversation — simpler and more correct than chasing a
    change-detection scheme.
    """
    try:
        response = httpx.get(
            _url("/crm_leads"),
            headers=_headers(),
            params={"select": "*", "order": "updated_at.desc", "limit": str(limit)},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error("list_leads HTTP %s: %s", response.status_code, response.text[:300])
            return []
        body = response.json()
        return body if isinstance(body, list) else []
    except Exception as exc:
        logger.error("list_leads failed: %s", exc)
        return []


def get_latest_wompi_transaction(lead_id: str) -> Optional[Dict[str, Any]]:
    """Most recent crm_wompi_transactions row for a lead, or None if none exists/on failure."""
    try:
        response = httpx.get(
            _url("/crm_wompi_transactions"),
            headers=_headers(),
            params={
                "select": "status,amount_cents,created_at",
                "lead_id": f"eq.{lead_id}",
                "order": "created_at.desc",
                "limit": "1",
            },
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error(
                "get_latest_wompi_transaction HTTP %s: %s", response.status_code, response.text[:300]
            )
            return None
        body = response.json()
        return body[0] if isinstance(body, list) and body else None
    except Exception as exc:
        logger.error("get_latest_wompi_transaction failed: %s", exc)
        return None


def mark_lead_synced(lead_id: str, hubspot_contact_id: str, hubspot_deal_id: str, synced_at: str) -> bool:
    return _patch(
        "/crm_leads",
        {"id": f"eq.{lead_id}"},
        {
            "hubspot_contact_id": hubspot_contact_id,
            "hubspot_deal_id": hubspot_deal_id,
            "last_synced_at": synced_at,
        },
    )


def list_b2b_clients(limit: int) -> List[Dict[str, Any]]:
    """All b2b_clients rows, most recently updated first (bounded by limit). Every tick re-syncs
    every client — same rationale as `list_leads` (design.md Decision #7)."""
    try:
        response = httpx.get(
            _url("/b2b_clients"),
            headers=_headers(),
            params={"select": "*", "order": "updated_at.desc", "limit": str(limit)},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error("list_b2b_clients HTTP %s: %s", response.status_code, response.text[:300])
            return []
        body = response.json()
        return body if isinstance(body, list) else []
    except Exception as exc:
        logger.error("list_b2b_clients failed: %s", exc)
        return []


def mark_b2b_client_synced(client_id: str, hubspot_company_id: str, synced_at: str) -> bool:
    return _patch(
        "/b2b_clients",
        {"id": f"eq.{client_id}"},
        {"hubspot_company_id": hubspot_company_id, "last_synced_at": synced_at},
    )


def _patch(path: str, filters: Dict[str, str], body: Dict[str, Any]) -> bool:
    try:
        response = httpx.patch(
            _url(path),
            headers=_headers(),
            params=filters,
            json=body,
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code not in (200, 204):
            logger.error("%s patch HTTP %s: %s", path, response.status_code, response.text[:300])
            return False
        return True
    except Exception as exc:
        logger.error("%s patch failed: %s", path, exc)
        return False
