"""Retry wrapper for transient network failures (DNS blips, dropped connections, TLS EOF).

Diagnosed 2026-09-09: neither supabase_client.py nor hubspot_client.py retried anything — a
single WinError 10053 / getaddrinfo failed / SSL UNEXPECTED_EOF on the founder's local network
cost the whole tick (0 synced) instead of one retry fixing it. This wraps only the network-level
exception, not HTTP error status codes (those are already handled explicitly by each caller and
should not be retried — a 404/400 won't fix itself).
"""

from __future__ import annotations

import logging
import time
from typing import Callable, TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (1, 2)  # sleep before attempt 2 and attempt 3


def request_with_retry(send: Callable[[], httpx.Response]) -> httpx.Response:
    """Calls `send()` (a zero-arg closure that performs one httpx request) and retries it up to
    `_MAX_ATTEMPTS` times on transient network errors (httpx.TransportError — covers connection
    resets, DNS failures, and TLS EOF). Raises the last exception if every attempt fails, so
    callers keep their existing try/except Exception fail-soft handling unchanged."""
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return send()
        except httpx.TransportError as exc:
            last_exc = exc
            if attempt < _MAX_ATTEMPTS:
                delay = _BACKOFF_SECONDS[attempt - 1]
                logger.warning(
                    "transient network error (attempt %d/%d), retrying in %ds: %s",
                    attempt,
                    _MAX_ATTEMPTS,
                    delay,
                    exc,
                )
                time.sleep(delay)
    assert last_exc is not None
    raise last_exc
