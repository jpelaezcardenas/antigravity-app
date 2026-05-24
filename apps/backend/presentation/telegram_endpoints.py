"""
Telegram webhook handler para Taty Contadora.
Recibe mensajes de Telegram, busca la empresa, llama a Taty, y envía respuesta.
"""

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
import logging
import hmac
import hashlib
from typing import Optional
import os
import json
import httpx

from services.taty_service import get_taty_service
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])  # prefix handled by router.py include_router()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "taty-secret-key")


class TelegramUser(BaseModel):
    id: int
    is_bot: bool
    first_name: str


class TelegramChat(BaseModel):
    id: int
    type: str


class TelegramMessage(BaseModel):
    message_id: int
    date: int
    text: str
    from_user: Optional[TelegramUser] = None
    chat: TelegramChat


class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[TelegramMessage] = None


def verify_telegram_signature(request_body: str, signature: str) -> bool:
    """Verifica que el mensaje viene realmente de Telegram."""
    expected_signature = hmac.new(
        TELEGRAM_WEBHOOK_SECRET.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Recibe mensajes de Telegram y los procesa con Taty.

    Flujo:
    1. Verifica que el mensaje es real (firma de Telegram)
    2. Extrae el texto y el chat_id
    3. Busca qué empresa es ese chat en Supabase
    4. Llama a Taty con la pregunta
    5. Envía la respuesta de vuelta a Telegram
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8')

        # PASO 1: Verificar firma de Telegram
        signature = request.headers.get("X-Telegram-Bot-API-Secret-Header")
        if not signature or not verify_telegram_signature(body_str, signature):
            logger.warning("❌ Firma de Telegram inválida")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

        # PASO 2: Parsear el mensaje
        update_data = json.loads(body_str)
        update = TelegramUpdate(**update_data)

        # Si no hay mensaje o texto, ignorar
        if not update.message or not update.message.text:
            return {"ok": True}

        chat_id = update.message.chat.id
        user_text = update.message.text.strip()
        user_id = str(update.message.from_user.id) if update.message.from_user else None

        logger.info(f"📱 Telegram: chat_id={chat_id}, pregunta={user_text[:50]}")

        # PASO 3: Buscar la empresa en Supabase
        supabase = get_supabase()
        try:
            result = supabase.table("telegram_chat_mappings").select("company_id").eq("telegram_chat_id", chat_id).single().execute()
            company_id = result.data["company_id"]
            logger.info(f"✅ Encontrado: chat_id={chat_id} → empresa={company_id}")
        except Exception as e:
            logger.warning(f"❌ No hay empresa mapeada para chat_id={chat_id}")
            await send_telegram_message(chat_id, "❌ Este chat no está configurado.\nContacta a soporte.")
            return {"ok": True}

        # PASO 4: Llamar a Taty
        taty = get_taty_service()
        response = taty.ask(
            company_id=company_id,
            question=user_text,
            channel="telegram",
            user_id=user_id,
        )

        # PASO 5: Preparar respuesta
        answer = response.get("answer", "Error procesando pregunta")

        citations_text = ""
        if response.get("citations"):
            citations_text = "\n\n📚 **Fuentes:**\n"
            for cite in response["citations"]:
                citations_text += f"• {cite['source']}\n"

        escalation = ""
        if response.get("requires_human_review"):
            escalation = "\n\n⚠️ *Esta pregunta requiere revisión de un CFO*"

        full_response = f"{answer}{citations_text}{escalation}"

        # PASO 6: Enviar respuesta a Telegram
        await send_telegram_message(chat_id, full_response)
        logger.info(f"✅ Respuesta enviada en {response['latency_ms']}ms")

        return {"ok": True}

    except Exception as e:
        logger.error(f"❌ Error en webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error procesando webhook")


async def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje a través de la API de Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error(f"❌ Error de Telegram API: {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ No se pudo enviar mensaje: {str(e)}")
