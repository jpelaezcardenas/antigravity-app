from fastapi import APIRouter, HTTPException, Depends
from datetime import date
from services.financials_service import compute_pulso_daily_snapshot
from core.supabase_client import get_supabase
from core.deps import get_current_user, _STAGING_USER

router = APIRouter()


async def _resolve_cliente_cero_tenant_id() -> str:
    """Resolve the Cliente Cero tenant ID from Supabase."""
    supabase = get_supabase()
    result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    return result.data["id"]


def _empty_snapshot() -> dict:
    """Zeroed snapshot for an authenticated caller with no resolved tenant —
    NEVER Cliente Cero, so an unwired client login can't see Contexia's own data."""
    return {
        "caja_real": 0,
        "dinero_disponible": 0,
        "ventas_ayer": 0,
        "gastos_ayer": 0,
        "status": "empty",
    }


@router.get("")
async def get_financials(user: dict = Depends(get_current_user)):
    """
    GET /api/v1/financials

    Returns the "Pulso diario" snapshot from Shadow GL aggregation: cumulative
    Caja Real as of today, plus ventas/gastos for yesterday specifically (not a
    monthly aggregate) — daily granularity is the product's core promise.

    Tenant resolution (per-tenant-client-access):
    - Authenticated caller with a resolved tenant (per-client login, wired via
      user_tenants) -> that caller's own tenant. This is what makes each B2B
      client see THEIR OWN Caja Real, not Contexia's.
    - Unauthenticated/local-dev caller (AUTH_ENFORCED=False, no token — the
      permissive staging identity) -> Cliente Cero, preserving the existing
      Contexia overview / local dev behavior.
    - Authenticated caller whose tenant did NOT resolve (e.g. membership not
      yet wired) -> an empty snapshot. Never falls back to Cliente Cero here —
      that would leak Contexia's financials to an unrelated logged-in client.

    Response (all amounts in COP minor units — cents):
    {
        "caja_real": 352000000,
        "dinero_disponible": 352000000,
        "ventas_ayer": 80000000,
        "gastos_ayer": 12000000,
        "status": "healthy"
    }
    """
    try:
        resolved_tenant_id = user.get("resolved_tenant_id")
        if resolved_tenant_id:
            tenant_id = resolved_tenant_id
        elif user.get("id") == _STAGING_USER["id"]:
            tenant_id = await _resolve_cliente_cero_tenant_id()
        else:
            return _empty_snapshot()

        today = date.today()
        snapshot = compute_pulso_daily_snapshot(tenant_id, today)
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing financial snapshot: {str(e)}"
        )
