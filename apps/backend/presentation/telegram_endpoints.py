"""
Telegram channel webhook for Taty.

This endpoint keeps Telegram as a thin transport layer. The conversation
logic stays in TatyAgentService so WhatsApp can reuse it later.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
import requests

from application.taty_agent_service import TatyAgentRequest, taty_agent_service
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    message = update.get("message") or update.get("edited_message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")

    if not text or not chat_id:
        return {"ok": True, "skipped": True, "reason": "no_text_message"}

    company_id = settings.TATY_TELEGRAM_COMPANY_ID
    conversation_id = f"telegram:{chat_id}"
    user_id = str(sender.get("id") or chat_id)

    try:
        response = taty_agent_service.ask(
            TatyAgentRequest(
                company_id=company_id,
                question=text,
                channel="telegram",
                conversation_id=conversation_id,
                user_id=user_id,
            )
        )
    except Exception:
        logger.exception("Telegram Taty request failed")
        fallback_text = (
            "Taty tuvo un problema procesando tu pregunta. "
            "Intenta de nuevo en un momento o escribe al equipo de Contexia."
        )
        delivered = _send_telegram_message(chat_id, fallback_text)
        return {"ok": True, "delivered": delivered, "error": "taty_failed"}

    delivered = _send_telegram_message(chat_id, _format_telegram_answer(response.answer))
    return {
        "ok": True,
        "delivered": delivered,
        "conversation_id": conversation_id,
        "latency_ms": response.latency_ms,
        "requires_human_review": response.requires_human_review,
    }


def _send_telegram_message(chat_id: int | str, text: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured; skipping Telegram send")
        return False

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:3900],
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=payload, timeout=8)
    if response.ok:
        return True

    logger.warning("Telegram send failed status=%s body=%s", response.status_code, response.text[:300])
    return False


def _format_telegram_answer(answer: str) -> str:
    # Telegram plain text keeps the MVP robust across clients.
    return answer.replace("\r\n", "\n").strip()
