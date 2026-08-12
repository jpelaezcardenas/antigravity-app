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
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v20.0"

_MD_TABLE_SEPARATOR = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")
_MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*")
_MD_HR = re.compile(r"^\s*[-=*_]{3,}\s*$")
_MD_BOLD_DOUBLE = re.compile(r"\*\*(.+?)\*\*")
_HTML_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_SOURCES_FOOTER = re.compile(
    r"\n{0,2}\**\s*fuentes?\s*\**\s*:.*$", re.IGNORECASE | re.DOTALL
)
_BLANK_RUN = re.compile(r"\n{3,}")


def sanitize_for_whatsapp(text: str) -> str:
    """Strip Markdown/HTML artifacts a real WhatsApp client cannot render.

    Found live 2026-08-12 (taty-whatsapp-renta-sales-capability): Chatwoot's own web UI renders
    GFM (tables, `##` headers, `**bold**`) fine, so a reply looked correct there, but the real
    WhatsApp app on the customer's phone has no Markdown-table/HTML support — it shows the raw
    pipes, dashes, `<br>` tags and double asterisks as literal clutter. The prompt now instructs
    the model to avoid all of this (see taty_service.py's WhatsApp-only closing instructions), but
    since instruction-following isn't 100% reliable (the same gap that made "24/7" get spelled out
    once), this is the safety net applied to every outbound WhatsApp reply regardless of source.

    - `**bold**` -> `*bold*` (WhatsApp's own bold syntax)
    - Markdown table rows/separators and `---`/`===` horizontal rules -> dropped
    - `#`/`##`/... headings -> the `#` markers stripped, text kept
    - `<br>` -> newline
    - A trailing "Fuentes: ..." / "**Fuentes**: ..." block -> dropped entirely
    - 3+ consecutive blank lines -> collapsed to 2
    """
    if not text:
        return text

    text = _SOURCES_FOOTER.sub("", text)
    # A space, not a newline: <br> inside a Markdown table cell is a soft break WITHIN one row —
    # splitting the line there would break the row's pipe count and leave orphan "| ...|" fragments
    # that the table-row detection below (which needs the whole row on one line) can't recognize.
    text = _HTML_BR.sub(" ", text)
    text = _MD_BOLD_DOUBLE.sub(r"*\1*", text)

    kept_lines = []
    for line in text.split("\n"):
        if _MD_TABLE_SEPARATOR.match(line) and "|" in line:
            continue
        if line.count("|") >= 2:
            line = "- " + " ".join(part.strip() for part in line.strip().strip("|").split("|") if part.strip())
        if _MD_HR.match(line):
            continue
        line = _MD_HEADING.sub("", line)
        kept_lines.append(line)

    result = "\n".join(kept_lines)
    result = _BLANK_RUN.sub("\n\n", result)
    return result.strip()


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

                if not text and media:
                    # An image/document sent with a caption carries the sender's actual words in
                    # `caption`, not `text` — found live 2026-08-11 when a forwarded ad image with
                    # a caption produced an empty event and Taty fell back to a generic non-answer.
                    text = (media.get("caption") or "").strip()

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
