"""LinkedIn organization page normalizer."""

from typing import Any, Dict, Iterable, List


def _iter_items(payload: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for key in ("events", "comments", "posts", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
            return
    yield payload


def normalize_linkedin_sync(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for item in _iter_items(payload):
        text = (
            item.get("commentary")
            or item.get("message")
            or item.get("text")
            or item.get("comment")
            or ""
        )
        text = str(text).strip()
        if not text:
            continue
        actor = item.get("actor") or item.get("author") or item.get("from") or {}
        events.append(
            {
                "channel": "linkedin",
                "account_id": str(
                    item.get("organization")
                    or item.get("organization_id")
                    or payload.get("organization_id")
                    or "linkedin-organization"
                ),
                "source_event_id": str(item.get("id") or item.get("activity") or ""),
                "event_type": str(item.get("event_type") or item.get("type") or "comment"),
                "actor_handle": str(actor.get("localizedName") or actor.get("id") or "linkedin-user"),
                "actor_name": str(actor.get("localizedName") or actor.get("name") or "LinkedIn user"),
                "text": text,
                "raw_payload": item,
            }
        )
    return events

