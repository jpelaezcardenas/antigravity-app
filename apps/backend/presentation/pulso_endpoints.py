from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from application.pulso_service import PulsoService
from core.deps import get_current_user, verify_resource_ownership
from datetime import date

router = APIRouter()
pulso_service = PulsoService()


class PulsoTodayRequest(BaseModel):
    company_id: str


class PulsoTodayResponse(BaseModel):
    company_id: str
    date: str
    kpis: dict


@router.get("/{usuario_id}")
async def get_pulso_diario(
    usuario_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/pulso/{usuario_id}
    Response: PulsoDiario JSON

    Protected: User can only access their own pulso (IDOR protection).
    Admins can access any user's pulso.
    """
    await verify_resource_ownership(current_user, usuario_id)  # Fixed: added await

    result = await pulso_service.calcular_pulso_diario(usuario_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return result


@router.post("/today")
async def get_pulso_today(request: PulsoTodayRequest):
    """
    POST /api/v1/pulso/today
    Request: { "company_id": "..." }
    Response: KPI Dashboard with tax filings, compliance, alerts, audit risk

    Public endpoint for demo (no auth required for MVP)
    """
    company_id = request.company_id

    # Demo KPIs - in production would query real data
    return PulsoTodayResponse(
        company_id=company_id,
        date=str(date.today()),
        kpis={
            "tax_filings_pending": 2,
            "compliance_status": "on_track",
            "alerts_count": 3,
            "audit_risk_score": 0.35
        }
    )
