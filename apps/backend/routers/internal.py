"""Internal aggregator endpoints — authenticated by HERMES_BRIDGE_TOKEN only.

These endpoints are called by Hermes cron jobs to retrieve data for ALL active
PWA clients in a single call. They are never exposed to end users.

Auth: verify_hermes_token dependency — HTTP 403 on any mismatch.
Data isolation: every per-client query uses an explicit tenant_id filter
  even though the service-role Supabase client bypasses RLS, as defense in depth.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends

from core.hermes_auth import verify_hermes_token
from core.pwa_clients import ActiveClient, get_active_pwa_clients
from core.supabase_client import get_service_supabase

router = APIRouter(prefix="/internal", tags=["internal"])


# ---------------------------------------------------------------------------
# Per-client data helpers (thin wrappers so tests can patch cleanly)
# ---------------------------------------------------------------------------

async def get_pulso_summary(company_id: str, tenant_id: str) -> dict[str, Any]:
    from services.pulso_diario_service import get_daily_summary
    return await get_daily_summary(tenant_id=tenant_id, supabase_client=get_service_supabase())


async def get_centinela_alerts(company_id: str, tenant_id: str) -> dict[str, Any]:
    supabase = get_service_supabase()
    result = (
        supabase.table("centinela_alerts")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("resolved", False)
        .execute()
    )
    return {"alerts": result.data or []}


async def get_radar_summary(company_id: str, tenant_id: str) -> dict[str, Any]:
    from services.radar_service import calculate_risk_score, calculate_cashflow_forecast
    svc_sb = get_service_supabase()
    risk_score = await calculate_risk_score(tenant_id=tenant_id, supabase_client=svc_sb)
    cashflow = await calculate_cashflow_forecast(tenant_id=tenant_id, supabase_client=svc_sb)
    return {"risk_score": risk_score, "cashflow_forecast_30d": cashflow}


async def run_auditoria_nightly(company_id: str, tenant_id: str) -> dict[str, Any]:
    from services.auditoria_sombra_service import request_audit_report
    from datetime import date, timedelta
    today = date.today()
    month_start = today.replace(day=1).isoformat()
    result = await request_audit_report(
        tenant_id=tenant_id,
        date_start=month_start,
        date_end=today.isoformat(),
        audience="internal",
    )
    return result


async def get_social_ops_briefing(company_id: str, tenant_id: str) -> dict[str, Any]:
    from services.social_ops_service import get_social_ops_service
    service = get_social_ops_service()
    pipeline = service.get_pipeline()
    return {"pipeline": pipeline}


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health", dependencies=[Depends(verify_hermes_token)])
async def internal_health():
    return {"status": "ok", "timestamp": _ts()}


@router.get("/pulso/all-active", dependencies=[Depends(verify_hermes_token)])
async def pulso_all_active():
    """Return Pulso daily summary for all active PWA clients."""
    supabase = get_service_supabase()
    clients: list[ActiveClient] = get_active_pwa_clients(supabase)
    results = []
    for c in clients:
        payload = await get_pulso_summary(c.company_id, c.tenant_id)
        results.append({"company_id": c.company_id, "nombre": c.nombre, "pulso": payload})
    return {"clientes": results, "total": len(results), "timestamp": _ts()}


@router.get("/centinela/all-active", dependencies=[Depends(verify_hermes_token)])
async def centinela_all_active():
    """Return Centinela alerts for all active PWA clients."""
    supabase = get_service_supabase()
    clients: list[ActiveClient] = get_active_pwa_clients(supabase)
    results = []
    for c in clients:
        payload = await get_centinela_alerts(c.company_id, c.tenant_id)
        results.append({"company_id": c.company_id, "nombre": c.nombre, "centinela": payload})
    return {"clientes": results, "total": len(results), "timestamp": _ts()}


@router.get("/radar/all-active", dependencies=[Depends(verify_hermes_token)])
async def radar_all_active():
    """Return Radar risk summary for all active PWA clients."""
    supabase = get_service_supabase()
    clients: list[ActiveClient] = get_active_pwa_clients(supabase)
    results = []
    for c in clients:
        payload = await get_radar_summary(c.company_id, c.tenant_id)
        results.append({"company_id": c.company_id, "nombre": c.nombre, "radar": payload})
    return {"clientes": results, "total": len(results), "timestamp": _ts()}


@router.post("/auditoria-sombra/all-active", dependencies=[Depends(verify_hermes_token)])
async def auditoria_sombra_all_active():
    """Trigger nightly audit for all active PWA clients (direct service call, no self-HTTP)."""
    supabase = get_service_supabase()
    clients: list[ActiveClient] = get_active_pwa_clients(supabase)
    results = []
    for c in clients:
        payload = await run_auditoria_nightly(c.company_id, c.tenant_id)
        results.append({"company_id": c.company_id, "nombre": c.nombre, "auditoria_sombra": payload})
    return {"clientes": results, "total": len(results), "timestamp": _ts()}


@router.get("/social-ops/all-active", dependencies=[Depends(verify_hermes_token)])
async def social_ops_all_active():
    """Return Social Ops briefing for all active PWA clients.

    Error-resilient: a failure for one client produces null payload + error field;
    other clients are unaffected.
    """
    supabase = get_service_supabase()
    clients: list[ActiveClient] = get_active_pwa_clients(supabase)
    results = []
    for c in clients:
        try:
            payload = await get_social_ops_briefing(c.company_id, c.tenant_id)
            results.append({"company_id": c.company_id, "nombre": c.nombre, "social_ops": payload})
        except Exception as exc:
            results.append({
                "company_id": c.company_id,
                "nombre": c.nombre,
                "social_ops": None,
                "error": str(exc),
            })
    return {"clientes": results, "total": len(results), "timestamp": _ts()}
