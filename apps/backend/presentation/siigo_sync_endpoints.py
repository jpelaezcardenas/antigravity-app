"""
Internal Siigo sync endpoint — triggered by hermes-siigo-poller (local cron).

POST /internal/siigo-sync/run
  Auth: INTERNAL_API_KEY header (machine-to-machine, never exposed to clients)
  Body: { "tenant_id": "<uuid>", "days_back": 1, "dry_run": false }

This endpoint is mounted under /internal/* which is NOT proxied through vercel.json
rewrite rules — it is only reachable directly from Railway's internal network or
via the poller running on the same machine as the backend.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

_INTERNAL_API_KEY_VAR = "INTERNAL_API_KEY"


def _verify_internal_key(x_internal_api_key: str | None) -> None:
    expected = os.environ.get(_INTERNAL_API_KEY_VAR, "")
    if not expected:
        # Fail closed: if the key is not configured, reject all requests.
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal API key")


class SiigoSyncRequest(BaseModel):
    tenant_id: str
    days_back: int = 1
    dry_run: bool = False


class SiigoSyncResponse(BaseModel):
    tenant_id: str
    rows_ingested: int
    date_range: str
    errors: list[str]
    dry_run: bool


@router.post("/siigo-sync/run", response_model=SiigoSyncResponse)
async def run_siigo_sync(
    body: SiigoSyncRequest,
    x_internal_api_key: Optional[str] = Header(default=None),
) -> SiigoSyncResponse:
    """
    Pull Siigo journals + invoices for a tenant and ingest them into the Shadow GL.

    Called by hermes-siigo-poller (Windows Task Scheduler, nightly at 2 AM).
    Requires X-Internal-Api-Key header matching the INTERNAL_API_KEY env var.

    is_verified_real is always True here — this is live client data fetched
    directly from the Siigo API with the client's own credentials.
    """
    _verify_internal_key(x_internal_api_key)

    from services.siigo_api_client import SiigoApiClient

    client = SiigoApiClient.for_tenant(body.tenant_id)
    if client is None:
        raise HTTPException(
            status_code=404,
            detail=f"No Siigo credentials configured for tenant {body.tenant_id}",
        )

    if body.dry_run:
        logger.info(f"[dry-run] Siigo sync for tenant {body.tenant_id}, days_back={body.days_back}")
        return SiigoSyncResponse(
            tenant_id=body.tenant_id,
            rows_ingested=0,
            date_range="",
            errors=[],
            dry_run=True,
        )

    logger.info(f"Starting Siigo sync for tenant {body.tenant_id}, days_back={body.days_back}")
    summary = await client.sync_to_shadow_gl(days_back=body.days_back)

    return SiigoSyncResponse(
        tenant_id=body.tenant_id,
        rows_ingested=summary["rows_ingested"],
        date_range=summary["date_range"],
        errors=summary["errors"],
        dry_run=False,
    )
