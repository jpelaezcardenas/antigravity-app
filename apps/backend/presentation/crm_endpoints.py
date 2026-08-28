"""CRM/Ventas B2B retainer endpoints (crm-b2b-retainers-cockpit, Change A).

Mounted at /api/v1/crm behind the CRM_CANONICAL feature flag (see presentation/router.py).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from postgrest.exceptions import APIError

from core.deps import get_current_user
from services.crm_service import get_crm_service
from services.retention_service import get_retention_service

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


@router.get("/b2b/retention-alerts")
def get_retention_alerts():
    """Evaluates the B2B roster for churn/risk signals (missed_payment, payment_drop) and
    returns current alert history (retention-loop). Evaluation runs on-demand on each call,
    same pattern as b2b_payments_grid's on-the-fly pivot."""
    return {"items": get_retention_service().evaluate_and_persist()}


class CreateB2bClientRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None
    monthly_fee_cents: Optional[int] = Field(default=None, ge=0)
    plan_tier: Optional[str] = None
    opening_balance_cents: Optional[int] = Field(default=None, ge=0)


@router.post("/b2b/clients")
def create_b2b_client(payload: CreateB2bClientRequest):
    """Alta: add a client to the roster (own tenant + best-effort login provisioning
    if an email is given). See B2bRetainersTab.tsx's alta form.

    plan_tier (plan-tier-feature-gating): omitted -> service-layer default ("starter");
    an invalid value raises ValueError -> 400, not a raw Postgres CHECK violation."""
    kwargs: Dict[str, Any] = dict(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        contact_name=payload.contact_name,
        monthly_fee_cents=payload.monthly_fee_cents,
    )
    if payload.plan_tier is not None:
        kwargs["plan_tier"] = payload.plan_tier
    if payload.opening_balance_cents is not None:
        kwargs["opening_balance_cents"] = payload.opening_balance_cents
    try:
        return get_crm_service().create_b2b_client(**kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class SetB2bClientStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


@router.patch("/b2b/clients/{client_id}/status")
def set_b2b_client_status(client_id: str, payload: SetB2bClientStatusRequest):
    """Baja/reactivar: activo <-> inactivo, and deactivates/reactivates the client's
    login membership in lockstep."""
    try:
        return get_crm_service().set_b2b_client_status(client_id, payload.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class UpsertB2bPaymentRequest(BaseModel):
    period: str = Field(..., min_length=1)
    amount_cents: int = Field(..., ge=0)


@router.put("/b2b/clients/{client_id}/payments")
def upsert_b2b_payment(client_id: str, payload: UpsertB2bPaymentRequest):
    """Pago: record/correct one client's payment for one calendar month (idempotent)."""
    try:
        return get_crm_service().upsert_b2b_payment(client_id, payload.period, payload.amount_cents)
    except (APIError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class UpdateB2bClientContactRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_name: Optional[str] = None


@router.patch("/b2b/clients/{client_id}/contact")
def update_b2b_client_contact(client_id: str, payload: UpdateB2bClientContactRequest):
    """Edit a client's captured contact info (email/phone/contact person)."""
    try:
        return get_crm_service().update_b2b_client_contact(
            client_id, email=payload.email, phone=payload.phone, contact_name=payload.contact_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


class WhatsappIntakeRequest(BaseModel):
    whatsapp_phone: str = Field(..., min_length=1)


@router.post("/leads/whatsapp-intake")
def whatsapp_intake(payload: WhatsappIntakeRequest):
    """Find-or-create a crm_leads row by WhatsApp phone number (chatwoot-hermes-taty-bridge,
    Task Group 1) — called by the Chatwoot bridge on every inbound WhatsApp message."""
    return get_crm_service().whatsapp_intake(payload.whatsapp_phone)


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
