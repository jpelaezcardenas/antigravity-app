"""
Radar Predictivo endpoints (FASE 4, Slice 3).

Exposes deterministic risk-score calculation (0-100) and 30-day cashflow forecast.
Risk scores >= 80 trigger conditional HITL (risk_review approval_queue entry).
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.deps import get_current_user
from core.supabase_client import get_supabase
from core.tenant_context import TenantScope, resolve_request_tenant_scope
from services.radar_service import (
    calculate_risk_score,
    calculate_cashflow_forecast,
    calculate_cash_projection_13w,
    enqueue_risk_review_if_critical,
    generate_alerta_narrativa,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["radar"])

# PWA-facing read surface, mounted separately at /radar (see presentation/router.py).
# The repo splits agent-internal routes (/agents/radar-predictivo, /agents/centinela,
# /agents/pulso-diario) from the clean per-tenant paths the PWA reads (/financials,
# /centinela, /tenant) — centinela_endpoints vs centinela_agents_endpoints is the
# precedent, and jarvis_endpoints is the precedent for two routers in one module.
pwa_router = APIRouter(tags=["radar"])


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


class WeekProjection(BaseModel):
    """One week of the 13-week cash projection."""

    semana: int
    fecha_inicio: str
    caja_proyectada: int
    confianza: str


class CashProjectionResponse(BaseModel):
    """13-week cash projection response (radar-cash-projection-13w)."""

    client_tenant_id: str
    generado_en: str
    metodologia: str
    impuesto_futuro_estimado: Optional[int] = None
    estado: str
    semanas: Optional[List[WeekProjection]] = None
    alerta_narrativa: Optional[str] = None


@pwa_router.get(
    "/proyeccion-caja",
    response_model=CashProjectionResponse,
    summary="13-week cash projection for the authenticated caller's own tenant",
)
async def get_cash_projection(
    user: dict = Depends(get_current_user),
) -> CashProjectionResponse:
    """
    Return a 13-week cash projection for the caller's resolved tenant.

    Tenant resolution uses the canonical `resolve_request_tenant_scope()`
    (Decision #17) — no query-param tenant. This is a read-only endpoint, so
    an unresolved tenant gets a graceful 200 empty response
    (`estado: "tenant_no_resuelto"`), matching `GET /centinela/alerts`'s
    precedent, not the 404 anti-enumeration policy used by write/ownership
    routes like Approval Queue (see design.md Decision #2).
    """
    supabase = get_supabase()
    scope = resolve_request_tenant_scope(user, supabase)
    tenant_id = scope.tenant_id if scope else None

    if tenant_id is None:
        return CashProjectionResponse(
            client_tenant_id="",
            generado_en="",
            metodologia="solo_historico",
            estado="tenant_no_resuelto",
            semanas=None,
        )

    try:
        result = await calculate_cash_projection_13w(tenant_id, supabase_client=supabase)
    except Exception as e:
        logger.error(f"Radar.get_cash_projection failed for tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cash projection calculation failed: {e}")

    narrativa = generate_alerta_narrativa(result.get("semanas"))

    return CashProjectionResponse(
        client_tenant_id=result["client_tenant_id"],
        generado_en=result["generado_en"],
        metodologia=result["metodologia"],
        impuesto_futuro_estimado=result.get("impuesto_futuro_estimado"),
        estado=result["estado"],
        semanas=result.get("semanas"),
        alerta_narrativa=narrativa,
    )
