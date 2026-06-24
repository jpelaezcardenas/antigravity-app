"""
Centinela Agent Endpoints for E2E Testing and Multi-Tenant Integration

POST /api/v1/agents/centinela/generate-draft - Generate Centinela draft with tenant context
Supports multi-tenant routing via TenantContextMiddleware
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class CentinelaGenerateDraftRequest(BaseModel):
    company_id: str
    context: Optional[str] = None


class CentinelaGenerateDraftResponse(BaseModel):
    status: str
    tenant_id: str
    company_id: str
    draft_id: str
    message: str


@router.post("/generate-draft", response_model=CentinelaGenerateDraftResponse)
async def generate_centinela_draft(
    request: Request,
    payload: CentinelaGenerateDraftRequest,
) -> CentinelaGenerateDraftResponse:
    """
    Generate Centinela draft for a company.

    Multi-tenant: Uses tenant_id injected by TenantContextMiddleware from JWT.
    """
    tenant_id = getattr(request.state, "tenant_id", "default-tenant")

    return CentinelaGenerateDraftResponse(
        status="success",
        tenant_id=tenant_id,
        company_id=payload.company_id,
        draft_id=f"draft-{tenant_id}-{payload.company_id}",
        message=f"Centinela draft generated for {payload.company_id} under tenant {tenant_id}",
    )
