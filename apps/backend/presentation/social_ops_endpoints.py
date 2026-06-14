"""Social Content Ops API endpoints."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.social_ops_service import get_social_ops_service

router = APIRouter(tags=["social-ops"])


class SocialOpsEventRequest(BaseModel):
    channel: str = Field(..., description="telegram, facebook, instagram, tiktok or linkedin")
    event_type: str = Field(default="message")
    text: str = Field(..., min_length=1)
    actor_handle: str = Field(..., min_length=1)
    actor_name: str = ""
    source_event_id: str = ""
    account_id: str = ""
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class DiagnoseRequest(BaseModel):
    event_id: Optional[str] = None
    lead_id: Optional[str] = None
    notes: str = ""


class CommandParseRequest(BaseModel):
    text: str = Field(..., min_length=1)
    channel: str = "telegram"
    actor_handle: str = ""
    lead_id: Optional[str] = None


class OnboardingStartRequest(BaseModel):
    company_name: str = Field(..., min_length=1)
    customer_email: str = Field(..., min_length=3)
    payment_reference: str = Field(..., min_length=1)
    plan_name: str = "Starter"
    owner_handle: str = ""
    company_id: str = ""
    requested_channels: list[str] = Field(
        default_factory=lambda: ["telegram", "instagram", "linkedin"]
    )


class OnboardingStepRequest(BaseModel):
    status: str = "completed"
    notes: str = ""


class OnboardingSeedRequest(BaseModel):
    business_summary: str = ""
    initial_channels: list[str] = Field(default_factory=list)


class OnboardingIntakeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = "dashboard"
    actor_handle: str = ""


@router.get("/pipeline")
def get_pipeline():
    return get_social_ops_service().get_pipeline()


@router.get("/inbox")
def get_inbox(
    limit: int = Query(default=50, ge=1, le=200),
    channel: Optional[str] = None,
    status: Optional[str] = None,
):
    return get_social_ops_service().get_inbox(limit=limit, channel=channel, status=status)


@router.get("/integrations")
def get_integrations():
    return get_social_ops_service().get_integrations()


@router.get("/onboarding")
def get_onboarding():
    return get_social_ops_service().get_onboarding()


@router.post("/events/simulate")
def simulate_event(payload: SocialOpsEventRequest):
    try:
        return get_social_ops_service().simulate_event(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/diagnose")
def diagnose(payload: DiagnoseRequest):
    try:
        return get_social_ops_service().diagnose(
            event_id=payload.event_id,
            lead_id=payload.lead_id,
            notes=payload.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/commands/parse")
def parse_command(payload: CommandParseRequest):
    try:
        return get_social_ops_service().parse_command(
            text=payload.text,
            channel=payload.channel,
            actor_handle=payload.actor_handle,
            lead_id=payload.lead_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/onboarding/start")
def start_onboarding(payload: OnboardingStartRequest):
    try:
        return get_social_ops_service().start_onboarding(
            company_name=payload.company_name,
            customer_email=payload.customer_email,
            payment_reference=payload.payment_reference,
            plan_name=payload.plan_name,
            owner_handle=payload.owner_handle,
            requested_channels=payload.requested_channels,
            company_id=payload.company_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/service-desk/tickets")
def list_service_tickets(company_id: str = "", limit: int = Query(default=50, ge=1, le=200)):
    return get_social_ops_service().get_service_desk(company_id=company_id, limit=limit)


class ServiceDeskTicketRequest(BaseModel):
    company_id: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    actor_handle: str = ""
    subject: str = ""
    body: str = Field(..., min_length=1)
    source_event_id: str = ""


@router.post("/service-desk/tickets")
def create_service_ticket(payload: ServiceDeskTicketRequest):
    try:
        return get_social_ops_service().create_service_ticket(
            company_id=payload.company_id,
            channel=payload.channel,
            actor_handle=payload.actor_handle,
            subject=payload.subject,
            body=payload.body,
            source_event_id=payload.source_event_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class ServiceDeskReplyDraftRequest(BaseModel):
    reply_text: str = Field(..., min_length=1)
    actor_handle: str = "taty"


@router.post("/service-desk/tickets/{ticket_id}/reply-draft")
def draft_service_reply(ticket_id: str, payload: ServiceDeskReplyDraftRequest):
    try:
        return get_social_ops_service().draft_service_reply(
            ticket_id=ticket_id, reply_text=payload.reply_text, actor_handle=payload.actor_handle
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class LeadReplyDraftRequest(BaseModel):
    lead_id: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    intent: str = ""
    include_shadow_audit_link: bool = True
    actor_handle: str = "taty"


@router.post("/leads/reply-draft")
def create_lead_reply_draft(payload: LeadReplyDraftRequest):
    try:
        return get_social_ops_service().draft_lead_reply(
            lead_id=payload.lead_id,
            channel=payload.channel,
            intent=payload.intent,
            include_shadow_audit_link=payload.include_shadow_audit_link,
            actor_handle=payload.actor_handle,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class SalesDraftRequest(BaseModel):
    lead_id: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    objective: str = "shadow_audit_booking"
    actor_handle: str = "taty"


@router.post("/leads/sales-draft")
def create_sales_draft(payload: SalesDraftRequest):
    try:
        return get_social_ops_service().draft_sales_closure(
            lead_id=payload.lead_id,
            channel=payload.channel,
            objective=payload.objective,
            actor_handle=payload.actor_handle,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/approvals")
def list_approvals(limit: int = Query(default=200, ge=1, le=500)):
    return get_social_ops_service().get_approval_queue(limit=limit)


class ApprovalActionRequest(BaseModel):
    actor_handle: str = Field(..., min_length=1)
    reason: str = ""


@router.post("/approvals/{draft_type}/{draft_id}/approve")
def approve_draft(draft_type: str, draft_id: str, payload: ApprovalActionRequest):
    try:
        return get_social_ops_service().approve_draft(draft_type, draft_id, approved_by=payload.actor_handle)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/approvals/{draft_type}/{draft_id}/reject")
def reject_draft(draft_type: str, draft_id: str, payload: ApprovalActionRequest):
    try:
        return get_social_ops_service().reject_draft(
            draft_type, draft_id, rejected_by=payload.actor_handle, reason=payload.reason
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/ideas")
def list_ideas():
    return get_social_ops_service().list_ideas()


class IdeaStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)


@router.post("/ideas/{idea_id}/status")
def update_idea_status(idea_id: int, payload: IdeaStatusRequest):
    try:
        return get_social_ops_service().update_idea_status(idea_id=idea_id, status=payload.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ideas/{idea_id}/generate-draft")
def generate_idea_draft(idea_id: int):
    try:
        return get_social_ops_service().generate_idea_draft(idea_id=idea_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/metrics")
def metrics_dashboard():
    return get_social_ops_service().get_metrics_dashboard()


@router.post("/metrics/simulate")
def simulate_metrics():
    return get_social_ops_service().simulate_metrics()


@router.post("/onboarding/{workspace_id}/steps/{step_id}/advance")
def advance_onboarding_step(workspace_id: str, step_id: str, payload: OnboardingStepRequest):
    try:
        return get_social_ops_service().advance_onboarding_step(
            workspace_id=workspace_id,
            step_id=step_id,
            status=payload.status,
            notes=payload.notes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/onboarding/{workspace_id}/seed")
def create_onboarding_seed(workspace_id: str, payload: OnboardingSeedRequest):
    try:
        return get_social_ops_service().create_onboarding_seed(
            workspace_id=workspace_id,
            business_summary=payload.business_summary,
            initial_channels=payload.initial_channels or None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/onboarding/{workspace_id}/intake")
def intake_onboarding(workspace_id: str, payload: OnboardingIntakeRequest):
    try:
        return get_social_ops_service().intake_onboarding(
            workspace_id=workspace_id,
            text=payload.text,
            source=payload.source,
            actor_handle=payload.actor_handle,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
