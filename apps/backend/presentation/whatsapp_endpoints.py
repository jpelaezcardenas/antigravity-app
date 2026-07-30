"""WhatsApp channel endpoints (taty-channel-consolidation).

Mounted at /api/v1/channels/whatsapp (see presentation/router.py). Two surfaces:

1. `POST /webhook` — the PUBLIC ingress from Meta, live as
   `https://contexia.online/api/v1/channels/whatsapp/webhook` via vercel.json's `/api/v1/:path*`
   rewrite to Railway, which is why Meta's callback needs no tunnel and no DNS delegation. It
   verifies `X-Hub-Signature-256` over the RAW body before doing anything: previously it accepted
   any POST, so anyone who learned the URL could forge leads and drive the Wompi flow.
   Persisting the event for durable, deduplicated processing (rather than routing/sending inline
   here) is the `whatsapp-durable-inbox` follow-up change — kept out of this one deliberately.
2. `POST /leads/{lead_id}/reply` — INTERNAL and authenticated. The Chatwoot bridge calls this
   instead of generating replies from a raw Hermes chat completion, so a single brain
   (services/taty_lead_router.py) owns intent classification, Wompi payment links, payment
   verification and KB grounding no matter which channel a message arrived on.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from channels.whatsapp import normalize_whatsapp_webhook
from config import settings
from core.deps import get_current_user
from services.taty_lead_router import lead_exists, route_lead_message

router = APIRouter(tags=["whatsapp"])


class LeadReplyRequest(BaseModel):
    text: str


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
    """Verify the signature, normalize the payload. Routing/sending lands with the durable-inbox
    follow-up change; this task only closes the "accepts any POST" hole."""
    raw_body = await request.body()
    if not verify_whatsapp_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    payload = await request.json()
    events = normalize_whatsapp_webhook(payload)

    return {"ok": True, "events_received": len(events)}


@router.post("/leads/{lead_id}/reply")
async def taty_lead_reply(
    lead_id: str,
    payload: LeadReplyRequest,
    _user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Internal, authenticated reply generation for a WhatsApp lead.

    Never creates a lead: the bridge calls /crm/leads/whatsapp-intake first and passes the id it
    got back, so find-or-create stays owned by crm_service.
    """
    if not lead_exists(lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")

    return route_lead_message(lead_id, payload.text)
