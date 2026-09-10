"""Internal follow-up-cadence send endpoint (taty-followup-cadence, part of
taty-voice-outbound-calls — ships and deploys independently of the voice/telephony tasks in that
change; no dependency on VOICE_OUTBOUND_CALLS_ENABLED or VOICE_ENABLED).

POST /internal/cadence/send-touch
  Auth: INTERNAL_API_KEY header (same machine-to-machine pattern as siigo_sync/ingest_file/voice)
  Body: {lead_id, day}

Why the caller (the local poller) only sends `day`, never message text
------------------------------------------------------------------------
The poller decides WHICH day looks due from its own read of `crm_leads` (cheap, no message
copy needed there). This endpoint re-reads the lead itself and is the only place authorized to
decide whether that day is *actually* due right now and what to say — never trusts the caller's
notion of elapsed time, and never accepts caller-supplied message text. Mirrors the "resolve
everything server-side, don't trust the caller" discipline already used for
`/internal/voice/outbound-call`'s design (Task 2 of the same change, not implemented here) and for
`/internal/whatsapp/voice-note` (existing, `presentation/voice_endpoints.py`).

A delivery failure, an already-sent day, a completed cadence, or a lead that isn't eligible all
return 200 with `sent: false` and a `reason` — same stance as voice_endpoints.py: these are not
this HTTP request's failure, and a 5xx would invite the poller to retry sends that should not be
retried. A genuinely wrong/malformed request (day outside the schedule) is the caller's bug and
gets 400.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from channels.whatsapp import send_whatsapp_message
from core.cadence_schedule import CADENCE_SCHEDULE, MAX_CADENCE_DAY
from core.supabase_client import get_service_supabase

logger = logging.getLogger(__name__)

router = APIRouter()

_INTERNAL_API_KEY_VAR = "INTERNAL_API_KEY"


def _verify_internal_key(x_internal_api_key: Optional[str]) -> None:
    expected = os.environ.get(_INTERNAL_API_KEY_VAR, "")
    if not expected:
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


class SendTouchRequest(BaseModel):
    lead_id: str
    day: int


class SendTouchResponse(BaseModel):
    sent: bool
    reason: str = ""


def _get_lead_cadence_state(lead_id: str) -> Optional[Dict[str, Any]]:
    """Reads the fields this endpoint needs directly from crm_leads (isolated for test
    patching, mirroring the convention in services/taty_lead_router.py)."""
    client = get_service_supabase()
    result = (
        client.table("crm_leads")
        .select("id, stage, whatsapp_phone, cadence_day, cadence_completed_at, last_inbound_at, created_at")
        .eq("id", lead_id)
        .maybe_single()
        .execute()
    )
    return result.data if result else None


def _advance_cadence(lead_id: str, day: int) -> None:
    """Persists the sent day, and stamps completion on day 14 (isolated for test patching)."""
    client = get_service_supabase()
    patch: Dict[str, Any] = {"cadence_day": day}
    if day >= MAX_CADENCE_DAY:
        patch["cadence_completed_at"] = datetime.now(timezone.utc).isoformat()
    client.table("crm_leads").update(patch).eq("id", lead_id).execute()


def _elapsed_hours(anchor_iso: Optional[str]) -> float:
    if not anchor_iso:
        return 0.0
    anchor = datetime.fromisoformat(anchor_iso.replace("Z", "+00:00"))
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - anchor).total_seconds() / 3600.0


@router.post("/cadence/send-touch", response_model=SendTouchResponse)
async def send_cadence_touch_endpoint(
    payload: SendTouchRequest,
    x_internal_api_key: Optional[str] = Header(default=None),
) -> SendTouchResponse:
    """Sends the scripted WhatsApp touch for `day`, if — and only if — this lead is actually due
    for it right now. Auth is checked before anything else, matching every other `/internal/*`
    endpoint in this file's siblings."""
    _verify_internal_key(x_internal_api_key)

    if payload.day not in CADENCE_SCHEDULE:
        raise HTTPException(status_code=400, detail=f"day {payload.day} is not a scheduled cadence day")

    lead = _get_lead_cadence_state(payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.get("stage") != "NUEVOS":
        return SendTouchResponse(sent=False, reason="not_eligible")

    if lead.get("cadence_completed_at"):
        return SendTouchResponse(sent=False, reason="cadence_completed")

    current_day = lead.get("cadence_day")
    if current_day is not None and payload.day <= current_day:
        return SendTouchResponse(sent=False, reason="already_sent")

    anchor = lead.get("last_inbound_at") or lead.get("created_at")
    elapsed_hours = _elapsed_hours(anchor)
    step = CADENCE_SCHEDULE[payload.day]
    if elapsed_hours < step.threshold_hours:
        return SendTouchResponse(sent=False, reason="not_due_yet")

    phone = lead.get("whatsapp_phone")
    if not phone:
        logger.warning("cadence: lead %s has no phone; not sent", payload.lead_id)
        return SendTouchResponse(sent=False, reason="no_phone")

    sent = await send_whatsapp_message(phone, step.message)
    if not sent:
        logger.error("cadence: WhatsApp send failed for lead %s (day %s)", payload.lead_id, payload.day)
        return SendTouchResponse(sent=False, reason="send_failed")

    _advance_cadence(payload.lead_id, payload.day)
    return SendTouchResponse(sent=True)
