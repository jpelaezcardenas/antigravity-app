"""
Pulso Diario Endpoints

POST /api/v1/agents/pulso-diario/summary - Daily aggregation of Shadow GL activity
Supports multi-tenant routing via TenantContextMiddleware
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PulsoDiarioSummaryRequest(BaseModel):
    company_id: str
    date_range: Optional[str] = None


class PulsoDiarioSummaryResponse(BaseModel):
    status: str
    tenant_id: str
    company_id: str
    message: str


@router.post("/summary", response_model=PulsoDiarioSummaryResponse)
async def post_pulso_summary(
    request: Request,
    payload: PulsoDiarioSummaryRequest,
) -> PulsoDiarioSummaryResponse:
    """
    Get Pulso Diario daily aggregation summary.

    Multi-tenant: Uses tenant_id injected by TenantContextMiddleware from JWT.
    """
    tenant_id = getattr(request.state, "tenant_id", "default-tenant")

    return PulsoDiarioSummaryResponse(
        status="success",
        tenant_id=tenant_id,
        company_id=payload.company_id,
        message=f"Pulso summary for {payload.company_id} under tenant {tenant_id}",
    )
