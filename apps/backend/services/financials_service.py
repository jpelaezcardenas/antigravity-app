"""
Financials aggregation service for Pulso snapshot computation.

Aggregates Caja Real, ventas, and salidas from erp_journal_lines for a given
tenant, either over a calendar month (`compute_pulso_snapshot`) or as a daily
pulse — balance as of today, sales/expenses for yesterday specifically
(`compute_pulso_daily_snapshot`).
"""

from typing import Dict, Any, List
from datetime import date, timedelta
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


def _compute_caja_real_balance(supabase, tenant_id: str, as_of_date: date) -> int:
    """
    Cumulative balance of account 1110 (Bancos) for ALL entries dated on or
    before `as_of_date` — not bounded by a single calendar month/day. A bank
    balance carries over from prior periods; computing it only from one
    period's movements would understate (or misreport) the real balance.
    """
    result = (
        supabase.table("erp_journal_lines")
        .select("debit_minor, credit_minor, erp_journal_entries!inner(entry_date)")
        .eq("tenant_id", tenant_id)
        .eq("account_code", "1110")
        .lte("erp_journal_entries.entry_date", as_of_date.isoformat())
        .execute()
    )
    lines = result.data or []
    return sum(
        (line.get("debit_minor", 0) or 0) - (line.get("credit_minor", 0) or 0)
        for line in lines
    )


def _classify_ventas_salidas(lines: List[dict]) -> tuple[int, int]:
    """Sum income credits (4100/4105) and expense debits (5xxx/6xxx) from journal lines."""
    ventas = 0
    salidas = 0
    for line in lines:
        account_code = line.get("account_code", "")
        debit_minor = line.get("debit_minor", 0) or 0
        credit_minor = line.get("credit_minor", 0) or 0

        if account_code in ("4100", "4105"):
            ventas += credit_minor
        if account_code.startswith("5") or account_code.startswith("6"):
            salidas += debit_minor

    return ventas, salidas


def compute_pulso_snapshot(tenant_id: str, year: int, month: int) -> Dict[str, Any]:
    """
    Compute the Pulso financials snapshot for a tenant in a given year/month.

    Args:
        tenant_id: Tenant UUID
        year: Year (e.g., 2026)
        month: Month (1-12)

    Returns:
        Dict with keys:
        - caja_real (int): Cumulative bank account balance through the end of
          the period, in COP minor units (cents) — NOT bounded to this
          month's movements alone.
        - ventas_periodo (int): Sum of income credits within the month, in COP minor units
        - salidas_periodo (int): Sum of expense debits within the month, in COP minor units
        - dinero_disponible (int): Alias for caja_real (MVP: same value)
        - status (str): "healthy" (caja_real > 0) or "empty" (no data / non-positive balance)
    """
    supabase = get_supabase()

    from calendar import monthrange

    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    caja_real = _compute_caja_real_balance(supabase, tenant_id, month_end)

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

    ventas_periodo, salidas_periodo = _classify_ventas_salidas(lines)

    status = "healthy" if caja_real > 0 else "empty"

    return {
        "caja_real": caja_real,
        "dinero_disponible": caja_real,  # MVP: same as caja_real
        "ventas_periodo": ventas_periodo,
        "salidas_periodo": salidas_periodo,
        "status": status,
    }


def compute_pulso_daily_snapshot(tenant_id: str, as_of_date: date) -> Dict[str, Any]:
    """
    Compute the "Pulso diario" snapshot for a tenant as of a given date — the
    daily-granularity promise behind the real CashTodayCard component
    (lib/types/contexia.ts: CashToday { total, yours, yesterdaySales, expenses }).

    Args:
        tenant_id: Tenant UUID
        as_of_date: The "today" the snapshot is computed for (caller passes
            the real current date in production; tests pass a fixed date).

    Returns:
        Dict with keys:
        - caja_real (int): Cumulative bank account balance through as_of_date
          (inclusive), in COP minor units.
        - dinero_disponible (int): Alias for caja_real (MVP: same value).
        - ventas_ayer (int): Income credits (4100/4105) dated exactly the day
          before as_of_date, in COP minor units.
        - gastos_ayer (int): Expense debits (5xxx/6xxx) dated exactly the day
          before as_of_date, in COP minor units.
        - status (str): "healthy" (caja_real > 0) or "empty" (non-positive balance)
    """
    supabase = get_supabase()
    yesterday = as_of_date - timedelta(days=1)

    caja_real = _compute_caja_real_balance(supabase, tenant_id, as_of_date)

    result = (
        supabase.table("erp_journal_lines")
        .select(
            "account_code, debit_minor, credit_minor, "
            "erp_journal_entries!inner(entry_date)"
        )
        .eq("tenant_id", tenant_id)
        .eq("erp_journal_entries.entry_date", yesterday.isoformat())
        .execute()
    )
    lines = result.data or []

    ventas_ayer, gastos_ayer = _classify_ventas_salidas(lines)

    status = "healthy" if caja_real > 0 else "empty"

    return {
        "caja_real": caja_real,
        "dinero_disponible": caja_real,
        "ventas_ayer": ventas_ayer,
        "gastos_ayer": gastos_ayer,
        "status": status,
    }
