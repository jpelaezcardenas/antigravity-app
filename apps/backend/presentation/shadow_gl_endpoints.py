"""
Shadow GL Endpoints

POST /api/v1/shadow-gl/dian-xml/ingest - Manually ingest a DIAN UBL 2.1 XML document
POST /api/v1/shadow-gl/siigo-csv/ingest - Manually ingest a Siigo journal CSV export
"""

import json
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from core.hermes_client import HermesClient, HermesClientError
from services.shadow_gl_service import (
    ingest_dian_xml,
    ingest_siigo_csv,
    _update_approval_queue,
    _persist_approved_entry,
)

logger = logging.getLogger(__name__)

router = APIRouter()

CLIENTE_CERO_TENANT_ID = "__cliente_cero__"


class DianXmlIngestResponse(BaseModel):
    success: bool
    cufe: str = ""
    document_type: str = ""
    error: str = ""


class SiigoCSVIngestResponse(BaseModel):
    success: bool
    row_count: int = 0
    date_range: str = ""
    error: str = ""


async def _resolve_tenant_id() -> str:
    """
    Resolve the tenant for this ingestion call.

    Multi-tenant routing (per-caller tenant resolution) isn't wired yet --
    every agent endpoint currently operates against Cliente Cero only.
    """
    from core.supabase_client import get_supabase

    supabase = get_supabase()
    result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    return result.data["id"]


@router.post("/dian-xml/ingest", response_model=DianXmlIngestResponse)
async def ingest_dian_xml_endpoint(request: Request):
    """
    Manually ingest a DIAN UBL 2.1 XML document (invoice, credit note, or
    debit note). Accepts the raw XML as the request body.

    Idempotent on CUFE: re-ingesting the same document does not duplicate it.
    """
    raw_xml = (await request.body()).decode("utf-8")

    if not raw_xml.strip():
        raise HTTPException(status_code=400, detail="Request body must contain XML")

    tenant_id = await _resolve_tenant_id()

    success, document, error = await ingest_dian_xml(tenant_id, raw_xml)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return DianXmlIngestResponse(
        success=True,
        cufe=document["cufe"],
        document_type=document["document_type"],
        error="",
    )


@router.post("/siigo-csv/ingest", response_model=SiigoCSVIngestResponse)
async def ingest_siigo_csv_endpoint(request: Request):
    """
    Manually ingest a Siigo journal CSV export (debit/credit double-entry format).
    Accepts the raw CSV as the request body.

    Idempotent on (tenant_id, external_reference_id, entry_date): re-ingesting
    the same batch does not duplicate entries.

    Returns 200 with row_count and date_range on success, or 400 with error message
    if CSV is malformed or accounting entries are imbalanced.
    """
    csv_text = (await request.body()).decode("utf-8")

    if not csv_text.strip():
        raise HTTPException(status_code=400, detail="Request body must contain CSV")

    tenant_id = await _resolve_tenant_id()

    success, summary, error = await ingest_siigo_csv(tenant_id, csv_text)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return SiigoCSVIngestResponse(
        success=True,
        row_count=summary["row_count"],
        date_range=summary["date_range"],
        error="",
    )


@router.websocket("/approval-callback")
async def approval_callback_endpoint(websocket: WebSocket) -> None:
    """
    Receive approval decisions from Hermes Workspace (Phase 6).

    Hermes sends approval_decision messages with:
    - approval_queue_id: which entry was approved/rejected
    - status: "approved" | "rejected"
    - reviewer_id: who made the decision
    - reason: why
    - decided_at: timestamp

    This endpoint updates approval_queue.status and triggers persistence if approved.
    """
    await websocket.accept()
    logger.info(f"Approval callback connected: {websocket.client}")

    try:
        while True:
            message_text = await websocket.receive_text()
            try:
                message = json.loads(message_text)
            except json.JSONDecodeError as exc:
                logger.error(f"Invalid JSON from Hermes: {exc}")
                continue

            if message.get("type") != "approval_decision":
                logger.debug(f"Ignoring message type: {message.get('type')}")
                continue

            # Extract decision
            queue_id = message.get("approval_queue_id")
            status = message.get("status")  # "approved" | "rejected"
            reviewer_id = message.get("reviewer_id")
            reason = message.get("reason", "")
            decided_at = message.get("decided_at")

            if not all([queue_id, status]):
                logger.warning(f"Incomplete approval_decision: {message}")
                continue

            logger.info(f"Approval decision: {queue_id} → {status}")

            # Update approval_queue status
            updated = await _update_approval_queue(
                queue_id=queue_id,
                status=status,
                reviewer_id=reviewer_id,
                reason=reason,
                reviewed_at=decided_at,
            )

            if not updated:
                logger.error(f"Failed to update approval_queue {queue_id}")

            # If approved, persist the entry (Phase 6 Stage 7-9)
            if status == "approved":
                from core.supabase_client import get_supabase

                supabase = get_supabase()
                queue = (
                    supabase.table("approval_queue")
                    .select("*")
                    .eq("id", queue_id)
                    .single()
                    .execute()
                )
                tenant_id = queue.data.get("tenant_id")
                success, error = await _persist_approved_entry(queue_id, tenant_id)
                if success:
                    logger.info(f"Successfully persisted entry from approval_queue {queue_id}")
                else:
                    logger.error(f"Failed to persist entry from approval_queue {queue_id}: {error}")

            # Send ACK back to Hermes
            ack = {
                "type": "ack",
                "approval_queue_id": queue_id,
                "status": "processed",
            }
            try:
                await websocket.send_text(json.dumps(ack))
                logger.debug(f"Sent ACK for {queue_id}")
            except Exception as exc:
                logger.warning(f"Failed to send ACK: {exc}")

    except WebSocketDisconnect:
        logger.info(f"Approval callback disconnected: {websocket.client}")
    except Exception as exc:
        logger.error(f"Approval callback error: {exc}")
        await websocket.close(code=1011)
