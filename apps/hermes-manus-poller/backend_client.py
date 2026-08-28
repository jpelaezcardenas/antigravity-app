"""Client for the Contexia backend's operator-task endpoints.

Consumes the unmodified surface built by hermes-manus-execution-bridge (archived 2026-07-19):

  GET  /api/v1/sell-machine/tasks/pending          -> [operator_tasks rows]
  POST /api/v1/sell-machine/tasks/{id}/status      {"status": "dispatched"}
  POST /api/v1/sell-machine/tasks/{id}/result      {"status": "completed"|"failed", "result": {...}}

Authenticates with a static shared bearer token (`HERMES_BRIDGE_TOKEN`), matched by
`require_hermes_bridge_token` on the backend (see hermes-bridge-token-production-hardening). When
the token is unset, no `Authorization` header is sent and the routes remain open — matching the
backend guard's own no-op-when-unset behavior, so local development without the token still works.

Fail-soft: nothing raises. Failures return None/False and are logged, so a backend blip costs one
tick rather than crashing the scheduled run.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.HERMES_BRIDGE_TOKEN:
        headers["Authorization"] = f"Bearer {settings.HERMES_BRIDGE_TOKEN}"
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
