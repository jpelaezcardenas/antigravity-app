"""
Approval Queue Endpoints

GET  /api/v1/approval-queue - List drafts (filter by status, draft_type)
POST /api/v1/approval-queue/enqueue - Enqueue draft with Critic validation
POST /api/v1/approval-queue/approve - Approve a draft and trigger vectorization
POST /api/v1/approval-queue/reject - Reject a draft
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import logging

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


class DraftListResponse(BaseModel):
    drafts: List[DraftListItem]


@router.get("", response_model=DraftListResponse)
async def list_drafts(
    status: Optional[str] = Query(default=None),
    draft_type: Optional[str] = Query(default=None),
):
    """
    List drafts across all draft types. Defaults to no filtering; pass
    `status=pending_approval` to see only items awaiting review.
    """
    try:
        decisions = await ApprovalQueueService.list_drafts(
            status=status, draft_type=draft_type
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
                )
                for d in decisions
            ]
        )
    except Exception as e:
        logger.error(f"List drafts endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enqueue", response_model=ApprovalResponse)
async def enqueue_for_approval(request: EnqueueRequest):
    """
    Enqueue a draft for approval after Agent Critic validation.

    If Critic validation fails, returns 400 with validation error.
    If validation passes, creates a pending approval decision.
    """
    try:
        # Convert request to journal entry dict
        journal_entry = {
            "lines": [line.model_dump() for line in request.lines],
            "memo": request.memo,
        }

        # Enqueue with Critic validation
        success, decision, error = await ApprovalQueueService.enqueue_draft(
            draft_id=request.draft_id,
            draft_type=request.draft_type,
            journal_entry=journal_entry,
            memo=request.memo,
        )

        if not success:
            logger.warning(f"Enqueue failed for draft {request.draft_id}: {error}")
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
async def approve_draft(request: ApprovalRequest):
    """
    Approve a draft. Triggers asynchronous vectorization of the approval decision.

    Vectorization failure is non-blocking (approval still succeeds).
    """
    try:
        success, decision, error = await ApprovalQueueService.approve_draft(
            decision_id=request.decision_id,
            approval_reason=request.reason,
            approved_by=request.approved_by,
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
async def reject_draft(request: RejectionRequest):
    """
    Reject a draft. Prevents journal entry from being posted.
    """
    try:
        success, decision, error = await ApprovalQueueService.reject_draft(
            decision_id=request.decision_id,
            rejection_reason=request.reason,
            rejected_by=request.rejected_by,
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
