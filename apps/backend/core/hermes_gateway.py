"""Dynamic Hermes gateway URL resolver.

Cloudflared tunnel URLs rotate on restart. tunnel_persistent.ps1 (Windows Startup)
publishes the current URL to hermes_tunnel[id='current'] in Supabase.
This helper caches the resolved URL for CACHE_TTL seconds to avoid a Supabase
round-trip on every request while still picking up restarts quickly.
"""

import time
import logging
from typing import Optional

from core.supabase_client import get_service_supabase

logger = logging.getLogger(__name__)

CACHE_TTL = 30  # seconds

_cache: dict = {"url": None, "ts": 0.0}


async def resolve_hermes_gateway_url() -> str:
    """Return the current Hermes gateway URL from Supabase hermes_tunnel table.

    Raises RuntimeError if the table has no current row or Supabase is unreachable.
    Never falls back to a stale URL — tunnel URLs change per restart.
    """
    now = time.time()
    if _cache["url"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["url"]

    try:
        client = get_service_supabase()
        row = client.table("hermes_tunnel").select("url").eq("id", "current").single().execute()
        url: Optional[str] = (row.data or {}).get("url")
        if not url:
            raise RuntimeError("hermes_tunnel[id='current'] has no url value")
        _cache["url"] = url
        _cache["ts"] = now
        logger.debug(f"Hermes gateway URL resolved: {url}")
        return url
    except Exception as exc:
        logger.error(f"Failed to resolve Hermes gateway URL: {exc}")
        raise RuntimeError(f"Hermes gateway unreachable: {exc}") from exc
