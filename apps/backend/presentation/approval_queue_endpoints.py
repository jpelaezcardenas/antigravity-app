"""
Approval Queue Endpoints

GET  /api/v1/approval-queue - List drafts (filter by status, draft_type)
POST /api/v1/approval-queue/enqueue - Enqueue draft with Critic validation
POST /api/v1/approval-queue/approve - Approve a draft and trigger vectorization
POST /api/v1/approval-queue/reject - Reject a draft
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
import logging

from core.deps import get_current_user
from core.supabase_client import get_service_supabase
from core.tenant_context import resolve_request_tenant_scope
from services.approval_queue_service import ApprovalQueueService

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class JournalLine(BaseModel):
    account: str
    debit: float = 0
    credit: float = 0
    description: str = ""


class EnqueueRequest(BaseModel):
    draft_id: str
    draft_type: str  # tax_correction, adjustment, etc.
    lines: List[JournalLine]
    memo: str = ""


class ApprovalRequest(BaseModel):
    decision_id: str
    reason: str
    approved_by: str  # Email of contador


class RejectionRequest(BaseModel):
    decision_id: str
    reason: str
    rejected_by: str  # Email of contador


class ApprovalResponse(BaseModel):
    success: bool
    decision_id: str
    status: str
    error: str = ""


class DraftListItem(BaseModel):
    id: str
    draft_id: str
    draft_type: str
    status: str
    reason: str
    payload: dict
    created_at: str
    tenant_id: Optional[str] = None


class DraftListResponse(BaseModel):
    drafts: List[DraftListItem]


@router.get("", response_model=DraftListResponse)
async def list_drafts(
    status: Optional[str] = Query(default=None),
    draft_type: Optional[str] = Query(default=None),
    tenant_id: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    """
    List drafts across all draft types. Defaults to no filtering; pass
    `status=pending_approval` to see only items awaiting review.

    Tenant scoping (approval-queue-tenant-scoping):
    - No resolved scope (authenticated, unwired caller) -> empty list. Never
      Cliente Cero.
    - Contexia operator scope (caller resolves to Cliente Cero) -> unfiltered
      by default, or scoped to the `?tenant_id=` query param if supplied.
    - Normal B2B client scope -> forced to the caller's own tenant, ignoring
      any client-supplied `?tenant_id`.
    """
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        return DraftListResponse(drafts=[])

    effective_tenant_id = tenant_id if scope.all_tenants else scope.tenant_id

    try:
        decisions = await ApprovalQueueService.list_drafts(
            status=status, draft_type=draft_type, tenant_id=effective_tenant_id
        )
        return DraftListResponse(
            drafts=[
                DraftListItem(
                    id=d.id,
                    draft_id=d.draft_id,
                    draft_type=d.draft_type,
                    status=d.status.value,
                    reason=d.reason,
                    payload=d.payload,
                    created_at=d.created_at.isoformat(),
                    tenant_id=d.tenant_id,
                )
                for d in decisions
            ]
        )
    except Exception as e:
        logger.error(f"List drafts endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enqueue", response_model=ApprovalResponse)
async def enqueue_for_approval(
    payload: EnqueueRequest, user: dict = Depends(get_current_user)
):
    """
    Enqueue a draft for approval after Agent Critic validation.

    Tenant scoping (approval-queue-tenant-scoping): the caller's resolved
    tenant scope stamps the enqueued row. No resolved scope -> 404 (never a
    silent Cliente Cero fallback; 404 rather than 403 per
    agent-endpoints-real-tenant-filtering's anti-enumeration policy).

    If Critic validation fails, returns 400 with validation error.
    If validation passes, creates a pending approval decision.
    """
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        raise HTTPException(status_code=404, detail="No tenant resolved for caller")

    try:
        # Convert request to journal entry dict
        journal_entry = {
            "lines": [line.model_dump() for line in payload.lines],
            "memo": payload.memo,
        }

        # Enqueue with Critic validation
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=payload.draft_id,
            draft_type=payload.draft_type,
            journal_entry=journal_entry,
            memo=payload.memo,
            tenant_id=scope.tenant_id,
        )

        if not success:
            logger.warning(f"Enqueue failed for draft {payload.draft_id}: {error}")
            raise HTTPException(status_code=400, detail=error)

        return ApprovalResponse(
            success=True,
            decision_id=decision.id,
            status=decision.status.value,
            error="",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enqueue endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve", response_model=ApprovalResponse)
async def approve_draft(
    request: ApprovalRequest, user: dict = Depends(get_current_user)
):
    """
    Approve a draft. Triggers asynchronous vectorization of the approval decision.

    Tenant scoping (approval-queue-tenant-scoping): a normal client scope
    restricts the approve to that tenant's own rows (cross-tenant decision_id
    returns "not found"); a Contexia operator scope (all_tenants) is
    unrestricted. No resolved scope -> 404 (not 403 — see
    agent-endpoints-real-tenant-filtering).

    Vectorization failure is non-blocking (approval still succeeds).
    """
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        raise HTTPException(status_code=404, detail="No tenant resolved for caller")

    try:
        success, decision, error = await ApprovalQueueService.approve_draft(
            decision_id=request.decision_id,
            approval_reason=request.reason,
            approved_by=request.approved_by,
            tenant_id=None if scope.all_tenants else scope.tenant_id,
        )

        if not success:
            raise HTTPException(status_code=400, detail=error)

        return ApprovalResponse(
            success=True,
            decision_id=decision.id,
            status=decision.status.value,
            error="",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approve endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject", response_model=ApprovalResponse)
async def reject_draft(
    request: RejectionRequest, user: dict = Depends(get_current_user)
):
    """
    Reject a draft. Prevents journal entry from being posted.

    Tenant scoping (approval-queue-tenant-scoping): same policy as
    `POST /approve` — see its docstring.
    """
    scope = resolve_request_tenant_scope(user, get_service_supabase())
    if scope is None:
        raise HTTPException(status_code=404, detail="No tenant resolved for caller")

    try:
        success, decision, error = await ApprovalQueueService.reject_draft(
            decision_id=request.decision_id,
            rejection_reason=request.reason,
            rejected_by=request.rejected_by,
            tenant_id=None if scope.all_tenants else scope.tenant_id,
        )

        if not success:
            raise HTTPException(status_code=400, detail=error)

        return ApprovalResponse(
            success=True,
            decision_id=decision.id,
            status=decision.status.value,
            error="",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reject endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
