"""Jarvis endpoints — Búnker chat proxy + brief aggregation.

Routes:
  POST /api/v1/jarvis/chat              — SSE streaming proxy to Hermes (Fase B)
  GET  /api/v1/jarvis/status            — Hermes health proxy, admin-only
  POST /api/v1/jarvis/brief             — financial context aggregation for morning brief cron

The Telegram side of Jarvis (founder's personal chat) is NOT a second bot/webhook
here anymore — D1 (hermes-jarvis-contexia re-scope, 2026-09-13) merged it into
`presentation/telegram_endpoints.py`'s existing Taty webhook: a message from
`TELEGRAM_JUAN_DAVID_CHAT_ID` is routed to Hermes there, before the Taty lookup.
One bot, one token, one webhook. See that module's `_route_to_jarvis`.
"""

import os
import logging
import json
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.deps import get_current_user
from core.hermes_gateway import resolve_hermes_gateway_url
from core.plan_features import has_feature
from core.supabase_client import get_service_supabase
from core.tenant_context import resolve_request_tenant_scope

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router — /jarvis prefix only (the /channels/jarvis webhook router was removed
# by D1; see module docstring)
# ---------------------------------------------------------------------------
api_router = APIRouter(tags=["jarvis-api"])            # prefix: /jarvis

_HERMES_BRIDGE_TOKEN = os.getenv("HERMES_BRIDGE_TOKEN", "")


class JarvisChatRequest(BaseModel):
    message: str


def _hermes_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if _HERMES_BRIDGE_TOKEN:
        headers["Authorization"] = f"Bearer {_HERMES_BRIDGE_TOKEN}"
    return headers


# ---------------------------------------------------------------------------
# Fase A — Brief aggregation (called by Hermes morning cron)
# ---------------------------------------------------------------------------

@api_router.post("/brief")
async def jarvis_brief():
    """Aggregate financial context for the morning brief cron.

    Returns:
      - caja_real: list of cash balances per tenant
      - centinela_alerts: active alerts across all tenants
      - approval_queue: pending items across all tenants

    Manus commercial context is NOT handled here — the Hermes cron script
    calls Manus directly (fail-graceful, 5s timeout). This endpoint owns
    only the financial side.
    """
    supabase = get_service_supabase()
    result: dict = {
        "caja_real": [],
        "centinela_alerts": [],
        "approval_queue": [],
    }

    try:
        rows = supabase.table("erp_journal_entries").select(
            "tenant_id, account_code, balance_cop"
        ).eq("account_code", "1110").eq("is_verified_real", True).execute()
        result["caja_real"] = rows.data or []
    except Exception as exc:
        logger.error(f"Jarvis brief: error fetching caja_real: {exc}")
        raise HTTPException(status_code=503, detail="Financial DB unreachable")

    try:
        alerts = supabase.table("centinela_alerts").select(
            "tenant_id, rule_id, severity, message, created_at"
        ).eq("is_active", True).order("created_at", desc=True).limit(20).execute()
        result["centinela_alerts"] = alerts.data or []
    except Exception as exc:
        logger.error(f"Jarvis brief: error fetching centinela_alerts: {exc}")
        # Non-critical — don't 503 for this

    try:
        queue = supabase.table("approval_queue").select(
            "tenant_id, action_type, payload, created_at"
        ).eq("status", "pending").order("created_at", desc=True).limit(10).execute()
        result["approval_queue"] = queue.data or []
    except Exception as exc:
        logger.error(f"Jarvis brief: error fetching approval_queue: {exc}")
        # Non-critical — don't 503 for this

    return result


# ---------------------------------------------------------------------------
# Fase B — Búnker chat (SSE streaming proxy)
# ---------------------------------------------------------------------------

@api_router.post("/chat")
async def jarvis_chat(body: JarvisChatRequest, user=Depends(get_current_user)):
    """Proxy a chat message to Hermes and stream the response via SSE.

    Gated by the jarvis_chat feature flag (plan_tier growth+).
    """
    supabase = get_service_supabase()
    scope = resolve_request_tenant_scope(user, supabase)
    if scope is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant not resolved")

    # Admin (all_tenants=True) always has access; B2B clients need jarvis_chat feature.
    if not scope.all_tenants:
        try:
            row = supabase.table("tenants").select("plan_tier").eq("id", scope.tenant_id).single().execute()
            plan_tier: str = (row.data or {}).get("plan_tier", "starter")
        except Exception:
            plan_tier = "starter"

        if not has_feature(plan_tier, "jarvis_chat"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "feature_not_available", "feature": "jarvis_chat", "plan_tier": plan_tier},
            )

    try:
        gateway_url = await resolve_hermes_gateway_url()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    payload = {
        "message": body.message,
        "system_prompt": (
            "You are Jarvis, the Contexia AI assistant embedded in the Búnker. "
            "Answer in the same language as the user's message. Be concise and helpful."
        ),
        "stream": True,
    }

    async def _stream_hermes() -> AsyncGenerator[str, None]:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{gateway_url}/api/run",
                    json=payload,
                    headers=_hermes_headers(),
                ) as resp:
                    async for chunk in resp.aiter_text():
                        if chunk:
                            yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as exc:
            logger.error(f"Jarvis chat stream error: {exc}")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        _stream_hermes(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Fase B — Hermes status (admin-only)
# ---------------------------------------------------------------------------

@api_router.get("/status")
async def jarvis_status(user=Depends(get_current_user)):
    """Proxy to Hermes /health. Admin-only (all_tenants scope = Contexia operator)."""
    supabase = get_service_supabase()
    scope = resolve_request_tenant_scope(user, supabase)
    if scope is None or not scope.all_tenants:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    try:
        gateway_url = await resolve_hermes_gateway_url()
    except RuntimeError as exc:
        return {"status": "unreachable", "detail": str(exc)}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{gateway_url}/health", headers=_hermes_headers())
            return {"status": "ok", "gateway_url": gateway_url, "hermes": resp.json()}
    except Exception as exc:
        return {"status": "unreachable", "gateway_url": gateway_url, "detail": str(exc)}
