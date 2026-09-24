"""Meta Conversions API (CAPI) client — server-side `Lead` event send
(empresa-4-0-agentic-gtm-roadmap, meta-capi-attribution spec).

Mirrors channels/whatsapp.py's contract: never raises, returns False and logs a clear
"not configured" message when META_CAPI_ACCESS_TOKEN/META_PIXEL_ID are unset, so a lead
capture never fails or degrades because Meta's API is unavailable or unconfigured
(design.md Decision 1, Risk "CAPI event-matching quality").

Match keys are phone-only today: `social_capture_partial`'s payload has no email field
(tasks.md Task 1.1 finding) — Meta's own matching degrades gracefully with a partial key
set, so this is not a blocker.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com"


def _hash_match_key(value: str) -> str:
    """Meta requires match-key values as lowercase, trimmed, SHA-256 hex digests."""
    normalized = value.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def send_lead_event(
    *,
    normalized_phone: str,
    lead_id: str,
    event_source_url: Optional[str] = None,
) -> bool:
    """Send a server-side `Lead` event to Meta's Conversions API.

    `normalized_phone` must already be in the E.164-ish normalized form
    `_normalize_whatsapp_phone` produces (digits, no separators) — CAPI expects the raw
    digits hashed, not a display-formatted number. Returns False (never raises) on any
    missing config, network failure, or non-200 response; the caller must never let this
    block or degrade the lead-capture response (spec meta-capi-attribution, Scenario
    "Meta CAPI unavailability does not block lead capture")."""
    access_token = os.getenv("META_CAPI_ACCESS_TOKEN")
    pixel_id = os.getenv("META_PIXEL_ID")
    api_version = os.getenv("META_CAPI_API_VERSION", "v21.0")

    if not access_token or not pixel_id:
        logger.warning(
            "send_lead_event: META_CAPI_ACCESS_TOKEN/META_PIXEL_ID not configured, skipping "
            "CAPI send for lead %s",
            lead_id,
        )
        return False

    url = f"{GRAPH_API_BASE}/{api_version}/{pixel_id}/events"
    payload = {
        "data": [
            {
                "event_name": "Lead",
                "event_time": int(time.time()),
                "action_source": "system_generated",
                "user_data": {
                    "ph": [_hash_match_key(normalized_phone)],
                },
                "event_source_url": event_source_url,
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, params={"access_token": access_token})
            if resp.status_code != 200:
                logger.error(
                    "Meta CAPI Lead event failed for lead %s: %s %s",
                    lead_id,
                    resp.status_code,
                    resp.text,
                )
                return False
            return True
    except Exception as e:
        logger.error("Failed to send Meta CAPI Lead event for lead %s: %s", lead_id, str(e))
        return False
