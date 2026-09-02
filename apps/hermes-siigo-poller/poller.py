"""Siigo sync poller — one tick.

Calls GET /internal/siigo-sync/eligible-tenants on the backend to discover which tenants
have SIIGO_* credentials configured (determined server-side from Railway env vars), then
calls POST /internal/siigo-sync/run for each tenant.

Alternatively (simpler for now): reads SIIGO_ELIGIBLE_TENANTS from the local .env
(comma-separated UUIDs) and fires one sync request per tenant. The backend
authenticates credentials via Railway env vars independently.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _sync_headers() -> dict[str, str]:
    return {
        "X-Internal-Api-Key": settings.INTERNAL_API_KEY,
        "Content-Type": "application/json",
    }


def _sync_tenant(client: httpx.Client, tenant_id: str) -> dict[str, Any]:
    """POST /internal/siigo-sync/run for one tenant. Returns the response dict."""
    url = f"{settings.RAILWAY_BACKEND_URL}/internal/siigo-sync/run"
    payload = {
        "tenant_id": tenant_id,
        "days_back": settings.SIIGO_SYNC_DAYS_BACK,
        "dry_run": settings.DRY_RUN,
    }
    try:
        resp = client.post(url, json=payload, headers=_sync_headers(), timeout=settings.HTTP_TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        logger.info(
            f"Tenant {tenant_id}: {data.get('rows_ingested', 0)} rows ingested "
            f"({data.get('date_range', '')})"
            + (f" | errors: {data.get('errors')}" if data.get("errors") else "")
        )
        return data
    except httpx.HTTPStatusError as exc:
        logger.error(f"Tenant {tenant_id} sync failed — HTTP {exc.response.status_code}: {exc.response.text[:200]}")
        return {"tenant_id": tenant_id, "rows_ingested": 0, "errors": [str(exc)]}
    except Exception as exc:
        logger.error(f"Tenant {tenant_id} sync failed — {exc}")
        return {"tenant_id": tenant_id, "rows_ingested": 0, "errors": [str(exc)]}


def _get_eligible_tenants() -> list[str]:
    """Read tenant UUIDs from SIIGO_ELIGIBLE_TENANTS env var (set in .env, never Railway)."""
    import os
    raw = os.environ.get("SIIGO_ELIGIBLE_TENANTS", "")
    return [t.strip() for t in raw.split(",") if t.strip()]


def run_tick() -> dict[str, Any]:
    """Run one sync tick: iterate all eligible tenants and sync each."""
    if not settings.INTERNAL_API_KEY:
        logger.error("INTERNAL_API_KEY is not set — poller is inert. Set it in .env")
        return {"skipped": True, "reason": "INTERNAL_API_KEY not configured"}

    tenants = _get_eligible_tenants()
    if not tenants:
        logger.warning(
            "No eligible tenants found. Set SIIGO_ELIGIBLE_TENANTS=<uuid1>,<uuid2> in .env"
        )
        return {"skipped": True, "reason": "no tenants configured"}

    logger.info(f"Starting Siigo sync tick for {len(tenants)} tenant(s) (dry_run={settings.DRY_RUN})")

    results: list[dict[str, Any]] = []
    with httpx.Client() as client:
        for tenant_id in tenants:
            result = _sync_tenant(client, tenant_id)
            results.append(result)

    total_rows = sum(r.get("rows_ingested", 0) for r in results)
    total_errors = sum(len(r.get("errors", [])) for r in results)
    logger.info(f"Tick complete: {total_rows} rows ingested, {total_errors} errors across {len(tenants)} tenants")

    return {
        "tenants": len(tenants),
        "rows_ingested": total_rows,
        "errors": total_errors,
        "results": results,
    }
