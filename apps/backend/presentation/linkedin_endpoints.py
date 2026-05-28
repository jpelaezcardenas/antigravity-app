"""LinkedIn organization sync endpoints for Social Content Ops."""

from typing import Any, Dict

from fastapi import APIRouter

from channels.linkedin import normalize_linkedin_sync
from services.social_ops_service import get_social_ops_service

router = APIRouter(tags=["linkedin"])


@router.post("/sync")
async def linkedin_sync(payload: Dict[str, Any]):
    service = get_social_ops_service()
    events = normalize_linkedin_sync(payload)
    results = [service.ingest_normalized_event(event) for event in events]
    return {"ok": True, "events_ingested": len(results), "results": results}

