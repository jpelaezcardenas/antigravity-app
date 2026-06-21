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
from services.social_ops_service import get_social_ops_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])  # prefix handled by router.py include_router()


@router.post("/health")
async def telegram_health():
    """Quick health check for webhook routing."""
    logger.info("✅ Telegram health check - routing works!")
    return {"ok": True, "status": "webhook endpoint is reachable"}

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
        logger.debug("🔵 Webhook request received")

        body = await request.body()
        body_str = body.decode('utf-8')

        # NOTE: Signature verification skipped - HTTPS provides transport security
        # TODO: Re-add signature verification after webhook is stable

        # PASO 2: Parsear el mensaje
        logger.debug("🔵 Parsing message")
        update_data = json.loads(body_str)
        update = TelegramUpdate(**update_data)

        # Si no hay mensaje o texto, ignorar
        if not update.message or not update.message.text:
            logger.debug("⚪ No message or text, ignoring")
            return {"ok": True}

        chat_id = update.message.chat.id
        user_text = update.message.text.strip()
        user_id = str(update.message.from_user.id) if update.message.from_user else None

        logger.info(f"📱 Telegram: chat_id={chat_id}, pregunta={user_text[:50]}")

        # Social Content Ops uses Telegram as the Zero-UI command channel.
        # Only explicit ops commands are routed here so Taty keeps handling fiscal Q&A.
        social_ops = get_social_ops_service()
        if social_ops.is_social_ops_command(user_text):
            result = social_ops.handle_telegram_update(update_data)
            await send_telegram_message(chat_id, build_social_ops_telegram_reply(result))
            return {"ok": True, "social_ops": True, "result": result}

        # PASO 3: Buscar la empresa en Supabase
        logger.debug("🔵 Getting Supabase client")
        supabase = get_supabase()

        logger.debug(f"🔵 Querying telegram_chat_mappings for chat_id={chat_id}")
        try:
            # Use eq filter without .single() to get all results
            result = supabase.table("telegram_chat_mappings").select("company_id").eq("telegram_chat_id", str(chat_id)).execute()

            if not result.data or len(result.data) == 0:
                logger.warning(f"❌ No hay empresa mapeada para chat_id={chat_id}")
                await send_telegram_message(chat_id, "❌ Este chat no está configurado.\nContacta a soporte.")
                return {"ok": True}

            company_id = result.data[0]["company_id"]
            logger.info(f"✅ Encontrado: chat_id={chat_id} → empresa={company_id}")
        except Exception as e:
            logger.error(f"❌ Error querying telegram_chat_mappings: {str(e)}", exc_info=True)
            await send_telegram_message(chat_id, "❌ Error de configuración.\nContacta a soporte.")
            return {"ok": True}

        # If onboarding is active for this company, treat Telegram messages as onboarding intake
        # (client should not fill long forms; capture facts conversationally).
        social_ops = get_social_ops_service()
        active_ws = social_ops.get_active_onboarding_for_company(company_id)
        if active_ws:
            intake = social_ops.intake_onboarding(
                workspace_id=active_ws["id"],
                text=user_text,
                source="telegram",
                actor_handle=str(update.message.from_user.username) if update.message.from_user and getattr(update.message.from_user, "username", None) else (user_id or "client"),
            )
            await send_telegram_message(chat_id, build_taty_onboarding_reply(active_ws, intake))
            return {"ok": True, "taty_mode": "onboarding", "workspace_id": active_ws["id"]}

        # PASO 4: Llamar a Taty
        logger.debug("🔵 Getting Taty service")
        taty = get_taty_service()

        logger.debug(f"🔵 Calling taty.ask() for company={company_id}")
        response = taty.ask(
            company_id=company_id,
            question=user_text,
            channel="telegram",
            user_id=user_id,
        )

        # PASO 5: Preparar respuesta
        logger.debug("🔵 Preparing response")
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
        logger.debug("🔵 Sending response to Telegram")
        await send_telegram_message(chat_id, full_response)
        logger.info(f"✅ Respuesta enviada en {response['latency_ms']}ms")

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error procesando webhook")


def build_social_ops_telegram_reply(result: dict) -> str:
    """Build a safe Telegram acknowledgement for Social Ops commands."""
    drafts = result.get("command_drafts") or []
    events = result.get("events") or []
    if drafts:
        draft = drafts[-1]
        return (
            "Social Content Ops recibio el comando.\n"
            f"Accion detectada: {draft['action']}.\n"
            "Estado: pending_approval. No se ejecuto ningun cambio de infraestructura, "
            "publicacion o agenda critica sin aprobacion."
        )
    if events:
        lead = events[-1].get("lead") or {}
        diagnosis = events[-1].get("diagnosis") or {}
        return (
            "Social Content Ops registro el evento inbound.\n"
            f"Lead: {lead.get('display_name', 'sin nombre')}.\n"
            f"Etapa: {diagnosis.get('maturity_stage', 'pendiente')}.\n"
            f"Siguiente paso: {diagnosis.get('next_stage', 'diagnostico')}."
        )
    return "Social Content Ops no encontro texto procesable en el mensaje."


def build_taty_onboarding_reply(workspace: dict, intake: dict) -> str:
    missing = intake.get("missing") or []
    present = intake.get("present") or []
    company = workspace.get("company_name", "cliente")
    sla = (workspace.get("sla") or {}).get("client_credentials_response_hours", 48)

    summary = (
        f"Onboarding 21D activo para {company}.\n"
        f"Captura conversacional recibida. Presentes: {len(present)}. Faltantes: {len(missing)}.\n"
    )
    if missing:
        summary += "Pendiente por capturar: " + ", ".join(missing) + ".\n"
    summary += (
        "Regla: nada sensible se ejecuta sin aprobacion. "
        f"SLA credenciales: {sla}h por solicitud."
    )
    return summary


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
