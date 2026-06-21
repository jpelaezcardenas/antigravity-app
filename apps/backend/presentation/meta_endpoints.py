"""Meta webhook endpoints for Social Content Ops."""

import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from channels.meta import normalize_meta_webhook
from services.social_ops_service import get_social_ops_service

router = APIRouter(tags=["meta"])


@router.get("/webhook")
async def verify_meta_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    expected = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "contexia-meta-webhook")

    if mode == "subscribe" and challenge and token == expected:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Invalid Meta webhook verification token")


@router.post("/webhook")
async def meta_webhook(payload: Dict[str, Any]):
    service = get_social_ops_service()
    events = normalize_meta_webhook(payload)
    results = [service.ingest_normalized_event(event) for event in events]
    return {"ok": True, "events_ingested": len(results), "results": results}

