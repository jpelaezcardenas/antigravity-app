"""WhatsApp channel endpoints (taty-whatsapp-sales-router, Change D).

Mounted at /api/v1/channels/whatsapp behind the WHATSAPP_CANONICAL feature flag (see
presentation/router.py). GET /webhook mirrors meta_endpoints.py's hub.challenge verification
exactly. POST /webhook normalizes inbound messages and routes each to the lead-scoped router
(services/taty_lead_router.py) — a NEW, separate router from taty_intent_router.py, since a
WhatsApp lead has no tenant_id (see design.md Decision 1).
"""

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from channels.whatsapp import normalize_whatsapp_webhook
from services.taty_lead_router import find_or_create_lead, route_lead_document, route_lead_message

router = APIRouter(tags=["whatsapp"])


@router.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    expected = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "contexia-whatsapp-webhook")

    if mode == "subscribe" and challenge and token == expected:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Invalid WhatsApp webhook verification token")


@router.post("/webhook")
async def whatsapp_webhook(payload: Dict[str, Any]):
    events = normalize_whatsapp_webhook(payload)

    for event in events:
        lead_id = find_or_create_lead(event["account_id"], full_name=event.get("actor_name"))
        if event.get("media_id"):
            await route_lead_document(lead_id, event["media_id"], event.get("mime_type") or "")
        else:
            route_lead_message(lead_id, event["text"])

    return {"ok": True, "events_processed": len(events)}
