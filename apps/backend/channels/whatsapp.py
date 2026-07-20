"""WhatsApp Cloud API channel (taty-whatsapp-sales-router, Change D).

Inbound normalizer mirrors channels/telegram.py's shape and defensive .get()-everywhere style.
Outbound sender mirrors presentation/telegram_endpoints.py's send_telegram_message pattern
(httpx.AsyncClient POST). No real WhatsApp Business number/token exists yet — send_whatsapp_message
returns False (rather than raising or calling out with empty credentials) whenever WHATSAPP_TOKEN /
WHATSAPP_PHONE_NUMBER_ID are unset.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"


def normalize_whatsapp_webhook(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize a WhatsApp Cloud API webhook payload into the common Social Ops/channel event
    shape (channel, account_id, source_event_id, actor_handle, actor_name, text, raw_payload).
    Defensive throughout — a malformed or non-text (e.g. status/delivery-receipt) payload returns
    an empty list rather than raising."""
    events: List[Dict[str, Any]] = []

    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            messages = value.get("messages") or []
            if not messages:
                continue

            contacts = value.get("contacts") or []
            contacts_by_wa_id = {c.get("wa_id"): c for c in contacts if c.get("wa_id")}

            for message in messages:
                text = (message.get("text") or {}).get("body", "").strip()
                message_type = message.get("type")
                media = message.get(message_type) if message_type in ("document", "image") else None

                if not text and not media:
                    continue

                from_phone = message.get("from") or "unknown"
                contact = contacts_by_wa_id.get(from_phone, {})
                actor_name = (contact.get("profile") or {}).get("name") or from_phone

                event = {
                    "channel": "whatsapp",
                    "account_id": str(from_phone),
                    "source_event_id": str(message.get("id") or ""),
                    "event_type": "message",
                    "actor_handle": str(from_phone),
                    "actor_name": actor_name,
                    "text": text,
                    "raw_payload": payload,
                }
                if media:
                    event["media_id"] = media.get("id")
                    event["mime_type"] = media.get("mime_type")

                events.append(event)

    return events


async def send_whatsapp_message(to: str, text: str) -> bool:
    """Send an outbound WhatsApp message via the Graph API. Returns False (logs a clear
    "not configured" message) if WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID are unset — never makes a
    network call with empty credentials, since no real WhatsApp number/token exists yet."""
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    if not token or not phone_number_id:
        logger.warning("send_whatsapp_message: WHATSAPP_TOKEN/WHATSAPP_PHONE_NUMBER_ID not configured")
        return False

    url = f"{GRAPH_API_BASE}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, json=payload, headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code != 200:
                logger.error("WhatsApp API error: %s", resp.status_code)
                return False
            return True
    except Exception as e:
        logger.error("Failed to send WhatsApp message: %s", str(e))
        return False


async def download_whatsapp_media(media_id: str) -> Optional[Dict[str, Any]]:
    """Downloads a WhatsApp media object (document/image) via the 2-step Graph API flow
    (taty-document-collection, Change I): fetch the temporary download URL from media_id, then
    download the bytes. Returns {"content": bytes, "mime_type": str} or None if unconfigured/
    failed — mirrors send_whatsapp_message's never-call-out-with-empty-credentials pattern."""
    token = os.getenv("WHATSAPP_TOKEN")
    if not token:
        logger.warning("download_whatsapp_media: WHATSAPP_TOKEN not configured")
        return None

    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient() as client:
            metadata_resp = await client.get(
                f"{GRAPH_API_BASE}/{media_id}", headers=headers
            )
            if metadata_resp.status_code != 200:
                logger.error("WhatsApp media metadata fetch failed: %s", metadata_resp.status_code)
                return None

            metadata = metadata_resp.json()
            download_url = metadata.get("url")
            mime_type = metadata.get("mime_type")
            if not download_url:
                logger.error("WhatsApp media metadata missing 'url'")
                return None

            file_resp = await client.get(download_url, headers=headers)
            if file_resp.status_code != 200:
                logger.error("WhatsApp media download failed: %s", file_resp.status_code)
                return None

            return {"content": file_resp.content, "mime_type": mime_type}
    except Exception as e:
        logger.error("Failed to download WhatsApp media: %s", str(e))
        return None
