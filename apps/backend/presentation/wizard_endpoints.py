"""
Wizard de Auditoría Sombra — endpoint público de onboarding.

POST /wizard/auditoria-sombra → corre auditoría 15-min sobre datos mínimos
y devuelve reporte ejecutivo. Es el hook GTM principal (Nodos Contexia).
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import logging

from services.wizard_service import run_auditoria_sombra

logger = logging.getLogger(__name__)

router = APIRouter(tags=["wizard"])  # prefix in router.py


class AuditoriaSombraRequest(BaseModel):
    nit: str = Field(..., description="NIT colombiano, con o sin guion")
    razon_social: str = Field(..., min_length=2, description="Razón social")
    email: EmailStr = Field(..., description="Email del solicitante")
    sector: Optional[str] = Field(
        None,
        description="Servicios Digitales | Comercio | Importaciones | Restaurantes | Construcción",
    )
    regime: Optional[str] = Field(
        None, description="Régimen Simple | Régimen Común"
    )
    monthly_revenue_cop: Optional[float] = Field(
        None, ge=0, description="Ingresos mensuales estimados en COP"
    )
    notes: Optional[str] = Field(None, max_length=500)


class AlertPreview(BaseModel):
    rule_id: str
    title: str
    severity: str
    recommendation: str


class AuditoriaSombraResponse(BaseModel):
    company_id: str
    razon_social: str
    email: str
    nit: str
    sector: str
    regime: str
    status_level: str = Field(..., description="sana | vigilancia | alerta | crítica")
    executive_summary: str
    top_risks: List[Dict[str, Any]]
    opportunities: List[Any]
    alert_count: int
    alerts_preview: List[AlertPreview]
    next_steps: List[str]
    audit_duration_seconds: float
    generated_at: str
    notes: Optional[str] = None


@router.post(
    "/auditoria-sombra",
    response_model=AuditoriaSombraResponse,
    summary="Run free 15-min Shadow Audit for prospect onboarding",
)
@router.options("/auditoria-sombra")
async def auditoria_sombra(request: AuditoriaSombraRequest) -> AuditoriaSombraResponse:
    """Generate a Shadow Audit report from minimal prospect inputs."""
    try:
        report = run_auditoria_sombra(
            nit=request.nit,
            razon_social=request.razon_social,
            email=request.email,
            sector=request.sector,
            regime=request.regime,
            monthly_revenue_cop=request.monthly_revenue_cop,
            notes=request.notes,
        )
        logger.info(
            f"Auditoría sombra completed: {report['company_id']} "
            f"status={report['status_level']} alerts={report['alert_count']}"
        )
        return AuditoriaSombraResponse(**report)
    except Exception as e:
        logger.error(f"Error in auditoria_sombra: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando auditoría sombra: {str(e)}",
        )


@router.get("/health", summary="Wizard health check")
async def wizard_health():
    return {"status": "ok", "service": "wizard", "ready": True}
