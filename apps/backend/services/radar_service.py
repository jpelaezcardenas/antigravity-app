"""
Radar Service

Deterministic risk-score calculation (0-100) based on Shadow GL history.
Risk score combines four weighted factors:
1. Discrepancy rate (invoices with discrepancies / total invoices) — 40 pts
2. Amount mismatch severity (sum of mismatches / total invoiced amount) — 30 pts
3. Alert frequency (Centinela alerts this month) — 20 pts
4. Days overdue (max days any invoice is overdue) — 10 pts

All computations are deterministic (same inputs always produce same output).
Zero-division safe: defaults to 0 if no history.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


async def calculate_risk_score(tenant_id: str, date: Optional[str] = None) -> int:
    """
    Calculate a deterministic risk score (0-100) for a tenant based on Shadow GL history.

    Factors (total 100 points):
    - Discrepancy rate (40 pts): (discrepancies / total_invoices) × 100, capped at 40
    - Amount mismatch (30 pts): (sum_mismatches / total_invoiced_amount) × 100, capped at 30
    - Alert frequency (20 pts): alerts_this_month × 4, capped at 20
    - Days overdue (10 pts): (max_days_overdue / 30) × 10, capped at 10

    Args:
        tenant_id: UUID of the tenant
        date: Optional date for filtering (default: today). Used for alert frequency window.

    Returns:
        int: Risk score from 0 to 100. Returns 0 if no history.
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    supabase = get_supabase()

    # Factor 1: Discrepancy Rate (40 pts)
    # Count total DIAN invoices and invoices with discrepancies
    try:
        dian_docs = (
            supabase.table("dian_xml_documents")
            .select("id, cufe")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        total_invoices = len(dian_docs.data)

        if total_invoices > 0:
            # Get unique CUFEs with discrepancies
            discrepancies = (
                supabase.table("shadow_gl_discrepancies")
                .select("cufe")
                .eq("tenant_id", tenant_id)
                .execute()
            )
            discrepancy_cufes = set(d["cufe"] for d in discrepancies.data)
            discrepancy_count = len(discrepancy_cufes)
            discrepancy_rate = (discrepancy_count / total_invoices) * 100
            factor_discrepancy = min(40, discrepancy_rate)
        else:
            factor_discrepancy = 0.0
    except Exception as e:
        logger.warning(f"Error calculating discrepancy rate for tenant {tenant_id}: {e}")
        factor_discrepancy = 0.0

    # Factor 2: Amount Mismatch Severity (30 pts)
    # Sum of absolute differences in amounts as % of total invoiced
    try:
        discrepancies = (
            supabase.table("shadow_gl_discrepancies")
            .select("variance_minor, status")
            .eq("tenant_id", tenant_id)
            .execute()
        )

        total_variance = sum(
            abs(d["variance_minor"] or 0) for d in discrepancies.data if d["status"] == "amount_mismatch"
        )

        dian_totals = (
            supabase.table("dian_xml_documents")
            .select("total_amount_minor")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        total_invoiced_minor = sum(d["total_amount_minor"] for d in dian_totals.data)

        if total_invoiced_minor > 0:
            mismatch_ratio = (total_variance / total_invoiced_minor) * 100
            factor_mismatch = min(30, mismatch_ratio)
        else:
            factor_mismatch = 0.0
    except Exception as e:
        logger.warning(f"Error calculating amount mismatch for tenant {tenant_id}: {e}")
        factor_mismatch = 0.0

    # Factor 3: Alert Frequency This Month (20 pts)
    # Count Centinela alerts in the current month
    try:
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Resolve tenant_id to company_id for centinela_alerts lookup
        tenant_row = (
            supabase.table("tenants")
            .select("company_id")
            .eq("id", tenant_id)
            .single()
            .execute()
        )
        company_id = tenant_row.data.get("company_id")

        if company_id:
            alerts_this_month = (
                supabase.table("centinela_alerts")
                .select("id")
                .eq("company_id", company_id)
                .eq("rule_id", "SHADOW_GL_DISCREPANCY")
                .gte("created_at", month_start.isoformat() + "Z")
                .lt("created_at", (today + timedelta(days=1)).isoformat() + "Z")
                .execute()
            )
            alert_count = len(alerts_this_month.data)
            factor_alerts = min(20, alert_count * 4)
        else:
            factor_alerts = 0.0
    except Exception as e:
        logger.warning(f"Error calculating alert frequency for tenant {tenant_id}: {e}")
        factor_alerts = 0.0

    # Factor 4: Days Overdue (10 pts)
    # Maximum days any invoice is overdue based on issue_date
    try:
        dian_docs = (
            supabase.table("dian_xml_documents")
            .select("issue_date")
            .eq("tenant_id", tenant_id)
            .execute()
        )

        if dian_docs.data:
            today = datetime.utcnow().date()
            max_days_overdue = 0
            for doc in dian_docs.data:
                if doc.get("issue_date"):
                    issue_date = datetime.fromisoformat(doc["issue_date"]).date()
                    days_diff = (today - issue_date).days
                    max_days_overdue = max(max_days_overdue, days_diff)

            # Assume 30-day payment term: overdue if > 30 days old
            actual_overdue_days = max(0, max_days_overdue - 30)
            factor_overdue = min(10, (actual_overdue_days / 30) * 10) if actual_overdue_days > 0 else 0.0
        else:
            factor_overdue = 0.0
    except Exception as e:
        logger.warning(f"Error calculating days overdue for tenant {tenant_id}: {e}")
        factor_overdue = 0.0

    # Combine all factors, cap at 100
    total_score = min(100, factor_discrepancy + factor_mismatch + factor_alerts + factor_overdue)

    return int(total_score)


async def calculate_cashflow_forecast(tenant_id: str, days: int = 30) -> int:
    """
    Calculate a 30-day cashflow forecast (minor units) based on historical net flux.

    Net flux = sum(DIAN invoiced) - sum(ERP posted) over the last 30 days.
    Forecast = (net_flux / historical_days) × forecast_days

    Args:
        tenant_id: UUID of the tenant
        days: Forecast horizon in days (default: 30)

    Returns:
        int: Projected net cashflow for the next N days in minor units. >= 0.
             Returns 0 if no historical data.
    """
    supabase = get_supabase()

    try:
        # Calculate lookback window (last 30 days)
        today = datetime.utcnow()
        lookback_start = today - timedelta(days=30)
        lookback_start_str = lookback_start.isoformat() + "Z"
        today_str = today.isoformat() + "Z"

        # Sum DIAN invoiced in lookback window
        dian_rows = (
            supabase.table("dian_xml_documents")
            .select("total_amount_minor")
            .eq("tenant_id", tenant_id)
            .gte("created_at", lookback_start_str)
            .lte("created_at", today_str)
            .execute()
        )
        total_dian_minor = sum(row["total_amount_minor"] for row in dian_rows.data)

        # Sum ERP posted in lookback window
        erp_entries = (
            supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", tenant_id)
            .gte("created_at", lookback_start_str)
            .lte("created_at", today_str)
            .execute()
        )

        total_erp_minor = 0
        if erp_entries.data:
            erp_lines = (
                supabase.table("erp_journal_lines")
                .select("debit_minor")
                .eq("tenant_id", tenant_id)
                .in_("entry_id", [row["id"] for row in erp_entries.data])
                .execute()
            )
            total_erp_minor = sum(line["debit_minor"] for line in erp_lines.data)

        # Net flux over lookback period
        net_flux_minor = total_dian_minor - total_erp_minor

        # Project to forecast horizon
        # If we have 30 days of history, project for the next N days
        if net_flux_minor > 0:
            # Simple linear projection: (net_flux / 30) × forecast_days
            forecast_minor = int((net_flux_minor / 30) * days)
        else:
            # If net flux is 0 or negative, forecast is 0 (conservative)
            forecast_minor = 0

        return forecast_minor

    except Exception as e:
        logger.warning(f"Error calculating cashflow forecast for tenant {tenant_id}: {e}")
        return 0
