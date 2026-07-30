"""Meta webhook endpoints for Social Content Ops.

Handles Instagram/Facebook events only — `channels/meta.py::normalize_meta_webhook` discards
anything whose channel is not facebook/instagram. This is NOT a WhatsApp receiver; WhatsApp has
its own ingress in presentation/whatsapp_endpoints.py (taty-channel-consolidation).

Both controls here fail closed: an unset `META_APP_SECRET` or `META_WEBHOOK_VERIFY_TOKEN`
rejects every request rather than accepting a built-in default.
"""

import hashlib
import hmac
from typing import Any, Dict

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

from channels.meta import normalize_meta_webhook
from config import settings
from services.social_ops_service import get_social_ops_service

router = APIRouter(tags=["meta"])


def verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Verify Meta's X-Hub-Signature-256 as HMAC-SHA256 over the EXACT raw request body.

    The raw bytes matter: parsing the JSON and re-serializing it changes key order and
    whitespace, so a signature computed over a round-tripped body never matches.
    """
    secret = settings.META_APP_SECRET
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_header[len("sha256=") :], expected)


@router.get("/webhook")
async def verify_meta_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    expected = settings.META_WEBHOOK_VERIFY_TOKEN

    if expected and mode == "subscribe" and challenge and hmac.compare_digest(token or "", expected):
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Invalid Meta webhook verification token")


@router.post("/webhook")
async def meta_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
) -> Dict[str, Any]:
    raw_body = await request.body()
    if not verify_meta_signature(raw_body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    payload = await request.json()
    service = get_social_ops_service()
    events = normalize_meta_webhook(payload)
    results = [service.ingest_normalized_event(event) for event in events]
    return {"ok": True, "events_ingested": len(results), "results": results}
