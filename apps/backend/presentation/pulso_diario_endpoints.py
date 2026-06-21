"""
Pulso Diario Endpoints

GET /api/v1/agents/pulso-diario/summary - Daily aggregation of Shadow GL activity
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, Dict
import logging

from services.pulso_diario_service import get_daily_summary

logger = logging.getLogger(__name__)

router = APIRouter()


class PulsoDiarioSummaryResponse(BaseModel):
    date: str
    tenant_id: str
    dian_total_minor: int
    dian_invoice_count: int
    erp_posted_minor: int
    erp_entry_count: int
    discrepancy_count: int
    discrepancies_by_status: Dict[str, int]
    alerts_generated: int


@router.get("/summary", response_model=PulsoDiarioSummaryResponse)
async def get_pulso_summary(
    date: Optional[str] = Query(default=None, description="Date in YYYY-MM-DD format, defaults to today"),
) -> PulsoDiarioSummaryResponse:
    """
    Get Pulso Diario daily aggregation summary.

    Returns totals for DIAN invoiced, ERP posted, discrepancies, and alerts
    generated for a given date (or today if not specified).

    TODO: Multi-tenant routing not yet wired (tenant_id hardcoded to Cliente Cero).
    """
    from core.supabase_client import get_supabase

    supabase = get_supabase()
    tenant_result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    tenant_id = tenant_result.data["id"]

    summary = await get_daily_summary(tenant_id=tenant_id, date=date)
    return PulsoDiarioSummaryResponse(**summary)
