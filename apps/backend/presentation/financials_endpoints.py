from fastapi import APIRouter, HTTPException
from datetime import date
from services.financials_service import compute_pulso_daily_snapshot
from core.supabase_client import get_supabase

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


@router.get("")
async def get_financials():
    """
    GET /api/v1/financials

    Returns the "Pulso diario" snapshot for Cliente Cero from Shadow GL
    aggregation: cumulative Caja Real as of today, plus ventas/gastos for
    yesterday specifically (not a monthly aggregate) — daily granularity is
    the product's core promise. Tenant is resolved server-side; no
    company_id parameter required.

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
        tenant_id = await _resolve_cliente_cero_tenant_id()
        today = date.today()
        snapshot = compute_pulso_daily_snapshot(tenant_id, today)
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing financial snapshot: {str(e)}"
        )
