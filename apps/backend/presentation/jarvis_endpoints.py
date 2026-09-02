"""Jarvis endpoints — personal Telegram bot + Búnker chat proxy.

Routes:
  POST /api/v1/channels/jarvis/webhook  — Telegram webhook (Fase A)
  POST /api/v1/jarvis/chat              — SSE streaming proxy to Hermes (Fase B)
  GET  /api/v1/jarvis/status            — Hermes health proxy, admin-only
  POST /api/v1/jarvis/brief             — financial context aggregation for morning brief cron
"""

import os
import hmac
import hashlib
import logging
import json
from typing import AsyncGenerator, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.deps import get_current_user
from core.hermes_gateway import resolve_hermes_gateway_url
from core.plan_features import has_feature
from core.supabase_client import get_service_supabase
from core.tenant_context import resolve_request_tenant_scope

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Routers — two prefixes, one file (see design.md D4)
# ---------------------------------------------------------------------------
webhook_router = APIRouter(tags=["jarvis-telegram"])   # prefix: /channels/jarvis
api_router = APIRouter(tags=["jarvis-api"])            # prefix: /jarvis

# ---------------------------------------------------------------------------
# Config — loaded at module level (fail-open: missing tokens skip auth checks
# gracefully so the route can return an explicit 401 rather than crashing)
# ---------------------------------------------------------------------------
_JARVIS_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_JARVIS", "")
_JARVIS_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET_JARVIS", "")
_JARVIS_CHAT_ID = os.getenv("TELEGRAM_JUAN_DAVID_CHAT_ID", "")
_HERMES_BRIDGE_TOKEN = os.getenv("HERMES_BRIDGE_TOKEN", "")

TELEGRAM_SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"
HERMES_CALL_TIMEOUT = 55  # seconds — leaves 5s buffer before Telegram's 60s webhook timeout

# ---------------------------------------------------------------------------
# Pydantic models (mirrors telegram_endpoints.py shapes)
# ---------------------------------------------------------------------------

class _TgUser(BaseModel):
    id: int
    is_bot: bool = False
    first_name: str = ""


class _TgChat(BaseModel):
    id: int
    type: str = "private"


class _TgMessage(BaseModel):
    message_id: int
    date: int
    text: Optional[str] = None
    from_user: Optional[_TgUser] = None
    chat: _TgChat

    class Config:
        populate_by_name = True
        fields = {"from_user": {"alias": "from"}}


class _TgUpdate(BaseModel):
    update_id: int
    message: Optional[_TgMessage] = None


class JarvisChatRequest(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verify_jarvis_webhook_secret(secret_header: Optional[str]) -> bool:
    """Validate X-Telegram-Bot-Api-Secret-Token against TELEGRAM_WEBHOOK_SECRET_JARVIS."""
    if not _JARVIS_WEBHOOK_SECRET:
        logger.warning("TELEGRAM_WEBHOOK_SECRET_JARVIS not set — skipping webhook auth")
        return True
    if not secret_header:
        return False
    return hmac.compare_digest(secret_header, _JARVIS_WEBHOOK_SECRET)


async def _send_jarvis_message(chat_id: int | str, text: str) -> None:
    """Send a message via the Jarvis Telegram bot."""
    if not _JARVIS_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN_JARVIS not set — cannot send message")
        return
    url = TELEGRAM_SEND_URL.format(token=_JARVIS_BOT_TOKEN)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
            if resp.status_code != 200:
                logger.error(f"Telegram sendMessage failed: {resp.status_code} {resp.text[:200]}")
    except Exception as exc:
        logger.error(f"Failed to send Jarvis Telegram message: {exc}")


def _hermes_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if _HERMES_BRIDGE_TOKEN:
        headers["Authorization"] = f"Bearer {_HERMES_BRIDGE_TOKEN}"
    return headers


# ---------------------------------------------------------------------------
# Fase A — Telegram webhook
# ---------------------------------------------------------------------------

@webhook_router.post("/webhook")
async def jarvis_telegram_webhook(request: Request):
    """Receive a Telegram update and proxy it to Hermes, reply to the founder's chat."""
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if not _verify_jarvis_webhook_secret(secret_header):
        # Return 200 OK with no action — Telegram retries on 4xx
        logger.warning("Jarvis webhook: invalid secret token, ignoring update")
        return {"ok": True}

    try:
        body = await request.body()
        raw = json.loads(body.decode("utf-8"))
        update = _TgUpdate(**raw)
    except Exception as exc:
        logger.error(f"Jarvis webhook: failed to parse update: {exc}")
        return {"ok": True}

    msg = update.message
    if not msg or not msg.text:
        return {"ok": True}

    # Allowlist: only respond to the founder's chat
    if _JARVIS_CHAT_ID and str(msg.chat.id) != str(_JARVIS_CHAT_ID):
        logger.warning(f"Jarvis webhook: unknown chat_id={msg.chat.id}, ignoring")
        return {"ok": True}

    user_text = msg.text.strip()
    chat_id = msg.chat.id
    logger.info(f"Jarvis webhook: chat_id={chat_id}, text={user_text[:80]}")

    try:
        gateway_url = await resolve_hermes_gateway_url()
    except RuntimeError as exc:
        logger.error(f"Jarvis: cannot resolve Hermes gateway: {exc}")
        await _send_jarvis_message(chat_id, "⚠️ Hermes no está disponible en este momento.")
        return {"ok": True}

    system_prompt = (
        "You are Jarvis, the personal AI assistant of Juan David, founder of Contexia. "
        "You have full admin context over all tenants and operations. "
        "Be concise, direct, and in the same language as the user's message."
    )

    payload = {
        "message": user_text,
        "system_prompt": system_prompt,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=HERMES_CALL_TIMEOUT) as client:
            resp = await client.post(
                f"{gateway_url}/api/run",
                json=payload,
                headers=_hermes_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            hermes_reply = data.get("response") or data.get("text") or str(data)
    except httpx.TimeoutException:
        logger.warning("Jarvis: Hermes call timed out")
        await _send_jarvis_message(chat_id, "⏳ Tardando más de lo habitual... intenta de nuevo en un momento.")
        return {"ok": True}
    except Exception as exc:
        logger.error(f"Jarvis: Hermes call failed: {exc}")
        await _send_jarvis_message(chat_id, "❌ Error al contactar a Hermes.")
        return {"ok": True}

    await _send_jarvis_message(chat_id, hermes_reply)
    return {"ok": True}


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
