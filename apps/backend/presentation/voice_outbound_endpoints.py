"""Internal outbound-call trigger endpoint (taty-voice-outbound-calls, Task 2).

POST /internal/voice/outbound-call
  Auth: INTERNAL_API_KEY header (same machine-to-machine pattern as siigo_sync/ingest_file/voice/
  cadence — see presentation/voice_endpoints.py and presentation/cadence_endpoints.py)
  Body: {lead_id, tenant_id} ONLY — a `phone` field, if present, is silently ignored. The phone is
  always resolved server-side from `crm_leads`, closing the same spoofing gap Decisión #16 already
  fixed once for Taty's WhatsApp endpoint (design.md Decision 4).

Generic voice by default (spec.md, "The cloned voice is gated by its own flag")
---------------------------------------------------------------------------------
With `VOICE_OUTBOUND_CALLS_ENABLED` false (the default) or unset, the opening is spoken via
Twilio's own built-in `<Say>` TTS verb — a real, non-cloned, generic voice. This satisfies the
spec's "call flow works end-to-end using a generic voice" requirement today.

Documented follow-up, NOT built here: true local VoiceBox synthesis for this flow hits the same
network-path problem `voicebox-local-voice-adoption` already solved once for WhatsApp voice notes
(Railway cannot reach the local inference node's VoiceBox on 127.0.0.1:17493) — and this endpoint's
own request shape (`{lead_id, tenant_id}` only, per spec.md) cannot be used to smuggle in
pre-synthesized audio bytes without violating the spec. Wiring real VoiceBox synthesis into this
specific call flow needs its own resolved network path/relay, exactly like the WhatsApp voice-note
endpoint has, and is intentionally left as a documented follow-up (see the change's tasks.md,
Task 2.4 note) rather than invented in this session. When `VOICE_OUTBOUND_CALLS_ENABLED=true`
eventually gates the cloned voice, this module's `_build_twiml` is the seam that would need to
change — never `VOICE_ENABLED` (WhatsApp voice notes), which stays fully independent.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional
from xml.sax.saxutils import escape

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from config import settings
from core.supabase_client import get_service_supabase
from core.voice_call_script import build_opening_script
from services import twilio_client

logger = logging.getLogger(__name__)

router = APIRouter()

_INTERNAL_API_KEY_VAR = "INTERNAL_API_KEY"


def _verify_internal_key(x_internal_api_key: Optional[str]) -> None:
    expected = os.environ.get(_INTERNAL_API_KEY_VAR, "")
    if not expected:
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


class OutboundCallRequest(BaseModel):
    lead_id: str
    tenant_id: str

    # A caller-supplied `phone` (or any other field) is accepted by FastAPI's model parsing but
    # never read anywhere in this module — the phone is always resolved server-side below.
    model_config = ConfigDict(extra="ignore")


class OutboundCallResponse(BaseModel):
    placed: bool
    reason: str = ""
    call_sid: str = ""


def _get_lead_for_call(lead_id: str) -> Optional[Dict[str, Any]]:
    """Reads the fields this endpoint needs directly from crm_leads (isolated for test patching,
    mirroring the convention in presentation/cadence_endpoints.py)."""
    client = get_service_supabase()
    result = (
        client.table("crm_leads")
        .select("id, tenant_id, stage, whatsapp_phone, lead_type")
        .eq("id", lead_id)
        .maybe_single()
        .execute()
    )
    return result.data if result else None


def _build_twiml(opening_script: str) -> str:
    """Builds the TwiML sent to Twilio as the inline call script.

    `<Say>` is Twilio's own generic TTS — never Tatiana's cloned voice. Text is XML-escaped since
    it is embedded directly into the TwiML document.

    **Not used on a Twilio trial account** (confirmed live 2026-09-10 — trial rejects the inline
    `Twiml` param with a 400). Kept for when the account is upgraded; the endpoint below calls
    `twilio_client.place_call_via_url` with `settings.TWILIO_TWIML_BIN_URL` today instead.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Say voice="Polly.Lupe" language="es-MX">{escape(opening_script)}</Say>'
        "</Response>"
    )


@router.get("/opening-twiml")
async def opening_twiml_endpoint() -> Response:
    """Public, unauthenticated TwiML document Twilio fetches via the `Url` Calls param.

    Deliberately public (no `INTERNAL_API_KEY`, unlike this router's other endpoints) — Twilio's
    servers must be able to fetch it, and any HTTP client can verify it responds. This replaces a
    Twilio TwiML Bin as the `TWILIO_TWIML_BIN_URL` target: TwiML Bins only accept requests signed
    by Twilio, so any external reachability check (including Twilio's own "Try out Voice" console
    tool) reports them as unreachable even though a real signed call succeeds against them
    (confirmed live 2026-09-10). Content is the fixed, non-personalized opening line — nothing
    lead-specific is exposed by making this endpoint public.
    """
    twiml = _build_twiml(build_opening_script())
    return Response(content=twiml, media_type="application/xml")


@router.post("/outbound-call", response_model=OutboundCallResponse)
async def trigger_outbound_call_endpoint(
    payload: OutboundCallRequest,
    x_internal_api_key: Optional[str] = Header(default=None),
) -> OutboundCallResponse:
    """Triggers a Twilio outbound call to a Renta Natural (B2C) lead. Auth is checked before
    anything else, matching every other `/internal/*` endpoint in this file's siblings."""
    _verify_internal_key(x_internal_api_key)

    lead = _get_lead_for_call(payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.get("tenant_id") != payload.tenant_id:
        # Anti-enumeration posture matching Decisión #17: a caller-supplied tenant_id that doesn't
        # match the lead's own tenant is treated as "not found", not "forbidden".
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.get("lead_type") == "business_interest":
        # spec.md: "A lead outside Renta Natural (B2C) is rejected... never silently placing a B2B
        # outbound call under this capability."
        raise HTTPException(
            status_code=403, detail="B2B leads are out of scope for outbound qualification calls"
        )

    if not twilio_client.is_configured():
        raise HTTPException(status_code=503, detail="Twilio is not configured")

    phone = lead.get("whatsapp_phone")
    if not phone:
        logger.warning("outbound-call: lead %s has no phone; not placed", payload.lead_id)
        return OutboundCallResponse(placed=False, reason="no_phone")

    if settings.VOICE_OUTBOUND_CALLS_ENABLED:
        # The cloned-voice path is intentionally NOT implemented — no written consent exists yet
        # (design.md Decision 2 / Open Questions). Flipping this flag today would not silently
        # start using the cloned voice; it is a documented gap, not a hidden one.
        logger.warning(
            "outbound-call: VOICE_OUTBOUND_CALLS_ENABLED is true but no cloned-voice path is "
            "implemented; using the generic Twilio voice regardless"
        )

    if not settings.TWILIO_TWIML_BIN_URL:
        logger.error("outbound-call: TWILIO_TWIML_BIN_URL is not configured; refusing to call")
        return OutboundCallResponse(placed=False, reason="twiml_bin_not_configured")

    call_sid = await twilio_client.place_call_via_url(phone, settings.TWILIO_TWIML_BIN_URL)
    if not call_sid:
        logger.error("outbound-call: Twilio call failed for lead %s", payload.lead_id)
        return OutboundCallResponse(placed=False, reason="call_failed")

    return OutboundCallResponse(placed=True, call_sid=call_sid)
