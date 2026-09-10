"""Twilio REST API client for outbound qualification/follow-up calls
(taty-voice-outbound-calls, Task 2.4).

Deliberately a thin `httpx` wrapper against Twilio's own REST API, NOT the `twilio` PyPI SDK —
checked `requirements.txt` first, it is not already a dependency, and this repo already has a
convention (`channels/whatsapp.py`) of calling third-party HTTP APIs directly rather than adding a
new SDK dependency for one integration.

Credentials (`TWILIO_ACCOUNT_SID`/`TWILIO_AUTH_TOKEN`/`TWILIO_FROM_NUMBER`) live only in Railway
env vars (design.md Decision 1) — never in `apps/chatwoot-bridge/`, which has no Twilio code at
all. Empty credentials fail closed: this module refuses to call Twilio rather than guessing, same
posture as `channels.whatsapp.send_whatsapp_message`.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

_TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


def is_configured() -> bool:
    return bool(
        settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER
    )


async def place_call(to_number: str, twiml: str) -> Optional[str]:
    """Places an outbound PSTN call via Twilio's Calls resource, with `twiml` as the inline
    instructions (the `Twiml` request param) — no callback URL/webhook server is stood up in this
    change, so the call's entire script is sent up front rather than fetched from a `Url`.

    Returns the Twilio call SID on success, None on any failure (never raises) — mirrors
    `channels.whatsapp.send_whatsapp_message`'s fail-soft contract, since a failed call attempt is
    not itself a bug in the caller's request.
    """
    if not is_configured():
        logger.warning("twilio_client: TWILIO_* credentials not configured; refusing to call")
        return None

    url = f"{_TWILIO_API_BASE}/Accounts/{settings.TWILIO_ACCOUNT_SID}/Calls.json"
    data = {
        "To": to_number,
        "From": settings.TWILIO_FROM_NUMBER,
        "Twiml": twiml,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                data=data,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            )
            if resp.status_code not in (200, 201):
                logger.error("Twilio Calls API error: %s %s", resp.status_code, resp.text[:200])
                return None
            body = resp.json()
            return body.get("sid")
    except Exception as exc:
        logger.error("Failed to place Twilio call: %s", exc)
        return None
