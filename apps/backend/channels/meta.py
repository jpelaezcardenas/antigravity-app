"""Meta webhook normalizer for Facebook and Instagram."""

from typing import Any, Dict, List


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_meta_webhook(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize supported Meta webhook shapes without scraping."""
    events: List[Dict[str, Any]] = []
    object_name = str(payload.get("object") or "").lower()
    default_channel = "instagram" if "instagram" in object_name else "facebook"

    for entry in payload.get("entry", []) or []:
        account_id = str(entry.get("id") or entry.get("page_id") or default_channel)
        channel = str(entry.get("channel") or entry.get("platform") or default_channel).lower()
        if channel not in {"facebook", "instagram"}:
            channel = default_channel

        for message in entry.get("messaging", []) or []:
            msg = message.get("message") or {}
            postback = message.get("postback") or {}
            text = _first_text(msg.get("text"), postback.get("title"), postback.get("payload"))
            if not text:
                continue
            sender = message.get("sender") or {}
            events.append(
                {
                    "channel": channel,
                    "account_id": account_id,
                    "source_event_id": str(msg.get("mid") or message.get("timestamp") or ""),
                    "event_type": "message",
                    "actor_handle": str(sender.get("id") or "meta-user"),
                    "actor_name": str(sender.get("name") or sender.get("id") or "Meta user"),
                    "text": text,
                    "raw_payload": message,
                }
            )

        for change in entry.get("changes", []) or []:
            field = str(change.get("field") or "change").lower()
            value = change.get("value") or {}
            text = _first_text(
                value.get("message"),
                value.get("text"),
                value.get("caption"),
                value.get("comment"),
                value.get("body"),
            )
            if not text:
                continue
            sender = value.get("from") or value.get("sender") or {}
            event_type = "comment" if "comment" in field or "feed" in field else "message"
            events.append(
                {
                    "channel": channel,
                    "account_id": account_id,
                    "source_event_id": str(
                        value.get("comment_id")
                        or value.get("id")
                        or value.get("mid")
                        or change.get("field")
                        or ""
                    ),
                    "event_type": event_type,
                    "actor_handle": str(sender.get("username") or sender.get("id") or "meta-user"),
                    "actor_name": str(sender.get("name") or sender.get("username") or "Meta user"),
                    "text": text,
                    "raw_payload": change,
                }
            )

    return events

