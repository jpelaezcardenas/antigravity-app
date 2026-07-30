"""WhatsApp channel endpoints (taty-channel-consolidation).

Mounted at /api/v1/channels/whatsapp (see presentation/router.py).

`POST /leads/{lead_id}/reply` — INTERNAL and authenticated. The Chatwoot bridge calls this instead
of generating replies from a raw Hermes chat completion, so a single brain
(services/taty_lead_router.py) owns intent classification, Wompi payment links, payment
verification and KB grounding on every channel.

The public `/webhook` (Meta's ingress) and the durable-inbox endpoints land in later tasks of this
same change/the follow-up change; this file grows incrementally, each addition tested first.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.deps import get_current_user
from services.taty_lead_router import lead_exists, route_lead_message

router = APIRouter(tags=["whatsapp"])


class LeadReplyRequest(BaseModel):
    text: str


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
