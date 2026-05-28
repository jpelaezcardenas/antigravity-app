"""Telegram normalizer for Social Content Ops."""

from typing import Any, Dict, List


def normalize_telegram_update(update: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize a Telegram webhook update into Social Ops events."""
    message = update.get("message") or update.get("edited_message") or {}
    text = (message.get("text") or message.get("caption") or "").strip()
    if not text:
        return []

    chat = message.get("chat") or {}
    actor = message.get("from") or {}
    actor_id = actor.get("id") or chat.get("id") or "unknown"
    actor_handle = actor.get("username") or str(actor_id)
    actor_name = " ".join(
        part for part in [actor.get("first_name"), actor.get("last_name")] if part
    ) or actor_handle

    return [
        {
            "channel": "telegram",
            "account_id": str(chat.get("id") or "telegram"),
            "source_event_id": str(update.get("update_id") or message.get("message_id") or ""),
            "event_type": "command" if text.startswith("/") else "message",
            "actor_handle": actor_handle,
            "actor_name": actor_name,
            "text": text,
            "raw_payload": update,
        }
    ]

