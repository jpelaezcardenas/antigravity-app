"""Chatwoot <-> Hermes (Taty) bridge.

Thin, stateless transport layer (design.md Goals): Chatwoot event -> filter /
HITL check -> history -> Hermes chat-completion -> Chatwoot reply. No
business logic is duplicated from the Contexia backend — lead lifecycle
stays owned by crm_service.py / social_ops_endpoints.py (design.md decision 5).
"""

from __future__ import annotations

import logging

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, status

import backend_client
import chatwoot_client
import hermes_client
from config import settings
from schemas import ChatwootWebhookPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chatwoot-Hermes Bridge")

AUDIO_FALLBACK_REPLY = (
    "Por ahora te leo mejor por texto - me puedes escribir tu mensaje? 🙂"
)
HERMES_FALLBACK_REPLY = (
    "Disculpa, tuve un problema para responderte en este momento. "
    "Un miembro del equipo va a revisar tu mensaje pronto."
)


def _check_webhook_token(token_param: str | None, token_header: str | None) -> None:
    provided = token_param or token_header
    if not settings.WEBHOOK_TOKEN or provided != settings.WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook token"
        )


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    token: str | None = None,
    x_webhook_token: str | None = Header(default=None, alias="X-Webhook-Token"),
) -> dict:
    # Token check happens before any event parsing (spec requirement).
    _check_webhook_token(token, x_webhook_token)

    body = await request.json()
    payload = ChatwootWebhookPayload(**body)

    if payload.event != "message_created":
        return {"status": "skipped"}
    if payload.message_type != "incoming":
        return {"status": "skipped"}
    if payload.private:
        return {"status": "skipped"}

    if settings.PAUSE_LABEL in payload.labels():
        return {"status": "paused", "reason": f"{settings.PAUSE_LABEL} tag active"}

    background_tasks.add_task(
        process_incoming_message,
        conversation_id=payload.conversation_id(),
        content=payload.content or "",
        attachments=[a.model_dump() for a in payload.attachments],
        contact_id=payload.contact_id(),
        phone=payload.contact_phone(),
    )
    return {"status": "processing_started"}


async def process_incoming_message(
    conversation_id: int,
    content: str,
    attachments: list[dict],
    contact_id: int | None,
    phone: str | None,
) -> None:
    """Background pipeline for a processable incoming WhatsApp message."""
    if any(a.get("file_type") == "audio" for a in attachments):
        await chatwoot_client.send_reply(conversation_id, AUDIO_FALLBACK_REPLY)
        return

    intake_result = None
    if phone:
        intake_result = await backend_client.whatsapp_intake(phone)
        # Graceful degradation (design.md decision 7): a failed intake call
        # never blocks the reply — just skip the new-lead side effects below.
        if intake_result and intake_result.get("is_new") and contact_id is not None:
            await chatwoot_client.set_contact_attributes(
                contact_id, {"tipo_lead": "b2c_whatsapp", "estado": "nuevo"}
            )

    history = await chatwoot_client.get_recent_messages(conversation_id)
    reply_text = await hermes_client.invoke_chat_completion(history, content)
    if reply_text is None:
        reply_text = HERMES_FALLBACK_REPLY

    await chatwoot_client.send_reply(conversation_id, reply_text)


@app.get("/")
async def health() -> dict:
    models = await hermes_client.check_models()
    logger.info("Hermes /v1/models liveness check at startup/health: %s", models)
    return {"status": "ok", "service": "chatwoot-hermes-bridge", "hermes_models": models}
