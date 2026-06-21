"""
Centinela Rules Engine - REST API endpoints.

Expone motor de detección fiscal ex-ante para:
- Dashboard (Centinela card)
- Auditoría programada
- Validación en tiempo real
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from services.centinela_service import get_centinela_service
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _calculate_risk_level(critical_count: int, warning_count: int) -> str:
    """Derive an overall risk level from alert severity counts."""
    if critical_count >= 2:
        return "critical"
    if critical_count >= 1 or warning_count >= 3:
        return "high"
    if warning_count >= 1:
        return "medium"
    return "low"


router = APIRouter(
    tags=["centinela"],
)  # prefix handled by router.py include_router()


# ============================================================================
# Request/Response Models
# ============================================================================


class CentinelaEvaluateRequest(BaseModel):
    """Request to evaluate company data against Centinela rules."""
    company_id: str = Field(
        ...,
        description="Client identifier (e.g., 'ctx-001')"
    )
    financial_data: Dict[str, Any] = Field(
        ...,
        description="Financial data to evaluate (annual_revenue, regime, etc.)"
    )
    save_alerts: bool = Field(
        True,
        description="Whether to save alerts to Supabase"
    )


class CentinelaAlert(BaseModel):
    """A Centinela rule alert"""
    rule_id: str = Field(..., description="Rule identifier (R001-R010)")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: str = Field(..., description="'info', 'warning', 'critical'")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    recommendation: Optional[str] = Field(None, description="Recommended action")
    evidence: Dict[str, Any] = Field(..., description="Data that triggered the alert")


class CentinelaEvaluateResponse(BaseModel):
    """Response from Centinela evaluation"""
    company_id: str = Field(..., description="Client identifier")
    alerts: List[CentinelaAlert] = Field(..., description="Triggered alerts")
    alert_count: int = Field(..., description="Total alerts triggered")
    critical_count: int = Field(..., description="Critical severity alerts")
    warning_count: int = Field(..., description="Warning severity alerts")
    risk_level: str = Field(..., description="'low', 'medium', 'high', 'critical'")
    saved_alert_ids: List[str] = Field(
        default_factory=list,
        description="IDs of saved alerts in Supabase"
    )


@router.post(
    "/evaluate",
    response_model=CentinelaEvaluateResponse,
    summary="Evaluate company against Centinela rules"
)
@router.options("/evaluate")  # Enable CORS preflight
async def evaluate_centinela(request: CentinelaEvaluateRequest) -> CentinelaEvaluateResponse:
    """Evaluate company financial data against Centinela rules."""
    try:
        logger.info(f"Centinela.evaluate() for company_id={request.company_id}")

        centinela = get_centinela_service()
        alerts = centinela.evaluate(
            company_id=request.company_id,
            data=request.financial_data
        )

        saved_ids = []
        if request.save_alerts and alerts:
            saved_ids = centinela.save_alerts(alerts)

        critical_count = sum(1 for a in alerts if a["severity"] == "critical")
        warning_count = sum(1 for a in alerts if a["severity"] == "warning")

        risk_level = _calculate_risk_level(critical_count, warning_count)

        logger.info(f"Centinela evaluation: {len(alerts)} alerts, risk_level={risk_level}")

        alert_models = [
            CentinelaAlert(
                rule_id=a["rule_id"],
                rule_name=a["rule_name"],
                severity=a["severity"],
                title=a["title"],
                description=a["description"],
                recommendation=a.get("recommendation"),
                evidence=a.get("evidence", {}),
            )
            for a in alerts
        ]

        return CentinelaEvaluateResponse(
            company_id=request.company_id,
            alerts=alert_models,
            alert_count=len(alerts),
            critical_count=critical_count,
            warning_count=warning_count,
            risk_level=risk_level,
            saved_alert_ids=saved_ids,
        )

    except Exception as e:
        logger.error(f"Error in evaluate_centinela: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error evaluating Centinela rules"
        )


class CentinelaAlertsListResponse(BaseModel):
    """Response for GET /centinela/alerts/{company_id}"""
    company_id: str
    alerts: List[CentinelaAlert]
    alert_count: int
    critical_count: int
    warning_count: int
    risk_level: str
    source: str = Field(..., description="'supabase' or 'demo_fallback'")


@router.get(
    "/alerts/{company_id}",
    response_model=CentinelaAlertsListResponse,
    summary="Get Centinela alerts for a company (Pulso feed)",
)
async def get_company_alerts(
    company_id: str,
    limit: int = 20,
    severity: Optional[str] = None,
) -> CentinelaAlertsListResponse:
    """Return active Centinela alerts for a company, most recent first."""
    try:
        logger.info(f"Centinela.get_alerts({company_id}, limit={limit}, severity={severity})")
        centinela = get_centinela_service()
        raw_alerts = centinela.get_alerts_for_company(
            company_id=company_id, limit=limit, severity=severity
        )

        # Detect source: if rule_id pattern + no created_at → demo fallback
        source = "supabase" if (raw_alerts and "created_at" in raw_alerts[0]) else "demo_fallback"

        critical_count = sum(1 for a in raw_alerts if a.get("severity") == "critical")
        warning_count = sum(1 for a in raw_alerts if a.get("severity") == "warning")

        risk_level = _calculate_risk_level(critical_count, warning_count)

        alert_models = [
            CentinelaAlert(
                rule_id=a["rule_id"],
                rule_name=a["rule_name"],
                severity=a["severity"],
                title=a["title"],
                description=a["description"],
                recommendation=a.get("recommendation"),
                evidence=a.get("evidence", {}),
            )
            for a in raw_alerts
        ]

        return CentinelaAlertsListResponse(
            company_id=company_id,
            alerts=alert_models,
            alert_count=len(raw_alerts),
            critical_count=critical_count,
            warning_count=warning_count,
            risk_level=risk_level,
            source=source,
        )

    except Exception as e:
        logger.error(f"Error in get_company_alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching alerts for {company_id}",
        )


@router.get(
    "/health",
    summary="Health check",
)
async def centinela_health():
    """Check if Centinela service is ready."""
    try:
        centinela = get_centinela_service()
        return {
            "status": "ok",
            "service": "centinela",
            "rules_count": len(centinela.rules),
            "ready": True
        }
    except Exception as e:
        logger.error(f"Centinela health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Centinela service not ready"
        )
