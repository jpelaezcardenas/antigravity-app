"""
Centinela Agent Endpoints for E2E Testing and Multi-Tenant Integration

POST /api/v1/agents/centinela/generate-draft - Generate Centinela draft with tenant context
Tenant-scoped via the canonical `resolve_request_tenant_scope` helper (see
core/tenant_context.py), not the raw JWT claim TenantContextMiddleware injects.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from core.deps import get_current_user
from core.supabase_client import get_service_supabase
from core.tenant_context import TenantScope, resolve_request_tenant_scope

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
    payload: CentinelaGenerateDraftRequest,
    user: dict = Depends(get_current_user),
) -> CentinelaGenerateDraftResponse:
    """
    Generate Centinela draft for a company.

    Multi-tenant: resolves the caller's tenant via `resolve_request_tenant_scope` — the same
    helper `approval_queue_endpoints.py` uses. An authenticated caller with no resolved tenant
    never falls back to Cliente Cero or the literal "default-tenant" string.
    """
    scope = resolve_request_tenant_scope(user, get_service_supabase())

    if scope is None:
        return CentinelaGenerateDraftResponse(
            status="tenant_unresolved",
            tenant_id="",
            company_id=payload.company_id,
            draft_id="",
            message=f"No tenant resolved for caller; cannot draft for {payload.company_id}",
        )

    return CentinelaGenerateDraftResponse(
        status="success",
        tenant_id=scope.tenant_id,
        company_id=payload.company_id,
        draft_id=f"draft-{scope.tenant_id}-{payload.company_id}",
        message=f"Centinela draft generated for {payload.company_id} under tenant {scope.tenant_id}",
    )
