"""Client for the Contexia backend's operator-task endpoints.

Consumes the unmodified surface built by hermes-manus-execution-bridge (archived 2026-07-19):

  GET  /api/v1/sell-machine/tasks/pending          -> [operator_tasks rows]
  POST /api/v1/sell-machine/tasks/{id}/status      {"status": "dispatched"}
  POST /api/v1/sell-machine/tasks/{id}/result      {"status": "completed"|"failed", "result": {...}}

Those routes are currently unauthenticated by design (Hermes has no browser session). The JWT is
sent anyway so gating them later needs no change here (design.md D5). The signing shape is copied
— deliberately, not imported — from apps/chatwoot-bridge/backend_client.py so the two local
services can be released independently.

Fail-soft: nothing raises. Failures return None/False and are logged, so a backend blip costs one
tick rather than crashing the scheduled run.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Matches the literal default `workspace_id` Contexia's own create_access_token uses for the
# Cliente Cero deployment (apps/backend/core/identity_resolver.py), so TenantContextMiddleware
# and Supabase RLS need zero backend-side changes.
_TENANT_ID = "contexia-org-1"


def sign_tenant_jwt() -> Optional[str]:
    """HS256 JWT for the backend, or None when no secret is configured (routes are open today)."""
    if not settings.CONTEXIA_JWT_SECRET:
        return None
    try:
        from jose import jwt

        return jwt.encode(
            {
                "sub": "hermes-manus-poller",
                "tenant_id": _TENANT_ID,
                "workspace_id": _TENANT_ID,
                "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            },
            settings.CONTEXIA_JWT_SECRET,
            algorithm="HS256",
        )
    except Exception as exc:
        logger.error("Failed to sign backend JWT: %s", exc)
        return None


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = sign_tenant_jwt()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _url(path: str) -> str:
    return f"{settings.CONTEXIA_API_URL.rstrip('/')}/api/v1/sell-machine{path}"


def list_pending() -> List[Dict[str, Any]]:
    """Pending operator tasks, oldest first. Returns [] on any failure."""
    try:
        response = httpx.get(
            _url("/tasks/pending"), headers=_headers(), timeout=settings.HTTP_TIMEOUT_SECONDS
        )
        if response.status_code != 200:
            logger.error("tasks/pending HTTP %s: %s", response.status_code, response.text[:500])
            return []
        body = response.json()
        return body if isinstance(body, list) else []
    except Exception as exc:
        logger.error("tasks/pending failed: %s", exc)
        return []


def mark_dispatched(task_id: str) -> bool:
    """Claim a task (pending -> dispatched). False if the backend rejected it (e.g. already claimed
    by an overlapping tick) — the caller must then NOT create a Manus task."""
    try:
        response = httpx.post(
            _url(f"/tasks/{task_id}/status"),
            headers=_headers(),
            json={"status": "dispatched"},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error(
                "mark_dispatched(%s) HTTP %s: %s", task_id, response.status_code, response.text[:300]
            )
            return False
        return True
    except Exception as exc:
        logger.error("mark_dispatched(%s) failed: %s", task_id, exc)
        return False


def report_result(task_id: str, status: str, result: Dict[str, Any]) -> bool:
    """Report a terminal result (dispatched -> completed|failed)."""
    if status not in ("completed", "failed"):
        logger.error("report_result(%s): invalid terminal status %r", task_id, status)
        return False
    try:
        response = httpx.post(
            _url(f"/tasks/{task_id}/result"),
            headers=_headers(),
            json={"status": status, "result": result},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error(
                "report_result(%s) HTTP %s: %s", task_id, response.status_code, response.text[:300]
            )
            return False
        return True
    except Exception as exc:
        logger.error("report_result(%s) failed: %s", task_id, exc)
        return False
