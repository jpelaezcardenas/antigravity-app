"""
Internal file ingestion endpoint — triggered by hermes-gmail-poller.

POST /internal/ingest/file
  Auth: INTERNAL_API_KEY header (machine-to-machine, same pattern as siigo_sync_endpoints)
  Body: multipart/form-data
    file: UploadFile  — the attachment (CSV, XLSX, XLS, XML, PDF)
    tenant_id: str    — target tenant UUID (resolved by poller from gmail_sender_map)
    is_verified_real: bool = true (email attachments are real client data)

The endpoint delegates to parse_any_to_siigo_rows() (Track 4 shared library)
then to ingest_siigo_csv() for idempotent Shadow GL insertion.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

_INTERNAL_API_KEY_VAR = "INTERNAL_API_KEY"


def _verify_internal_key(x_internal_api_key: str | None) -> None:
    expected = os.environ.get(_INTERNAL_API_KEY_VAR, "")
    if not expected:
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


class IngestFileResponse(BaseModel):
    success: bool
    tenant_id: str
    filename: str
    row_count: int
    date_range: str
    error: str = ""


@router.post("/ingest/file", response_model=IngestFileResponse)
async def ingest_file_endpoint(
    file: UploadFile = File(...),
    tenant_id: str = Form(...),
    is_verified_real: bool = Form(default=True),
    x_internal_api_key: Optional[str] = Header(default=None),
) -> IngestFileResponse:
    """
    Ingest an email attachment into the Shadow GL for a specific tenant.

    Called by hermes-gmail-poller after it downloads an invoice/CSV attachment
    from Taty's Gmail inbox and resolves the sender's tenant via gmail_sender_map.

    Supports: CSV (Siigo), XLSX/XLS (Excel), XML (DIAN UBL 2.1), PDF (with embedded XML
    or via LLM extraction). Delegates to parse_any_to_siigo_rows() from Track 4.

    is_verified_real defaults to True — email attachments from clients are real data.
    """
    _verify_internal_key(x_internal_api_key)

    from services.multi_format_parser import parse_any_to_siigo_rows, UnsupportedFormatError
    from services.shadow_gl_service import ingest_siigo_csv
    from presentation.shadow_gl_endpoints import _rows_to_csv_text

    filename = file.filename or "attachment"
    file_content = await file.read()

    logger.info(f"Ingesting {filename} ({len(file_content)} bytes) for tenant {tenant_id}")

    # Parse the file into Shadow GL rows
    try:
        rows = await parse_any_to_siigo_rows(filename, file_content)
    except UnsupportedFormatError as exc:
        logger.warning(f"Unsupported format for {filename}: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"Parse failed for {filename}: {exc}")
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")

    if not rows:
        return IngestFileResponse(
            success=True,
            tenant_id=tenant_id,
            filename=filename,
            row_count=0,
            date_range="",
            error="File parsed but contained no rows",
        )

    # Ingest via existing idempotent service
    csv_text = _rows_to_csv_text(rows)
    success, summary, error = await ingest_siigo_csv(tenant_id, csv_text, is_verified_real)

    if not success:
        raise HTTPException(status_code=400, detail=error)

    return IngestFileResponse(
        success=True,
        tenant_id=tenant_id,
        filename=filename,
        row_count=summary.get("row_count", 0),
        date_range=summary.get("date_range", ""),
    )
