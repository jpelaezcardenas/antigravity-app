"""crm_leads.stage (+ crm_wompi_transactions.status) -> HubSpot dealstage.

See openspec/changes/hubspot-sync-renta-natural/design.md Decision #4 (corrected 2026-08-15
after discovering the real crm_leads.stage CHECK constraint diverged from the original design).
"""

from __future__ import annotations

from typing import Optional

STAGE_MAPPING = {
    "NUEVOS": "appointmentscheduled",
    "PROSPECTOS": "qualifiedtobuy",
    "POR_APROBAR": "presentationscheduled",
    "LISTOS_CONTADORA": "decisionmakerboughtin",
}

_WOMPI_OVERRIDE = {
    "APPROVED": "closedwon",
    "DECLINED": "closedlost",
}


def resolve_dealstage(lead_stage: str, wompi_status: Optional[str] = None) -> str:
    """Resolves the HubSpot dealstage for a lead. A PENDING or missing Wompi transaction leaves
    the stage-based mapping untouched; APPROVED/DECLINED overrides it (design.md Decision #4)."""
    if wompi_status in _WOMPI_OVERRIDE:
        return _WOMPI_OVERRIDE[wompi_status]
    return STAGE_MAPPING.get(lead_stage, STAGE_MAPPING["NUEVOS"])
