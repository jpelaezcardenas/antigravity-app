"""CRM/Ventas B2B retainer endpoints (crm-b2b-retainers-cockpit, Change A).

Mounted at /api/v1/crm behind the CRM_CANONICAL feature flag (see presentation/router.py).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core.deps import get_current_user
from services.crm_service import get_crm_service

router = APIRouter(tags=["crm"], dependencies=[Depends(get_current_user)])


@router.get("/b2b/clients")
def list_b2b_clients():
    return get_crm_service().list_b2b_clients()


@router.get("/b2b/payments")
def get_b2b_payments_grid(
    from_period: Optional[str] = Query(default="2026-01-01"),
    to_period: Optional[str] = Query(default="2026-06-30"),
):
    return get_crm_service().b2b_payments_grid(from_period=from_period, to_period=to_period)


@router.get("/b2c/pipeline")
def get_b2c_pipeline():
    return get_crm_service().b2c_pipeline()


class AdvanceLeadRequest(BaseModel):
    stage: str = Field(..., min_length=1)


@router.post("/leads/{lead_id}/advance")
def advance_lead(lead_id: str, payload: AdvanceLeadRequest):
    try:
        return get_crm_service().advance_lead(lead_id, payload.stage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/leads/{lead_id}/tax-profile")
def get_lead_tax_profile(lead_id: str):
    return get_crm_service().get_tax_profile(lead_id)


@router.patch("/leads/{lead_id}/tax-profile")
def patch_lead_tax_profile(lead_id: str, payload: Dict[str, Any]):
    return get_crm_service().update_tax_profile(lead_id, payload)


class ApprovePaymentRequest(BaseModel):
    approved_by: str = Field(..., min_length=1)


@router.post("/leads/{lead_id}/approve-payment")
async def approve_lead_payment(lead_id: str, payload: ApprovePaymentRequest):
    try:
        return await get_crm_service().approve_payment(lead_id, approved_by=payload.approved_by)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/leads/{lead_id}/checkout")
def checkout_lead_payment(lead_id: str):
    """Create a signed Wompi checkout for a lead's Renta Natural payment.

    See openspec/changes/wompi-payment-integration ("Change C" for
    crm-b2c-sell-machine-cockpit's crm_wompi_transactions table).
    """
    try:
        return get_crm_service().checkout_lead_payment(lead_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/wompi/webhook")
async def wompi_webhook(request: Request):
    """Receive and verify a Wompi transaction-status event.

    Public endpoint (Wompi has no user session) — the signature check IS the
    access control. See services.crm_service.handle_wompi_webhook.
    """
    event = await request.json()
    try:
        return get_crm_service().handle_wompi_webhook(event)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
