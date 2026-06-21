"""
Shadow GL Endpoints

POST /api/v1/shadow-gl/dian-xml/ingest - Manually ingest a DIAN UBL 2.1 XML document
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.shadow_gl_service import ingest_dian_xml

logger = logging.getLogger(__name__)

router = APIRouter()

CLIENTE_CERO_TENANT_ID = "__cliente_cero__"


class DianXmlIngestResponse(BaseModel):
    success: bool
    cufe: str = ""
    document_type: str = ""
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
