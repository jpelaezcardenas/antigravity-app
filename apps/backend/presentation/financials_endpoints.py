from fastapi import APIRouter, HTTPException, Query
from infrastructure.supabase_client import supabase_client
from datetime import datetime

router = APIRouter()


@router.get("")
async def get_financials(
    company_id: str = Query(
        default="a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0",
        description="Company UUID (default: Contexia client zero)"
    )
):
    """
    GET /api/v1/financials

    Returns current financial snapshot for a company from company_financials table.

    Response:
    {
        "caja_real": 42850000,
        "dinero_disponible": 38500000,
        "ventas_ayer": 1250000,
        "salidas_plata": 345000,
        "iva_vencimiento_dias": 3,
        "status": "healthy"
    }
    """
    try:
        response = supabase_client.table("company_financials") \
            .select("*") \
            .eq("company_id", company_id) \
            .eq("date", datetime.now().date().isoformat()) \
            .limit(1) \
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="No financial data found for today"
            )

        financials = response.data[0]

        return {
            "caja_real": financials["caja_real"],
            "dinero_disponible": financials["dinero_disponible"],
            "ventas_ayer": financials["ventas_ayer"],
            "salidas_plata": financials["salidas_plata"],
            "iva_vencimiento_dias": financials["iva_vencimiento_dias"],
            "status": financials["status"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching financial data: {str(e)}"
        )


@router.get("/pending-transactions")
async def get_pending_transactions(
    company_id: str = Query(
        default="a0a0a0a0-a0a0-a0a0-a0a0-a0a0a0a0a0a0",
        description="Company UUID (default: Contexia client zero)"
    )
):
    """
    GET /api/v1/pending-transactions

    Returns list of unclassified transactions (pending status) for a company.

    Response:
    {
        "count": 5,
        "transactions": [
            {
                "id": 1,
                "amount": 50000,
                "description": "Transferencia Entrada",
                "date": "2026-06-21",
                "status": "pending"
            },
            ...
        ]
    }
    """
    try:
        response = supabase_client.table("transactions_pending") \
            .select("*") \
            .eq("company_id", company_id) \
            .eq("status", "pending") \
            .order("date", desc=True) \
            .execute()

        return {
            "count": len(response.data),
            "transactions": response.data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching pending transactions: {str(e)}"
        )
