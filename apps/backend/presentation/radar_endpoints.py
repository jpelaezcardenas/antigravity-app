"""
Radar Predictivo endpoints (FASE 4, Slice 3).

Exposes deterministic risk-score calculation (0-100) and 30-day cashflow forecast.
Risk scores >= 80 trigger conditional HITL (risk_review approval_queue entry).
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.radar_service import (
    calculate_risk_score,
    calculate_cashflow_forecast,
    enqueue_risk_review_if_critical,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["radar"])


class RiskScoreResponse(BaseModel):
    """Risk score and cashflow forecast response."""

    risk_score: int
    forecast_30d_minor: int
    hitl_triggered: bool
    hitl_entry_id: Optional[str] = None


@router.get("/risk-score", response_model=RiskScoreResponse)
async def get_risk_score(
    tenant_id: str = Query(..., description="Tenant UUID"),
) -> RiskScoreResponse:
    """
    Get deterministic risk score (0-100) and 30-day cashflow forecast.

    Risk score combines:
    - Discrepancy rate (40 pts): invoices with discrepancies / total
    - Amount mismatch (30 pts): sum(mismatches) / total_invoiced
    - Alert frequency (20 pts): alerts this month × 4 (capped)
    - Days overdue (10 pts): max_days_overdue / 30 (capped)

    If risk_score >= 80, automatically enqueue a risk_review for human approval
    (no duplicate if unresolved entry already exists).

    Returns:
        RiskScoreResponse with risk_score, forecast_30d_minor, HITL trigger info
    """
    try:
        risk_score = await calculate_risk_score(tenant_id)
        forecast = await calculate_cashflow_forecast(tenant_id)
        hitl_entry_id = await enqueue_risk_review_if_critical(tenant_id)
        hitl_triggered = hitl_entry_id is not None

        return RiskScoreResponse(
            risk_score=risk_score,
            forecast_30d_minor=forecast,
            hitl_triggered=hitl_triggered,
            hitl_entry_id=hitl_entry_id,
        )
    except Exception as e:
        logger.error(f"Radar.get_risk_score failed for tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Risk score calculation failed: {e}")
