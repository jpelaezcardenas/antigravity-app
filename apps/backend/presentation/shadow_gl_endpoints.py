"""
Shadow GL Endpoints

POST /api/v1/shadow-gl/dian-xml/ingest - Manually ingest a DIAN UBL 2.1 XML document
POST /api/v1/shadow-gl/siigo-csv/ingest - Manually ingest a Siigo journal CSV export
"""

import csv as _csv_module
import io
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, UploadFile, File
from pydantic import BaseModel

from core.deps import get_current_user
from core.hermes_client import HermesClient, HermesClientError
from core.supabase_client import get_supabase
from core.tenant_context import resolve_request_tenant_scope
from services.shadow_gl_service import (
    ingest_dian_xml,
    ingest_siigo_csv,
    _update_approval_queue,
    _persist_approved_entry,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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


def _resolve_tenant_from_scope(user: dict) -> str:
    """Resolve the tenant_id for an ingestion call using the caller's JWT scope.

    Operators (Contexia staff) get Cliente Cero. B2B clients get their own tenant.
    Raises 403 if the scope cannot be resolved (unauthenticated with AUTH_ENFORCED=True).
    """
    supabase = get_supabase()
    scope = resolve_request_tenant_scope(user, supabase)
    if scope is None:
        raise HTTPException(status_code=403, detail="Tenant not resolved — valid authentication required")
    return scope.tenant_id


@router.post("/dian-xml/ingest", response_model=DianXmlIngestResponse)
async def ingest_dian_xml_endpoint(
    request: Request,
    is_verified_real: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    Manually ingest a DIAN UBL 2.1 XML document (invoice, credit note, or
    debit note). Accepts the raw XML as the request body.

    Idempotent on CUFE: re-ingesting the same document does not duplicate it.

    Pass ?is_verified_real=true when uploading a genuine DIAN export (vs. a
    fixture/test document) — defaults to false so nothing is silently
    treated as real (shadow-gl-data-integrity-flag).
    """
    raw_xml = (await request.body()).decode("utf-8")

    if not raw_xml.strip():
        raise HTTPException(status_code=400, detail="Request body must contain XML")

    tenant_id = _resolve_tenant_from_scope(user)

    success, document, error = await ingest_dian_xml(tenant_id, raw_xml, is_verified_real)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return DianXmlIngestResponse(
        success=True,
        cufe=document["cufe"],
        document_type=document["document_type"],
        error="",
    )


@router.post("/siigo-csv/ingest", response_model=SiigoCSVIngestResponse)
async def ingest_siigo_csv_endpoint(
    request: Request,
    is_verified_real: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    Manually ingest a Siigo journal CSV export (debit/credit double-entry format).
    Accepts the raw CSV as the request body.

    Idempotent on (tenant_id, external_reference_id, entry_date): re-ingesting
    the same batch does not duplicate entries.

    Pass ?is_verified_real=true when uploading a genuine Siigo export (vs. a
    fixture/test file) — defaults to false so nothing is silently treated as
    real (shadow-gl-data-integrity-flag).

    Returns 200 with row_count and date_range on success, or 400 with error message
    if CSV is malformed or accounting entries are imbalanced.
    """
    csv_text = (await request.body()).decode("utf-8")

    if not csv_text.strip():
        raise HTTPException(status_code=400, detail="Request body must contain CSV")

    tenant_id = _resolve_tenant_from_scope(user)

    success, summary, error = await ingest_siigo_csv(tenant_id, csv_text, is_verified_real)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return SiigoCSVIngestResponse(
        success=True,
        row_count=summary["row_count"],
        date_range=summary["date_range"],
        error="",
    )


@router.post("/siigo-csv/upload", response_model=SiigoCSVIngestResponse)
async def upload_siigo_csv_endpoint(
    file: UploadFile = File(...),
    is_verified_real: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    Upload a Siigo journal CSV export via multipart form data (PWA file uploader).

    Creates a batch record in ingestion_batches, validates the CSV, and injects into
    erp_journal_entries.

    Idempotent on (tenant_id, external_reference_id, entry_date): duplicate rows
    are skipped.

    Pass ?is_verified_real=true when uploading a genuine Siigo export (vs. a
    fixture/test file) — defaults to false so nothing is silently treated as
    real (shadow-gl-data-integrity-flag).

    Returns 200 with row_count and date_range on success, or 400 with error message
    if file upload, parsing, or DB insertion fails.
    """
    tenant_id = _resolve_tenant_from_scope(user)
    supabase = get_supabase()

    # Create batch record
    batch_id = str(uuid.uuid4())
    file_content = await file.read()
    csv_text = file_content.decode("utf-8")
    file_size = len(file_content)

    batch_data = {
        "id": batch_id,
        "tenant_id": tenant_id,
        "data_source": "siigo_csv",
        "file_name": file.filename or "upload.csv",
        "file_size_bytes": file_size,
        "row_count": 0,
        "status": "pending",
        "error_count": 0,
        "error_summary": None,
        "uploaded_at": datetime.now(tz=None).isoformat(),
    }

    try:
        supabase.table("ingestion_batches").insert(batch_data).execute()
        logger.info(f"Created ingestion_batch {batch_id}")
    except Exception as exc:
        logger.error(f"Failed to create ingestion_batch: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create batch record")

    # Parse and ingest CSV
    success, summary, error = await ingest_siigo_csv(tenant_id, csv_text, is_verified_real)

    # Update batch record
    try:
        if success:
            update_data = {
                "status": "completed",
                "row_count": summary.get("row_count", 0),
                "processed_at": datetime.now(tz=None).isoformat(),
                "completed_at": datetime.now(tz=None).isoformat(),
            }
        else:
            update_data = {
                "status": "error",
                "error_count": 1,
                "error_summary": {"parsing_error": error},
                "processed_at": datetime.now(tz=None).isoformat(),
            }

        supabase.table("ingestion_batches").update(update_data).eq("id", batch_id).execute()
        logger.info(f"Updated ingestion_batch {batch_id} to {update_data['status']}")
    except Exception as exc:
        logger.error(f"Failed to update ingestion_batch {batch_id}: {exc}")

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return SiigoCSVIngestResponse(
        success=True,
        row_count=summary.get("row_count", 0),
        date_range=summary.get("date_range", ""),
        error="",
    )


@router.post("/upload", response_model=SiigoCSVIngestResponse)
async def upload_any_format_endpoint(
    file: UploadFile = File(...),
    is_verified_real: bool = False,
    user: dict = Depends(get_current_user),
):
    """
    Upload any supported file format (CSV, XLSX, XLS, XML, PDF) for ingestion into the Shadow GL.

    Accepts Siigo CSV exports, Excel workbooks, DIAN UBL 2.1 XML files, and PDF invoices
    (electronic with embedded XML, or non-electronic processed via LLM extraction).

    Idempotent on (tenant_id, external_reference_id, entry_date): duplicate rows are skipped.
    Pass ?is_verified_real=true for genuine client data (defaults to false for test uploads).
    """
    from services.multi_format_parser import parse_any_to_siigo_rows, UnsupportedFormatError

    tenant_id = _resolve_tenant_from_scope(user)
    supabase = get_supabase()

    batch_id = str(uuid.uuid4())
    file_content = await file.read()
    file_size = len(file_content)
    filename = file.filename or "upload"

    batch_data = {
        "id": batch_id,
        "tenant_id": tenant_id,
        "data_source": "multi_format_upload",
        "file_name": filename,
        "file_size_bytes": file_size,
        "row_count": 0,
        "status": "pending",
        "error_count": 0,
        "error_summary": None,
        "uploaded_at": datetime.now(tz=None).isoformat(),
    }

    try:
        supabase.table("ingestion_batches").insert(batch_data).execute()
    except Exception as exc:
        logger.error(f"Failed to create ingestion_batch: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create batch record")

    # Parse the file into Shadow GL rows
    try:
        rows = await parse_any_to_siigo_rows(filename, file_content)
    except UnsupportedFormatError as exc:
        supabase.table("ingestion_batches").update(
            {"status": "error", "error_count": 1, "error_summary": {"error": str(exc)}}
        ).eq("id", batch_id).execute()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        supabase.table("ingestion_batches").update(
            {"status": "error", "error_count": 1, "error_summary": {"parsing_error": str(exc)}}
        ).eq("id", batch_id).execute()
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")

    # Reconstruct CSV text from parsed rows and delegate to ingest_siigo_csv
    # (reuses its idempotency guarantee on (tenant_id, external_reference_id, entry_date))
    success, summary, error = await ingest_siigo_csv(tenant_id, _rows_to_csv_text(rows), is_verified_real)

    try:
        if success:
            supabase.table("ingestion_batches").update({
                "status": "completed",
                "row_count": summary.get("row_count", 0),
                "processed_at": datetime.now(tz=None).isoformat(),
                "completed_at": datetime.now(tz=None).isoformat(),
            }).eq("id", batch_id).execute()
        else:
            supabase.table("ingestion_batches").update({
                "status": "error",
                "error_count": 1,
                "error_summary": {"ingestion_error": error},
                "processed_at": datetime.now(tz=None).isoformat(),
            }).eq("id", batch_id).execute()
    except Exception as exc:
        logger.error(f"Failed to update ingestion_batch {batch_id}: {exc}")

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return SiigoCSVIngestResponse(
        success=True,
        row_count=summary.get("row_count", 0),
        date_range=summary.get("date_range", ""),
        error="",
    )


def _rows_to_csv_text(rows: list[dict]) -> str:
    """Convert parsed rows back to Siigo CSV format for ingest_siigo_csv() reuse."""
    import csv as _csv
    buf = io.StringIO()
    if not rows:
        return ""
    writer = _csv.DictWriter(
        buf,
        fieldnames=["Fecha", "Referencia Externa", "Código de Cuenta", "Descripción", "Débito", "Crédito"],
        extrasaction="ignore",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({
            "Fecha": row.get("fecha", ""),
            "Referencia Externa": row.get("referencia_externa", ""),
            "Código de Cuenta": row.get("codigo_cuenta", ""),
            "Descripción": row.get("descripcion", ""),
            "Débito": row.get("debito_cents", 0) / 100 if row.get("debito_cents") else 0,
            "Crédito": row.get("credito_cents", 0) / 100 if row.get("credito_cents") else 0,
        })
    return buf.getvalue()


@router.websocket("/approval-callback")
async def approval_callback_endpoint(websocket: WebSocket) -> None:
    """
    Receive approval decisions from Hermes Desktop (Phase 6).

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
