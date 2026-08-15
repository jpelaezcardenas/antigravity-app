"""Manus API v2 client.

Contract confirmed 2026-08-12 from https://open.manus.ai/docs/v2 — this resolves the
"exact Manus API request/response shape is still unconfirmed" non-goal carried by
hermes-manus-execution-bridge (archived 2026-07-19):

  Base      https://api.manus.ai
  Auth      header `x-manus-api-key: <key>`
  Create    POST /v2/task.create  {"message": {"content": ...}, "title", "agent_profile"}
            -> {"ok": true, "task_id", "task_title", "task_url", "request_id"}
  Poll      GET  /v2/task.detail?task_id=<id>
            -> {"ok": true, "task": {"id", "status", "credit_usage", "task_url", ...}}
  Status    running | stopped | waiting | error
  Messages  GET  /v2/task.listMessages?task_id=<id>  (manus-content-retrieval, confirmed 2026-08-15
            from https://open.manus.ai/docs/v2/task.listMessages.md — task.detail alone never
            carries what Manus actually produced, only status metadata)
            -> {"ok": true, "task_id", "messages": [{"type", "assistant_message": {"content"},
               "structured_output_result": {"success", "value", "error"}, ...}], "has_more"}

Fail-soft: no function raises on network/HTTP/`ok:false` failure. They return None (create) or
None-status (get) and log, so one bad tick never crashes the scheduled run — the operator task is
simply retried or left in flight for a later tick.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Manus statuses that mean "the agent is done with this task, one way or another".
# `stopped` means "finished or halted" and is NOT distinguishable from success at the API level,
# so it maps to `completed` while carrying task_url/credit_usage for human audit (design.md D0).
TERMINAL_STATUSES = {"stopped", "error"}
# `waiting` = Manus is asking a human a question. Deliberately treated as in-flight, never
# auto-answered: replying for the founder would be an unapproved action.
IN_FLIGHT_STATUSES = {"running", "waiting"}


@dataclass(frozen=True)
class ManusTask:
    """A Manus task as reported by task.detail."""

    task_id: str
    status: str
    task_url: Optional[str] = None
    credit_usage: Optional[int] = None

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def backend_status(self) -> str:
        """Map a terminal Manus status onto the backend's completed|failed vocabulary."""
        return "failed" if self.status == "error" else "completed"


def is_configured() -> bool:
    """True only when a Manus API key is present. Checked before any task is claimed so an
    unconfigured node never half-processes work (design.md D3)."""
    return bool(settings.MANUS_API_KEY)


def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-manus-api-key": settings.MANUS_API_KEY,
    }


def create_task(content: str, title: str) -> Optional[Dict[str, Any]]:
    """Create a Manus task. Returns the response dict (with `task_id`) or None on any failure."""
    if not is_configured():
        logger.error("MANUS_API_KEY is not set — refusing to call Manus.")
        return None

    payload: Dict[str, Any] = {
        "message": {"content": content},
        "title": title,
        "agent_profile": settings.MANUS_AGENT_PROFILE,
    }
    if settings.MANUS_PROJECT_ID:
        payload["project_id"] = settings.MANUS_PROJECT_ID

    try:
        response = httpx.post(
            f"{settings.MANUS_API_BASE_URL}/v2/task.create",
            headers=_headers(),
            json=payload,
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error("Manus task.create HTTP %s: %s", response.status_code, response.text[:500])
            return None
        body = response.json()
        if not body.get("ok") or not body.get("task_id"):
            logger.error("Manus task.create returned not-ok/no task_id: %s", str(body)[:500])
            return None
        return body
    except Exception as exc:  # fail soft — never crash the tick
        logger.error("Manus task.create failed: %s", exc)
        return None


def get_task(task_id: str) -> Optional[ManusTask]:
    """Fetch a Manus task's current state. Returns None on any failure (caller leaves it in flight)."""
    if not is_configured():
        logger.error("MANUS_API_KEY is not set — refusing to call Manus.")
        return None

    try:
        response = httpx.get(
            f"{settings.MANUS_API_BASE_URL}/v2/task.detail",
            headers=_headers(),
            params={"task_id": task_id},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error("Manus task.detail HTTP %s: %s", response.status_code, response.text[:500])
            return None
        body = response.json()
        task = body.get("task") if body.get("ok") else None
        if not task or not task.get("status"):
            logger.error("Manus task.detail returned not-ok/no task: %s", str(body)[:500])
            return None
        return ManusTask(
            task_id=task.get("id") or task_id,
            status=task["status"],
            task_url=task.get("task_url"),
            credit_usage=task.get("credit_usage"),
        )
    except Exception as exc:  # fail soft
        logger.error("Manus task.detail failed: %s", exc)
        return None


def list_messages(task_id: str) -> Optional[List[Dict[str, Any]]]:
    """Fetch a terminal task's message history (manus-content-retrieval), including any
    structured/free-text output Manus actually produced — task.detail alone never carries this.
    Fail-soft: returns None on any failure, same contract as get_task()/create_task()."""
    if not is_configured():
        logger.error("MANUS_API_KEY is not set — refusing to call Manus.")
        return None

    try:
        response = httpx.get(
            f"{settings.MANUS_API_BASE_URL}/v2/task.listMessages",
            headers=_headers(),
            params={"task_id": task_id},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.error(
                "Manus task.listMessages HTTP %s: %s", response.status_code, response.text[:500]
            )
            return None
        body = response.json()
        if not body.get("ok"):
            logger.error("Manus task.listMessages returned not-ok: %s", str(body)[:500])
            return None
        return body.get("messages") or []
    except Exception as exc:  # fail soft
        logger.error("Manus task.listMessages failed: %s", exc)
        return None
