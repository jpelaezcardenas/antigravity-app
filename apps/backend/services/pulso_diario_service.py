"""
Pulso Diario Service

Daily aggregation of Shadow GL activity: DIAN invoiced total, ERP posted total,
discrepancies detected, alerts generated. Read-only, no write operations.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)


async def get_daily_summary(tenant_id: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Pulso Diario summary for a given date (default: today).

    Returns:
        {
            "date": "2026-06-21",
            "tenant_id": "...",
            "dian_total_minor": 500000000,  # BIGINT minor units (centavos)
            "dian_invoice_count": 3,
            "erp_posted_minor": 480000000,
            "erp_entry_count": 2,
            "discrepancy_count": 1,  # missing_in_erp + amount_mismatch
            "discrepancies_by_status": {
                "missing_in_erp": 1,
                "amount_mismatch": 0,
            },
            "alerts_generated": 0,  # Centinela alerts created today
        }
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    supabase = get_supabase()

    # Query DIAN XML documents for the date
    dian_rows = (
        supabase.table("dian_xml_documents")
        .select("total_amount_minor")
        .eq("tenant_id", tenant_id)
        .gte("created_at", f"{date}T00:00:00Z")
        .lt("created_at", f"{date}T23:59:59Z")
        .execute()
    )
    dian_total_minor = sum(row["total_amount_minor"] for row in dian_rows.data)
    dian_invoice_count = len(dian_rows.data)

    # Query ERP journal entries for the date
    erp_rows = (
        supabase.table("erp_journal_entries")
        .select("id")
        .eq("tenant_id", tenant_id)
        .gte("created_at", f"{date}T00:00:00Z")
        .lt("created_at", f"{date}T23:59:59Z")
        .execute()
    )
    erp_entry_count = len(erp_rows.data)

    # Query discrepancies (note: this is the current view, not filtered by date)
    # For a true daily summary, we'd need to track discrepancy creation_at
    discrepancies = (
        supabase.table("shadow_gl_discrepancies")
        .select("status")
        .eq("tenant_id", tenant_id)
        .execute()
    )
    discrepancy_count = len(discrepancies.data)
    discrepancies_by_status = {}
    for d in discrepancies.data:
        status = d["status"]
        discrepancies_by_status[status] = discrepancies_by_status.get(status, 0) + 1

    # Query Centinela alerts for the date (Shadow GL discrepancy rule)
    alerts = (
        supabase.table("centinela_alerts")
        .select("id")
        .eq("company_id", tenant_id)  # Note: centinela_alerts uses company_id, not tenant_id
        .eq("rule_id", "SHADOW_GL_DISCREPANCY")
        .gte("created_at", f"{date}T00:00:00Z")
        .lt("created_at", f"{date}T23:59:59Z")
        .execute()
    )
    alerts_generated = len(alerts.data)

    # Calculate ERP posted total (sum of debit amounts from journal lines)
    if erp_entry_count > 0:
        erp_lines = (
            supabase.table("erp_journal_lines")
            .select("debit_minor")
            .eq("tenant_id", tenant_id)
            .in_("entry_id", [row["id"] for row in erp_rows.data])
            .execute()
        )
        erp_posted_minor = sum(line["debit_minor"] for line in erp_lines.data)
    else:
        erp_posted_minor = 0

    return {
        "date": date,
        "tenant_id": tenant_id,
        "dian_total_minor": dian_total_minor,
        "dian_invoice_count": dian_invoice_count,
        "erp_posted_minor": erp_posted_minor,
        "erp_entry_count": erp_entry_count,
        "discrepancy_count": discrepancy_count,
        "discrepancies_by_status": discrepancies_by_status,
        "alerts_generated": alerts_generated,
    }
