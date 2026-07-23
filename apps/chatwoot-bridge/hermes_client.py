"""Client for the local Hermes Gateway's OpenAI-compatible chat completions
API (design.md decision 1) — Hermes owns model routing internally; this
bridge never talks to an LLM provider directly.

Fail-soft contract (design.md decision 7): invoke_chat_completion and
check_models never raise. On timeout or any error they log with a traceback
and return None, so the caller can fall back to a fixed apology message
rather than leaving the customer without a reply.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 60.0


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.HERMES_API_KEY}"}


async def invoke_chat_completion(
    history: list[dict[str, str]], message: str
) -> Optional[str]:
    """Call Hermes's /v1/chat/completions with the prior history plus the
    current user message. Returns the assistant's text, or None on any
    failure (timeout, non-200, malformed response) — never raises."""
    url = f"{settings.HERMES_GATEWAY_URL}/v1/chat/completions"
    body = {
        "model": settings.HERMES_MODEL,
        "messages": [*history, {"role": "user", "content": message}],
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, headers=_headers(), json=body)
        if response.status_code != 200:
            logger.error(
                "Hermes chat completion returned non-200: %s %s",
                response.status_code,
                response.text,
            )
            return None
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        logger.exception("Hermes chat completion call failed")
        return None


async def check_models() -> Optional[dict[str, Any]]:
    """Startup/troubleshooting liveness check: GET /v1/models. Returns the
    parsed response, or None on any failure — never raises (design.md
    decision 8/troubleshooting rule: makes a wrong-profile gateway visible
    in logs, not a crash)."""
    url = f"{settings.HERMES_GATEWAY_URL}/v1/models"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=_headers())
        if response.status_code != 200:
            logger.error(
                "Hermes /v1/models check returned non-200: %s %s",
                response.status_code,
                response.text,
            )
            return None
        return response.json()
    except Exception:
        logger.exception("Hermes /v1/models liveness check failed")
        return None
