"""
Pulso Diario Endpoints

POST /api/v1/agents/pulso-diario/summary - Daily aggregation of Shadow GL activity
Tenant-scoped via the canonical `resolve_request_tenant_scope` helper (see
core/tenant_context.py), not the raw JWT claim TenantContextMiddleware injects.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from core.deps import get_current_user
from core.supabase_client import get_service_supabase
from core.tenant_context import TenantScope, resolve_request_tenant_scope
from presentation.sell_machine_endpoints import require_hermes_bridge_token
from services.operator_task_service import submit_completed_insight

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


class PulsoDiarioInsightRequest(BaseModel):
    tenant_id: str
    caja_real: int
    dinero_disponible: int
    ventas_ayer: int
    gastos_ayer: int


@router.post("/insights", dependencies=[Depends(require_hermes_bridge_token)])
async def post_pulso_diario_insight(payload: PulsoDiarioInsightRequest) -> dict:
    """
    Hermes-only bridge (pulso-diario-agent-insight-bridge): a local agent pushes a computed
    Pulso Diario insight for a tenant with no Shadow GL data yet. Gated by the same
    `require_hermes_bridge_token` bearer-token dependency the Sell Machine bridge routes use —
    same actor (Hermes, local/on-prem), same kind of local-to-cloud push.

    Stored as an already-`completed` `operator_tasks` row (task_type="pulso_diario_insight") —
    there is no prior pending request this responds to, so the usual pending/dispatched state
    machine does not apply here.
    """
    success, row, error = submit_completed_insight(
        tenant_id=payload.tenant_id,
        result={
            "caja_real": payload.caja_real,
            "dinero_disponible": payload.dinero_disponible,
            "ventas_ayer": payload.ventas_ayer,
            "gastos_ayer": payload.gastos_ayer,
        },
    )
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return row
