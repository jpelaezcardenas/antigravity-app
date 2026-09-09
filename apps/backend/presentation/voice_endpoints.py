"""Internal outbound voice-note endpoint (voicebox-local-voice-adoption).

POST /internal/whatsapp/voice-note
  Auth: INTERNAL_API_KEY header (machine-to-machine, same pattern as ingest_file_endpoints)
  Body: {lead_id, text, audio_base64, mime_type}

Why this endpoint exists at all
-------------------------------
Two constraints meet here and only this shape satisfies both:

1. The backend runs on Railway and **cannot reach** a VoiceBox listening on the inference node's
   `127.0.0.1:17493`. So synthesis cannot happen here.
2. Chatwoot **cannot deliver** to WhatsApp. Its channel never sees a genuine customer inbound (the
   durable-inbox poller mirrors messages in as private notes, because a real `incoming` is rejected
   422 on a real-provider inbox), so its 24-hour-window bookkeeping always believes the window is
   closed and Meta rejects everything it tries to send. Found live 2026-08-12 — see
   `apps/chatwoot-bridge/backend_client.py:85-101`. So delivery cannot happen locally either.

Therefore: the **local bridge synthesises** (VoiceBox + ffmpeg, entirely on-prem — the model, the
cloned voice and the client's text never leave the machine) and posts the finished OGG bytes here,
and **this endpoint delivers** through Meta's Graph API, which Railway can reach and already holds
credentials for. Mounted under `/internal`, which `vercel.json`'s `/api/v1/*` rewrite does not
expose, and authenticated by a key that fails closed.

Voice is additive: the text reply was already sent and mirrored into Chatwoot before this is
called. Nothing here can remove or alter it.
"""

from __future__ import annotations

import base64
import binascii
import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from channels.whatsapp import send_whatsapp_audio, upload_whatsapp_media
from config import settings
from services.taty_lead_router import get_lead_phone, lead_exists
from services.voice_safety import should_speak

logger = logging.getLogger(__name__)

router = APIRouter()

_INTERNAL_API_KEY_VAR = "INTERNAL_API_KEY"

# WhatsApp plays voice notes as OGG/Opus. A WAV uploads fine and then silently fails to play, so
# the wrong container is rejected here rather than discovered by a customer.
_ACCEPTED_MIME = "audio/ogg"


def _verify_internal_key(x_internal_api_key: Optional[str]) -> None:
    expected = os.environ.get(_INTERNAL_API_KEY_VAR, "")
    if not expected:
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


class VoiceNoteRequest(BaseModel):
    lead_id: str
    # The reply text that was synthesised. Carried so the safety gate can be re-applied here — the
    # bridge is a local, modifiable process and its `voice_allowed` decision is not trusted twice.
    text: str
    audio_base64: str
    mime_type: str = _ACCEPTED_MIME


class VoiceNoteResponse(BaseModel):
    sent: bool
    reason: str = ""


@router.post("/whatsapp/voice-note", response_model=VoiceNoteResponse)
async def send_voice_note_endpoint(
    payload: VoiceNoteRequest,
    x_internal_api_key: Optional[str] = Header(default=None),
) -> VoiceNoteResponse:
    """Deliver an already-synthesised voice note to a lead's WhatsApp number.

    Auth is checked before anything else, including the feature flag, so an unauthenticated caller
    cannot probe whether voice is enabled.

    A delivery failure returns 200 with `sent: false`, not a 5xx. Same stance as `taty_lead_reply`:
    the text reply already reached the customer, so this is not the request's failure — and a 5xx
    would invite the bridge to retry a send that may already have gone out.
    """
    _verify_internal_key(x_internal_api_key)

    if not settings.VOICE_ENABLED:
        # The expected production response for this change. Voice ships switched off.
        raise HTTPException(status_code=503, detail="Voice is disabled")

    if payload.mime_type != _ACCEPTED_MIME:
        raise HTTPException(
            status_code=415, detail=f"Voice notes must be {_ACCEPTED_MIME}, got {payload.mime_type}"
        )

    try:
        audio = base64.b64decode(payload.audio_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="audio_base64 is not valid base64")

    if not audio:
        raise HTTPException(status_code=400, detail="audio_base64 decoded to no bytes")

    if len(audio) > settings.VOICE_MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Voice note exceeds the maximum size")

    # Defence in depth. The bridge already received `voice_allowed` on the reply response, so a
    # request that fails the gate here means the bridge is modified, stale, or replaying. Refuse.
    if not should_speak(payload.text, settings.VOICE_MAX_CHARS):
        raise HTTPException(status_code=422, detail="Text is not permitted to be spoken")

    if not lead_exists(payload.lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    phone = get_lead_phone(payload.lead_id)
    if not phone:
        logger.warning("voice-note: lead %s has no phone; not sent", payload.lead_id)
        return VoiceNoteResponse(sent=False, reason="no_phone")

    media_id = await upload_whatsapp_media(audio, payload.mime_type)
    if not media_id:
        logger.error("voice-note: media upload failed for lead %s", payload.lead_id)
        return VoiceNoteResponse(sent=False, reason="upload_failed")

    if not await send_whatsapp_audio(phone, media_id):
        logger.error("voice-note: audio send failed for lead %s", payload.lead_id)
        return VoiceNoteResponse(sent=False, reason="send_failed")

    return VoiceNoteResponse(sent=True)
