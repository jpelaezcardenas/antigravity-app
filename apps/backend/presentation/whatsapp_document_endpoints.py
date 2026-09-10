"""Internal inbound document endpoint (taty-document-collection-wiring, Task 3).

POST /internal/whatsapp/document
  Auth: INTERNAL_API_KEY header (machine-to-machine, same pattern as voice_endpoints,
        ingest_file_endpoints, siigo_sync_endpoints)
  Body: {lead_id, data_url, mime_type}

Why this endpoint exists
-------------------------
Chatwoot's inbound WhatsApp attachment payload never carries a Graph API media_id — only a
Chatwoot-hosted `data_url` (see services/taty_lead_router.py::route_lead_document's docstring,
Task 2). The local bridge (apps/chatwoot-bridge, Task 4) resolves the lead_id and the attachment's
data_url, then posts them here rather than reaching directly into services/taty_lead_router.py —
same boundary the voice-note flow already draws: the local bridge talks to Railway only through an
/internal/* route authenticated by a key that fails closed, mirroring
presentation/voice_endpoints.py.

This endpoint owns no download or gating logic itself. It authenticates the caller and forwards to
route_lead_document(data_url=...), which already owns: the never-throw download contract
(download_chatwoot_attachment, Task 1), the LISTOS_CONTADORA stage gate, and the sequential
RUT-then-extractos bookkeeping.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from services.taty_lead_router import route_lead_document

logger = logging.getLogger(__name__)

router = APIRouter()

_INTERNAL_API_KEY_VAR = "INTERNAL_API_KEY"


def _verify_internal_key(x_internal_api_key: Optional[str]) -> None:
    expected = os.environ.get(_INTERNAL_API_KEY_VAR, "")
    if not expected:
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


class WhatsappDocumentRequest(BaseModel):
    lead_id: str
    data_url: str
    mime_type: str = "application/octet-stream"


class WhatsappDocumentResponse(BaseModel):
    processed: bool


@router.post("/whatsapp/document", response_model=WhatsappDocumentResponse)
async def send_whatsapp_document_endpoint(
    payload: WhatsappDocumentRequest,
    x_internal_api_key: Optional[str] = Header(default=None),
) -> WhatsappDocumentResponse:
    """Forward a Chatwoot-hosted attachment to route_lead_document's data_url path.

    Auth is checked before anything else, same stance as send_voice_note_endpoint: an
    unauthenticated caller cannot probe lead state or trigger a download.

    `processed: False` is a normal, expected outcome (wrong stage, both documents already
    collected, or the download failed) — not an error. Returned as 200, not raised, matching
    route_lead_document's own never-throw contract.
    """
    _verify_internal_key(x_internal_api_key)

    result = await route_lead_document(
        payload.lead_id,
        mime_type=payload.mime_type,
        data_url=payload.data_url,
    )

    return WhatsappDocumentResponse(processed=bool(result.get("processed")))
