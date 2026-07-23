"""
Pulso Diario Endpoints

POST /api/v1/agents/pulso-diario/summary - Daily aggregation of Shadow GL activity
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
    payload: PulsoDiarioSummaryRequest,
    user: dict = Depends(get_current_user),
) -> PulsoDiarioSummaryResponse:
    """
    Get Pulso Diario daily aggregation summary.

    Multi-tenant: resolves the caller's tenant via `resolve_request_tenant_scope` — the same
    helper `approval_queue_endpoints.py` uses. An authenticated caller with no resolved tenant
    never falls back to Cliente Cero or the literal "default-tenant" string.
    """
    scope = resolve_request_tenant_scope(user, get_service_supabase())

    if scope is None:
        return PulsoDiarioSummaryResponse(
            status="tenant_unresolved",
            tenant_id="",
            company_id=payload.company_id,
            message=f"No tenant resolved for caller; cannot summarize {payload.company_id}",
        )

    return PulsoDiarioSummaryResponse(
        status="success",
        tenant_id=scope.tenant_id,
        company_id=payload.company_id,
        message=f"Pulso summary for {payload.company_id} under tenant {scope.tenant_id}",
    )
