"""
Shadow GL Endpoints

POST /api/v1/shadow-gl/dian-xml/ingest - Manually ingest a DIAN UBL 2.1 XML document
POST /api/v1/shadow-gl/siigo-csv/ingest - Manually ingest a Siigo journal CSV export
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.shadow_gl_service import ingest_dian_xml, ingest_siigo_csv

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
