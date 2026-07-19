"""Sell Machine creative-swarm endpoints (sell-machine-creative-swarm, Change E).

Mounted at /api/v1/sell-machine behind the SELL_MACHINE_CANONICAL feature flag (see
presentation/router.py). Campaign-package approve/reject reuse the existing, unmodified
/api/v1/approval-queue/approve and /reject endpoints — no new approval routes here.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from services.copywriter_service import generate_hooks
from services.sell_machine_service import (
    create_campaign_package,
    evaluate_hooks,
    list_campaigns,
)

router = APIRouter(tags=["sell-machine"])


class GenerateHooksRequest(BaseModel):
    count: int = Field(default=5, ge=1, le=20)


@router.post("/hooks/generate")
def generate_hooks_endpoint(payload: GenerateHooksRequest):
    hooks = generate_hooks(count=payload.count)
    return {"hooks": hooks}


class EvaluateHooksRequest(BaseModel):
    hooks: List[Dict[str, Any]]


@router.post("/hooks/evaluate")
def evaluate_hooks_endpoint(payload: EvaluateHooksRequest):
    survivors = evaluate_hooks(payload.hooks)
    return {"survivors": survivors}


class CreateCampaignRequest(BaseModel):
    hooks: List[Dict[str, Any]]
    brief: str = Field(..., min_length=1)
    target_segment: str = Field(..., min_length=1)
    budget: Optional[int] = None


def _to_dict(obj: Any) -> Any:
    """Best-effort serialization: ApprovalDecision has .to_dict(); mocks in tests are plain dicts."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj


@router.post("/campaigns")
async def create_campaign_endpoint(payload: CreateCampaignRequest):
    decision = await create_campaign_package(
        hooks=payload.hooks,
        brief=payload.brief,
        target_segment=payload.target_segment,
        budget=payload.budget,
    )
    return _to_dict(decision)


@router.get("/campaigns")
async def list_campaigns_endpoint(status: Optional[str] = Query(default=None)):
    decisions = await list_campaigns(status=status)
    return [_to_dict(d) for d in decisions]
