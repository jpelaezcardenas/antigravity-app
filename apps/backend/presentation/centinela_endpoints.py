"""
Centinela Rules Engine - REST API endpoints.

Expone motor de detección fiscal ex-ante para:
- Dashboard (Centinela card)
- Auditoría programada
- Validación en tiempo real
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from services.centinela_service import get_centinela_service
from core.supabase_client import get_supabase
from core.deps import get_current_user
from core.tenant_context import resolve_caller_tenant_id

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


class CentinelaAlertsScopedResponse(BaseModel):
    """Response for GET /centinela/alerts (tenant-scoped, no company_id in the payload —
    the caller's tenant is resolved server-side, not passed as a free-text path param)."""
    alerts: List[CentinelaAlert]
    alert_count: int
    critical_count: int
    warning_count: int
    risk_level: str
    source: str = Field(..., description="'supabase' — this route never demo-falls-back")


def _empty_alerts_scoped_response() -> CentinelaAlertsScopedResponse:
    """Empty response for an authenticated caller with no resolved tenant —
    NEVER Cliente Cero, so an unwired client login can't see Contexia's own alerts."""
    return CentinelaAlertsScopedResponse(
        alerts=[],
        alert_count=0,
        critical_count=0,
        warning_count=0,
        risk_level="none",
        source="supabase",
    )


@router.get(
    "/alerts",
    response_model=CentinelaAlertsScopedResponse,
    summary="Get Centinela alerts for the authenticated caller's own tenant (Pulso/ActiveAlerts feed)",
)
async def get_my_alerts(
    user: dict = Depends(get_current_user),
    limit: int = 20,
) -> CentinelaAlertsScopedResponse:
    """Return active Centinela alerts for the caller's resolved tenant, most recent
    first — no path param, no demo fallback (pwa-tenant-aware-screens D2).

    Tenant resolution (same shared policy as GET /api/v1/financials, via
    `core.tenant_context.resolve_caller_tenant_id`):
    - Authenticated caller with a resolved tenant -> that caller's own alerts only.
    - Unauthenticated/local-dev caller (AUTH_ENFORCED=False, no token) -> Cliente Cero.
    - Authenticated caller whose tenant did NOT resolve -> an empty response. Never
      falls back to Cliente Cero here — that would leak Contexia's alerts to an
      unrelated logged-in client.
    """
    try:
        tenant_id = await resolve_caller_tenant_id(user)
        if tenant_id is None:
            return _empty_alerts_scoped_response()

        supabase = get_supabase()
        result = (
            supabase.table("centinela_alerts")
            .select("*")
            .eq("tenant_id", tenant_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        raw_alerts = result.data or []

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

        return CentinelaAlertsScopedResponse(
            alerts=alert_models,
            alert_count=len(raw_alerts),
            critical_count=critical_count,
            warning_count=warning_count,
            risk_level=risk_level,
            source="supabase",
        )

    except Exception as e:
        logger.error(f"Error in get_my_alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching tenant-scoped alerts",
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
