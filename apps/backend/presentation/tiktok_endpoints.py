"""TikTok webhook endpoints for Social Content Ops."""

from typing import Any, Dict

from fastapi import APIRouter

from channels.tiktok import normalize_tiktok_webhook
from services.social_ops_service import get_social_ops_service

router = APIRouter(tags=["tiktok"])


@router.post("/webhook")
async def tiktok_webhook(payload: Dict[str, Any]):
    service = get_social_ops_service()
    events = normalize_tiktok_webhook(payload)
    results = [service.ingest_normalized_event(event) for event in events]
    return {"ok": True, "events_ingested": len(results), "results": results}

