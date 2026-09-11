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

import audio_converter
import backend_client
import chatwoot_client
import hermes_client
import inbox_poller
import voicebox_client
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
DOCUMENT_ACK_REPLY = "Recibimos tu documento, gracias. Seguimos con el proceso 🙂"

# chatwoot-auto-tagging: maps Taty's existing classification output (taty_lead_router.py) onto
# the 16 Chatwoot custom attributes provisioned in chatwoot-mcp-and-attributes. Only covers what
# Taty already classifies today — no new classification logic here. "unknown" intent is
# deliberately absent from these maps so a low-signal message never overwrites a prior tag.
_INTENT_TO_INTENCION = {
    "sales_interest": "ventas",
    "payment_confirmation": "cobranza",
}
_INTENT_TO_SERVICIO_INTERES = {
    "sales_interest": "renta",
    # whatsapp-b2b-lead-bridge: "creacion_empresa" confirmed live against the Chatwoot instance
    # (GET /api/v1/accounts/{id}/custom_attribute_definitions, 2026-09-09) as one of two real
    # dropdown options for servicio_interes alongside "CFO" — this is the best semantic match for
    # a company-formation/continuous-operations signal, not the only value that exists on the
    # attribute (see design.md Decision 3 and the implementer report for the alternative).
    "business_interest": "creacion_empresa",
}
_INTENT_TO_SIGUIENTE_ACCION = {
    "sales_interest": "Enviar link de pago",
    "payment_confirmation": "Verificar estado de pago",
}


def _confidence_to_prioridad(confidence: float) -> str:
    if confidence >= 0.8:
        return "alta"
    if confidence >= 0.6:
        return "media"
    return "baja"


async def _auto_tag_chatwoot(
    conversation_id: int,
    contact_id: int | None,
    taty_result: dict,
) -> None:
    """Fire-and-forget: tag the Chatwoot conversation/contact from Taty's classification.
    Never raises — a tagging failure must never surface to the customer or block the reply
    already sent by process_incoming_message."""
    try:
        intent = taty_result.get("intent", "unknown")
        confidence = taty_result.get("confidence", 0.0)
        persona_fields = taty_result.get("persona_fields") or {}

        conversation_attrs: dict = {"prioridad": _confidence_to_prioridad(confidence)}
        if intent in _INTENT_TO_INTENCION:
            conversation_attrs["intencion"] = _INTENT_TO_INTENCION[intent]
        if intent in _INTENT_TO_SIGUIENTE_ACCION:
            conversation_attrs["siguiente_accion"] = _INTENT_TO_SIGUIENTE_ACCION[intent]
        await chatwoot_client.set_conversation_attributes(conversation_id, conversation_attrs)

        if contact_id is not None:
            contact_attrs: dict = {}
            if intent in _INTENT_TO_SERVICIO_INTERES:
                contact_attrs["servicio_interes"] = _INTENT_TO_SERVICIO_INTERES[intent]
            # whatsapp-b2b-lead-bridge design.md Decision 2/3: a business_interest signal takes
            # precedence over the persona_natural/regimen_simple derivation below — "SAS"
            # confirmed live against the same Chatwoot custom_attribute_definitions call above.
            if intent == "business_interest":
                contact_attrs["tipo_contribuyente"] = "SAS"
            elif "es_asalariado" in persona_fields:
                contact_attrs["tipo_contribuyente"] = (
                    "persona_natural" if persona_fields["es_asalariado"] else "regimen_simple"
                )
            if contact_attrs:
                await chatwoot_client.set_contact_attributes(contact_id, contact_attrs)
    except Exception:
        logger.exception(
            "auto_tag_chatwoot failed for conversation %s (non-fatal)", conversation_id
        )


