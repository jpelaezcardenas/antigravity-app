from fastapi import APIRouter, Depends, HTTPException, Query
from application.centinela_service import CentinelaService
from core.deps import get_current_user, verify_resource_ownership

router = APIRouter()
centinela_service = CentinelaService()


@router.get("/alerts")
async def get_centinela_alerts(company_id: str = Query(...)):
    """
    GET /api/v1/centinela/alerts?company_id=...
    Response: Dict with alerts_by_severity

    Public endpoint for demo (no auth required for MVP)
    """
    # Demo: Use company_id as usuario_id for now
    alertas = await centinela_service.evaluar_umbrales(company_id)

    # Wrapper: Convert List[AlertaTributaria] → Dict with severity grouping
    by_severity = {
        "critical": [a for a in alertas if a.severidad == "roja"],
        "warning": [a for a in alertas if a.severidad == "amarilla"],
        "info": [a for a in alertas if a.severidad == "verde"]
    }

    return {
        "total_alerts": len(alertas),
        "alerts_by_severity": by_severity,
        "company_id": company_id
    }


@router.get("/{usuario_id}")
async def get_centinela_fiscal(
    usuario_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/centinela/{usuario_id}
    Response: List[AlertaTributaria]

    Protected: User can only access their own fiscal alerts (IDOR protection).
    """
    verify_resource_ownership(current_user, usuario_id)

    return await centinela_service.evaluar_umbrales(usuario_id)
