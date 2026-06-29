"""
Financials aggregation service for Pulso snapshot computation.

Aggregates Caja Real, ventas_periodo, and salidas_periodo from erp_journal_lines
for a given tenant and period.
"""

from typing import Dict, Any
from datetime import date
from core.supabase_client import get_supabase


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


def compute_pulso_snapshot(tenant_id: str, year: int, month: int) -> Dict[str, Any]:
    """
    Compute the Pulso financials snapshot for a tenant in a given year/month.

    Args:
        tenant_id: Tenant UUID
        year: Year (e.g., 2026)
        month: Month (1-12)

    Returns:
        Dict with keys:
        - caja_real (int): Bank account balance in COP minor units (cents)
        - ventas_periodo (int): Sum of income credits in COP minor units
        - salidas_periodo (int): Sum of expense debits in COP minor units
        - dinero_disponible (int): Alias for caja_real (MVP: same value)
        - status (str): "healthy" (caja_real > 0) or "empty" (no data)
    """
    supabase = get_supabase()

    # Determine the month range
    from calendar import monthrange

    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    # Query: all journal lines for the tenant in this month
    result = (
        supabase.table("erp_journal_lines")
        .select(
            "account_code, debit_minor, credit_minor, entry_id, "
            "erp_journal_entries!inner(entry_date)"
        )
        .eq("tenant_id", tenant_id)
        .gte("erp_journal_entries.entry_date", month_start.isoformat())
        .lte("erp_journal_entries.entry_date", month_end.isoformat())
        .execute()
    )

    lines = result.data or []

    if not lines:
        return {
            "caja_real": 0,
            "dinero_disponible": 0,
            "ventas_periodo": 0,
            "salidas_periodo": 0,
            "status": "empty",
        }

    # Aggregate by account classification
    caja_real = 0
    ventas_periodo = 0
    salidas_periodo = 0

    for line in lines:
        account_code = line.get("account_code", "")
        debit_minor = line.get("debit_minor", 0) or 0
        credit_minor = line.get("credit_minor", 0) or 0

        # Caja Real: account 1110 (Bancos)
        if account_code == "1110":
            caja_real += debit_minor - credit_minor

        # Ventas: income accounts 4100, 4105
        if account_code in ("4100", "4105"):
            ventas_periodo += credit_minor

        # Salidas: expense accounts starting with 5 or 6
        if account_code.startswith("5") or account_code.startswith("6"):
            salidas_periodo += debit_minor

    # Status classification
    status = "healthy" if caja_real > 0 else "empty"

    return {
        "caja_real": caja_real,
        "dinero_disponible": caja_real,  # MVP: same as caja_real
        "ventas_periodo": ventas_periodo,
        "salidas_periodo": salidas_periodo,
        "status": status,
    }