async def _send_voice_reply(lead_id: str, reply_text: str) -> None:
    """Fire-and-forget: synthesise `reply_text` locally and hand the audio to the backend.

    Never raises — same contract and for the same reason as _auto_tag_chatwoot above. By the time
    this runs the text reply has already been delivered to the customer's phone and mirrored into
    Chatwoot, so a voice failure must not surface to the customer or disturb anything that already
    succeeded. Voice is additive; it can only ever add audio, never remove or delay a reply.

    Synthesis and encoding both happen on this machine: the model, the cloned voice profile and the
    customer's text never leave it. Only the finished OGG bytes cross to the backend, which is the
    only side that can reach Meta's Graph API (voicebox-local-voice-adoption, design.md Decision 1).
    """
    try:
        wav = await voicebox_client.synthesize(reply_text)
        if not wav:
            return

        ogg = audio_converter.wav_to_ogg_opus(wav)
        if not ogg:
            return

        await backend_client.send_voice_note(lead_id, reply_text, ogg)
    except Exception:
        logger.exception("voice reply failed for lead %s (non-fatal)", lead_id)


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

    # taty-document-collection-wiring: an image/file attachment with a resolved lead is a
    # candidate RUT/extractos document (sequential collection owned by route_lead_document on the
    # backend, gated on LISTOS_CONTADORA). `processed: True` means the backend already stored it,
    # so we ack privately here and skip the normal Taty text reply below. `processed: False` (or a
    # failed call, treated the same — see backend_client.submit_whatsapp_document) is deliberately
    # NOT silence: it falls through to the normal Taty reply so the lead still gets a helpful
    # answer instead of nothing when the document arrives at the wrong stage, both documents are
    # already collected, or the download itself failed.
    doc_attachments = [
        a
        for a in attachments
        if a.get("file_type") in ("image", "file") and (a.get("data_url") or a.get("media_id"))
    ]
    if doc_attachments:
        attachment = doc_attachments[0]
        if attachment.get("data_url"):
            doc_result = await backend_client.submit_whatsapp_document(
                lead_id, attachment["data_url"], attachment["file_type"]
            )
        else:
            # Bug found 2026-09-11 (task 6b): the durable-inbox poller (the only path live in
            # production since taty-channel-consolidation) forwards Meta's media_id, never a
            # Chatwoot data_url — this attachment shape must be routed too, or every real inbound
            # document is silently dropped. No bridge-side download needed: the Graph API is
            # reachable from Railway, unlike Chatwoot's localhost-hosted data_url.
            doc_result = await backend_client.submit_whatsapp_document(
                lead_id, media_id=attachment["media_id"], mime_type=attachment["file_type"]
            )
        if doc_result and doc_result.get("processed"):
            await chatwoot_client.send_reply(conversation_id, DOCUMENT_ACK_REPLY, private=True)
            return

    taty_result = await backend_client.taty_reply(lead_id, content)
    if taty_result is None:
        reply_text = HANDOVER_FALLBACK_REPLY
    else:
        reply_text = taty_result.get("reply") or HANDOVER_FALLBACK_REPLY
        # chatwoot-auto-tagging: fire-and-forget so a Chatwoot API failure never blocks or
        # delays the reply already computed above.
        asyncio.create_task(_auto_tag_chatwoot(conversation_id, contact_id, taty_result))

    # The backend already delivered this exact reply to the customer's phone directly via Meta's
    # Graph API (taty_reply now sends deliver=True — see backend_client.taty_reply for why Chatwoot
    # cannot do the delivery itself). Posting it here as a *private note* mirrors it for the human
    # operator without a second, failing delivery attempt: Chatwoot believes the 24h window is
    # closed (it never saw a real inbound, only the private-note mirror), so an outgoing message
    # would just surface a red "Error al enviar" even though the phone already received it.
    await chatwoot_client.send_reply(conversation_id, reply_text, private=True)

    # voicebox-local-voice-adoption: optionally ALSO send the reply as a voice note. Strictly
    # additive — the text above has already gone out and been mirrored, and nothing below can
    # change that.
    #
    # `voice_allowed` is computed by the backend (services/voice_safety.py) and already folds in
    # the backend's own VOICE_ENABLED, so this never synthesises audio the voice-note endpoint
    # would reject. Fire-and-forget, exactly like _auto_tag_chatwoot: synthesis takes seconds on a
    # GPU and minutes on a CPU, and the customer must not wait for it.
    if settings.VOICE_ENABLED and (taty_result or {}).get("voice_allowed"):
        asyncio.create_task(_send_voice_reply(lead_id, reply_text))


@app.get("/")
async def health() -> dict:
    models = await hermes_client.check_models()
    logger.info("Hermes /v1/models liveness check at startup/health: %s", models)
    return {"status": "ok", "service": "chatwoot-hermes-bridge", "hermes_models": models}
