"""Chatwoot <-> Contexia (Taty) bridge.

Thin, stateless transport layer: Chatwoot event -> filter / HITL check -> CRM intake ->
backend Taty reply -> Chatwoot reply. No business logic is duplicated from the Contexia
backend — lead lifecycle stays owned by crm_service.py, and reply generation is owned by
services/taty_lead_router.py (taty-channel-consolidation).

Previously this module called Hermes directly for a free-text chat completion: a second reply
brain that bypassed intent classification, Wompi payment links, payment verification and KB
grounding. Hermes is still the inference provider, reached through the backend's anonymized LLM
path; `hermes_client` survives here only as a liveness probe that makes a wrong-profile gateway
visible in logs.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, status

import backend_client
import chatwoot_client
import hermes_client
import inbox_poller
from config import settings
from schemas import ChatwootWebhookPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Starts the durable-inbox poller as a background task when enabled (whatsapp-durable-inbox).
    Off by default (INBOX_POLLER_ENABLED) so the bridge keeps working standalone before it is
    configured — e.g. before WHATSAPP_APP_SECRET exists in Railway (design.md 4.4)."""
    poller_task = None
    if settings.INBOX_POLLER_ENABLED:
        poller_task = asyncio.create_task(inbox_poller.run_forever())

    yield

    if poller_task is not None:
        poller_task.cancel()


app = FastAPI(title="Chatwoot-Hermes Bridge", lifespan=_lifespan)

AUDIO_FALLBACK_REPLY = (
    "Por ahora te leo mejor por texto - me puedes escribir tu mensaje? 🙂"
)
HANDOVER_FALLBACK_REPLY = (
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

    intake_result = await backend_client.whatsapp_intake(phone) if phone else None
    if intake_result and intake_result.get("is_new") and contact_id is not None:
        await chatwoot_client.set_contact_attributes(
            contact_id, {"tipo_lead": "b2c_whatsapp", "estado": "nuevo"}
        )

    # taty-channel-consolidation: without a lead we do NOT answer. The previous behaviour fell
    # through to a raw Hermes completion, which meant an unidentified contact could still get an
    # ungrounded tax answer with no lead context, no Wompi state and no KB grounding. Handing
    # over to a human in Chatwoot is the correct degraded mode.
    lead_id = (intake_result or {}).get("lead_id")
    if not lead_id:
        logger.warning(
            "No lead_id for conversation %s (phone=%s) — handing over to a human",
            conversation_id,
            phone,
        )
        await chatwoot_client.send_reply(conversation_id, HANDOVER_FALLBACK_REPLY)
        return

    reply_text = await backend_client.taty_reply(lead_id, content)
    if reply_text is None:
        reply_text = HANDOVER_FALLBACK_REPLY

    await chatwoot_client.send_reply(conversation_id, reply_text)


@app.get("/")
async def health() -> dict:
    models = await hermes_client.check_models()
    logger.info("Hermes /v1/models liveness check at startup/health: %s", models)
    return {"status": "ok", "service": "chatwoot-hermes-bridge", "hermes_models": models}
