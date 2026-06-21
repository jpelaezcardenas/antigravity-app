"""
Centinela Resolution Poller

Polls the `shadow_gl_discrepancies` materialized view for unresolved DIAN
vs. ERP discrepancies and creates one `centinela_alerts` row per new
discrepancy, deduplicating against discrepancies that already have an
alert (identified by `rule_id` + `cufe` stored in `evidence`).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

SHADOW_GL_DISCREPANCY_RULE_ID = "SHADOW_GL_DISCREPANCY"

UNRESOLVED_STATUSES = ("missing_in_erp", "amount_mismatch")


def _resolve_company_id(supabase: Any, tenant_id: str) -> str:
    """
    Resolve a Shadow GL `tenants.id` (uuid) to the `agent_profiles.company_id`
    (text) that `centinela_alerts.company_id` is FK'd to. These are two
    separate identity models for the same company (see design.md Slice 2
    correction, 2026-06-21).
    """
    result = (
        supabase.table("tenants")
        .select("company_id")
        .eq("id", tenant_id)
        .single()
        .execute()
    )
    company_id = result.data["company_id"]
    if not company_id:
        raise ValueError(f"Tenant {tenant_id} has no linked agent_profiles.company_id")
    return company_id


def _existing_alert_cufes(supabase: Any, company_id: str) -> set[str]:
    result = (
        supabase.table("centinela_alerts")
        .select("evidence")
        .eq("rule_id", SHADOW_GL_DISCREPANCY_RULE_ID)
        .eq("company_id", company_id)
        .execute()
    )
    return {row["evidence"]["cufe"] for row in result.data if row.get("evidence", {}).get("cufe")}


def _alert_payload(company_id: str, discrepancy: Dict[str, Any]) -> Dict[str, Any]:
    cufe = discrepancy["cufe"]
    status = discrepancy["status"]
    return {
        "company_id": company_id,
        "rule_id": SHADOW_GL_DISCREPANCY_RULE_ID,
        "rule_name": "Shadow GL Discrepancy",
        "severity": "high" if status == "missing_in_erp" else "medium",
        "title": f"Discrepancia Shadow GL: {status} ({cufe})",
        "description": (
            f"El documento DIAN con CUFE {cufe} presenta estado '{status}' al "
            f"reconciliarse contra el libro mayor ERP."
        ),
        "recommendation": "Revisar y generar un draft de corrección para sincronizar el ERP con el documento DIAN.",
        "evidence": {
            "cufe": cufe,
            "discrepancy_status": status,
            "dian_total_minor": discrepancy.get("dian_total_minor"),
            "erp_total_minor": discrepancy.get("erp_total_minor"),
            "variance_minor": discrepancy.get("variance_minor"),
        },
        "status": "open",
        "requires_human_review": True,
    }


async def poll_shadow_gl_discrepancies(tenant_id: str) -> List[str]:
    """
    Poll `shadow_gl_discrepancies` for the given tenant and create one
    `centinela_alerts` row per new discrepancy. Discrepancies that already
    have an alert (matched by CUFE) are skipped.

    Returns:
        List of newly created `centinela_alerts` row ids.
    """
    supabase = get_supabase()

    discrepancies = (
        supabase.table("shadow_gl_discrepancies")
        .select("*")
        .eq("tenant_id", tenant_id)
        .in_("status", UNRESOLVED_STATUSES)
        .execute()
    )

    if not discrepancies.data:
        return []

    company_id = _resolve_company_id(supabase, tenant_id)
    already_alerted = _existing_alert_cufes(supabase, company_id)

    created_ids: List[str] = []
    for discrepancy in discrepancies.data:
        cufe = discrepancy["cufe"]
        if cufe in already_alerted:
            continue

        inserted = (
            supabase.table("centinela_alerts")
            .insert(_alert_payload(company_id, discrepancy))
            .execute()
        )
        created_ids.append(inserted.data[0]["id"])
        already_alerted.add(cufe)

    if created_ids:
        logger.info(
            f"Created {len(created_ids)} Shadow GL discrepancy alert(s) for tenant {tenant_id}"
        )

    return created_ids
