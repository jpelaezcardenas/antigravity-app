"""CRM/Ventas B2B retainer endpoints (crm-b2b-retainers-cockpit, Change A).

Mounted at /api/v1/crm behind the CRM_CANONICAL feature flag (see presentation/router.py).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from services.crm_service import get_crm_service

router = APIRouter(tags=["crm"])


@router.get("/b2b/clients")
def list_b2b_clients():
    return get_crm_service().list_b2b_clients()


@router.get("/b2b/payments")
def get_b2b_payments_grid(
    from_period: Optional[str] = Query(default="2026-01-01"),
    to_period: Optional[str] = Query(default="2026-06-30"),
):
    return get_crm_service().b2b_payments_grid(from_period=from_period, to_period=to_period)
