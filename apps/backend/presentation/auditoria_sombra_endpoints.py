"""
Auditoría Sombra endpoints (FASE 4, Slice 3).

Exposes PDF audit report generation with HITL gating:
- POST /report (audience=internal): returns download URL immediately
- POST /report (audience=external): enqueues audit_report_signoff, withholds URL
- GET /report-status/{approval_queue_id}: query post-approval status
"""

import logging
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.auditoria_sombra_service import (
    request_audit_report,
    get_audit_report_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auditoria-sombra"])


class ReportRequest(BaseModel):
    """Request body for audit report generation."""

    tenant_id: str
    date_start: str  # YYYY-MM-DD
    date_end: str  # YYYY-MM-DD
    audience: Literal["internal", "external"] = "internal"


class ReportResponse(BaseModel):
    """Audit report response."""

    report_id: str
    download_url: Optional[str] = None
    signoff_required: bool
    approval_queue_id: Optional[str] = None
    status: str
    pdf_size_bytes: int


class ReportStatusResponse(BaseModel):
    """Report status query response."""

    status: str
    download_url: Optional[str] = None
    approval_queue_id: str


@router.post("/report", response_model=ReportResponse)
async def create_audit_report(request: ReportRequest) -> ReportResponse:
    """
    Generate an audit report.

    Internal audience: immediate download URL.
    External audience: enqueues audit_report_signoff approval, URL withheld until approved.
    """
    try:
        result = await request_audit_report(
            tenant_id=request.tenant_id,
            date_start=request.date_start,
            date_end=request.date_end,
            audience=request.audience,
        )
        return ReportResponse(**result)
    except Exception as e:
        logger.error(f"Auditoria.create_audit_report failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Audit report generation failed: {e}")


@router.get("/report-status/{approval_queue_id}", response_model=ReportStatusResponse)
async def get_report_status(approval_queue_id: str) -> ReportStatusResponse:
    """
    Get the current status of an external audit report awaiting signoff.

    Status values:
    - pending_signoff: awaiting Entidad A approval
    - available: approved, download URL returned
    - rejected: signoff rejected, URL inaccessible
    """
    try:
        result = await get_audit_report_status(approval_queue_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Audit report request not found")
        return ReportStatusResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auditoria.get_report_status failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status query failed: {e}")
