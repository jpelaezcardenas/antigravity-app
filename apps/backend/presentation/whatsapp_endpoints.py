"""WhatsApp channel endpoints (taty-channel-consolidation, whatsapp-durable-inbox).

Mounted at /api/v1/channels/whatsapp (see presentation/router.py). Three surfaces:

1. `POST /webhook` — the PUBLIC ingress from Meta, live as
   `https://contexia.online/api/v1/channels/whatsapp/webhook` via vercel.json's `/api/v1/:path*`
   rewrite to Railway, which is why Meta's callback needs no tunnel and no DNS delegation. It
   verifies `X-Hub-Signature-256` over the RAW body, then does exactly one thing: persist.
   Classification, LLM inference and outbound sending are deliberately NOT on this path — an LLM
   call inside Meta's request turns a slow model into a retry, and a retry into a duplicate reply.
2. `GET /inbox/pending`, `POST /inbox/ack`, `GET /inbox/health` — INTERNAL and authenticated. The
   local Chatwoot bridge PULLS from these, which is what lets the local node stay unreachable
   from the internet.
3. `POST /leads/{lead_id}/reply` — INTERNAL and authenticated. The bridge's entry point into the
   single Taty brain (taty-channel-consolidation), so intent classification, Wompi payment links,
   payment verification and KB grounding apply on every channel.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from channels.whatsapp import normalize_whatsapp_webhook, sanitize_for_whatsapp, send_whatsapp_message
from config import settings
from core.deps import get_current_user
from services.taty_lead_router import get_lead_phone, lead_exists, route_lead_message
from services.whatsapp_inbox_service import (
    DEFAULT_PULL_LIMIT,
    acknowledge,
    inbox_health,
    pull_pending,
    store_inbound_events,
)

router = APIRouter(tags=["whatsapp"])


class HistoryTurn(BaseModel):
    role: str  # "user" | "assistant"
    text: str


class LeadReplyRequest(BaseModel):
    text: str
    history: List[HistoryTurn] | None = None
    deliver: bool = True


class AckRequest(BaseModel):
    event_ids: List[str]


def verify_whatsapp_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 as HMAC-SHA256 over the EXACT raw request body.

    The raw bytes matter: parsing the JSON and re-serializing it changes key order and
    whitespace, so a signature computed over a round-tripped body never matches. Fails closed —
    an unset WHATSAPP_APP_SECRET rejects everything rather than waving traffic through.
    """
    secret = settings.WHATSAPP_APP_SECRET
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header[len("sha256=") :], expected)


@router.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    """Meta's subscription handshake. Fails closed: no hardcoded default verify token."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    expected = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN

    if expected and mode == "subscribe" and challenge and hmac.compare_digest(token or "", expected):
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook verification token")


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
) -> Dict[str, Any]:
    """Verify, persist, acknowledge. Nothing else.

    The response reports what was accepted for processing, not what was processed — Meta only
    needs a fast 200 so it stops retrying.
    """
    raw_body = await request.body()
    if not verify_whatsapp_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    payload = await request.json()
    events = normalize_whatsapp_webhook(payload)
    accepted = store_inbound_events(events)

    return {"ok": True, "events_accepted": accepted}


@router.get("/inbox/pending")
async def inbox_pending(
    limit: int = DEFAULT_PULL_LIMIT,
    _user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Hand unprocessed events to the local bridge and claim them."""
    events = pull_pending(limit=limit)
    return {"events": events, "count": len(events)}


@router.post("/inbox/ack")
async def inbox_ack(
    payload: AckRequest,
    _user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Mark events processed — called only after Chatwoot accepted the injected message."""
    return {"acknowledged": acknowledge(payload.event_ids)}


@router.get("/inbox/health")
async def inbox_health_endpoint(_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Backlog depth and oldest unprocessed age, so an offline local node is detectable."""
    return inbox_health()


@router.post("/leads/{lead_id}/reply")
async def taty_lead_reply(
    lead_id: str,
    payload: LeadReplyRequest,
    _user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Internal, authenticated reply generation for a WhatsApp lead.

    Never creates a lead: the bridge calls /crm/leads/whatsapp-intake first and passes the id it
    got back, so find-or-create stays owned by crm_service.

    `deliver` (default True) controls whether this endpoint ALSO sends the reply to the
    customer's real WhatsApp number via Meta's API directly, or returns text only.

    Historical context for why this flag exists (taty-whatsapp-renta-sales-capability, Stage 5):
    when the bridge injected events into Chatwoot's `Channel::Api` inbox (no Meta credentials —
    it can only fire an outgoing webhook, never deliver to WhatsApp), this endpoint HAD to send
    directly or the customer got nothing (found live: a reply mirrored into Chatwoot correctly
    but never reached the phone, because nothing else was calling Meta's send API). Once the
    bridge is pointed at the real Meta-linked `Channel::Whatsapp` inbox, Chatwoot itself can
    deliver — the bridge calls this with `deliver=False` and sends the returned text via its own
    `chatwoot_client.send_reply`, so a human's reply typed in Chatwoot also reaches the customer,
    which it could not while this endpoint was the only channel capable of a real send. A missing
    phone or a failed send never fails this request — the caller still needs the reply text back
    regardless (for Chatwoot mirroring when `deliver=False`, or simply because a delivery failure
    is not the request's failure).
    """
    if not lead_exists(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    history = [turn.model_dump() for turn in payload.history] if payload.history else None
    result = route_lead_message(lead_id, payload.text, history=history)

    # Safety net: strip any Markdown/HTML artifacts (tables, headers, <br>, **bold**, "Fuentes:"
    # footer) a real WhatsApp client can't render, regardless of how "reply" was generated. Applied
    # here so both the direct Meta send below AND the value returned to the bridge (which the bridge
    # mirrors into Chatwoot as a private note) get the same clean text — see
    # channels/whatsapp.py::sanitize_for_whatsapp for the full rationale.
    if result.get("reply"):
        result["reply"] = sanitize_for_whatsapp(result["reply"])

    if payload.deliver:
        phone = get_lead_phone(lead_id)
        if phone:
            await send_whatsapp_message(phone, result["reply"])

    return result
