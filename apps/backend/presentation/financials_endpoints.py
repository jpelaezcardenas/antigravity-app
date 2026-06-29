from fastapi import APIRouter, HTTPException
from datetime import datetime
from services.financials_service import compute_pulso_snapshot
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

    Returns current financial snapshot for Cliente Cero from Shadow GL aggregation.
    Tenant is resolved server-side; no company_id parameter required.

    Response (all amounts in COP minor units — cents):
    {
        "caja_real": 352000000,
        "dinero_disponible": 352000000,
        "ventas_periodo": 2980000000,
        "salidas_periodo": 190000000,
        "status": "healthy"
    }
    """
    try:
        tenant_id = await _resolve_cliente_cero_tenant_id()
        now = datetime.utcnow()
        snapshot = compute_pulso_snapshot(tenant_id, now.year, now.month)
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing financial snapshot: {str(e)}"
        )
