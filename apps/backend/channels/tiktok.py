"""TikTok webhook normalizer for capability-gated inbound events."""

from typing import Any, Dict, Iterable, List


def _iter_items(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for key in ("events", "data", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return
    yield payload


def normalize_tiktok_webhook(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for item in _iter_items(payload):
        text = (
            item.get("comment_text")
            or item.get("text")
            or item.get("caption")
            or item.get("message")
            or ""
        )
        text = str(text).strip()
        if not text:
            continue
        actor = item.get("user") or item.get("author") or {}
        events.append(
            {
                "channel": "tiktok",
                "account_id": str(item.get("account_id") or item.get("open_id") or "tiktok"),
                "source_event_id": str(
                    item.get("event_id")
                    or item.get("comment_id")
                    or item.get("video_id")
                    or item.get("id")
                    or ""
                ),
                "event_type": str(item.get("event_type") or item.get("type") or "comment"),
                "actor_handle": str(actor.get("username") or actor.get("open_id") or "tiktok-user"),
                "actor_name": str(actor.get("display_name") or actor.get("username") or "TikTok user"),
                "text": text,
                "raw_payload": item,
            }
        )
    return events

