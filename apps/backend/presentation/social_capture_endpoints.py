"""Public, unauthenticated social-lead-capture endpoint (b2c-social-lead-capture, Task 2).

Deliberately its own router, NOT part of `crm_endpoints.py`: that router applies
`get_current_user` as a router-level dependency (it's the tenant-scoped B2B/B2C
cockpit surface), but a visitor landing on a public social ad page has no
session/token at all. This is a narrow, explicit exception to this backend's
tenant-scoping pattern (ARCHITECTURE.md Decisions #13-#17) — it always resolves to
Cliente Cero, the same funnel `POST /crm/leads/whatsapp-intake` already writes to
(design.md Decision 2), reusing `CrmService.whatsapp_intake`'s find-or-create rather
than duplicating it.

Mounted unconditionally in `presentation/router.py` (same reasoning as
`channels/whatsapp`'s router) — a feature flag here would risk silently dropping real
ad-traffic leads.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from channels.whatsapp import send_whatsapp_message
from services.crm_service import _normalize_whatsapp_phone, get_crm_service
from services.social_capture_throttle import (
    is_ip_throttled,
    is_phone_repeat,
    record_ip_hit,
    record_phone_capture,
)

#: First-contact message sent once, on the create path only (Task 3, design.md Decision 4).
#: Kept intentionally short and generic — Taty's own conversational skill (ARCHITECTURE.md
#: Decision #25) takes over from the reply, this is only the opening ping.
FIRST_CONTACT_MESSAGE = (
    "¡Hola! Soy Taty, la asistente de Contexia 👋. Vi que dejaste tus datos para la "
    "declaración de Renta Natural 2026. Cuéntame en qué te puedo ayudar."
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["social-capture"])


class SocialCapturePartialRequest(BaseModel):
    whatsapp_phone: str = Field(..., min_length=1)
    full_name: Optional[str] = None
    #: Landing page campaign tag (e.g. "facebook_ad_renta2026"), stamped on
    #: crm_leads.source (migration 0052). Optional — omitted stays NULL.
    source: Optional[str] = None


@router.post("/social-capture/partial")
async def social_capture_partial(payload: SocialCapturePartialRequest, request: Request):
    """Partial-capture write path for the public social landing page (Dapta Forms
    pattern, design.md Goals): fires the moment a visitor enters a valid phone
    number, before full form submission.

    Throttled by IP (reject excess requests) and by phone number (a repeat capture
    of the same phone within the throttle window is a no-op — it never re-hits the
    service layer, so it can never produce a duplicate lead or a duplicate
    first-contact WhatsApp send).

    First-contact trigger (Task 3, design.md Decision 4): only fires when
    `whatsapp_intake` reports `is_new: True` (the create path) — a phone number
    already in `crm_leads`, whether found now or previously throttled as a repeat,
    never gets a second first-contact message. Reuses `channels.whatsapp.
    send_whatsapp_message`, the same text-delivery mechanism `cadence_endpoints.py`
    already calls directly — no new send mechanism, no Twilio/voice dependency."""
    client_ip = request.client.host if request.client else "unknown"

    if is_ip_throttled(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests, try again shortly.")
    record_ip_hit(client_ip)

    normalized_phone = _normalize_whatsapp_phone(payload.whatsapp_phone)
    if is_phone_repeat(normalized_phone):
        return {"is_new": False, "throttled_repeat": True}

    result = get_crm_service().whatsapp_intake(
        payload.whatsapp_phone, full_name=payload.full_name, source=payload.source
    )
    record_phone_capture(normalized_phone)

    if result.get("is_new"):
        sent = await send_whatsapp_message(payload.whatsapp_phone, FIRST_CONTACT_MESSAGE)
        if not sent:
            logger.warning(
                "social_capture_partial: first-contact WhatsApp send failed for lead %s",
                result.get("lead_id"),
            )

    return result
