"""Durable inbox for inbound WhatsApp Cloud API events (change: whatsapp-durable-inbox).

Meta's webhook is at-least-once with a hard ceiling: it retries a non-200 and then drops the
event permanently — no replay API, no dead-letter queue, no event log. So the consumer has to
supply the durability and the idempotency the platform does not.

The webhook's only job becomes: verify signature -> store here -> 200. The local Chatwoot bridge
then PULLS, which is what lets the local node stay unreachable from the internet (and removes the
Cloudflare-Tunnel / DNS-delegation requirement entirely).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from core.supabase_client import get_service_supabase

logger = logging.getLogger(__name__)

_TABLE = "whatsapp_inbound_events"

# How long a pulled-but-unacknowledged event stays claimed before it is offered again. If the
# local node crashes between pulling and injecting into Chatwoot, this is what gets the customer's
# message redelivered instead of lost.
DEFAULT_CLAIM_TTL_SECONDS = 300
DEFAULT_PULL_LIMIT = 50


def store_inbound_events(events: List[Dict[str, Any]]) -> int:
    """Persist normalized inbound events, deduplicating on Meta's message id.

    Returns the number of events handed to the database (not the number of new rows — the
    database silently ignores conflicts, which is the point).

    Events without a usable Meta message id are SKIPPED, never written with a blank id: the
    column is UNIQUE, so a blank would collide every un-idded message into one row and silently
    discard real customer messages. Dropping one unidentifiable event loudly is strictly better
    than discarding a stream of real ones quietly.
    """
    rows: List[Dict[str, Any]] = []

    for event in events:
        meta_message_id = str(event.get("source_event_id") or "").strip()
        if not meta_message_id:
            logger.warning(
                "Inbound WhatsApp event from %s has no Meta message id — skipped, cannot dedupe",
                event.get("account_id"),
            )
            continue

        rows.append(
            {
                "meta_message_id": meta_message_id,
                "account_id": str(event.get("account_id") or ""),
                "actor_name": event.get("actor_name"),
                "body": event.get("text") or "",
                "media_id": event.get("media_id"),
                "mime_type": event.get("mime_type"),
                "raw_payload": event.get("raw_payload") or {},
            }
        )

    if not rows:
        return 0

    client = get_service_supabase()
    # ON CONFLICT (meta_message_id) DO NOTHING. Deliberately the database's job: two concurrent
    # Meta retries would race any read-then-write check in application code.
    client.table(_TABLE).upsert(
        rows, on_conflict="meta_message_id", ignore_duplicates=True
    ).execute()

    return len(rows)


def pull_pending(
    limit: int = DEFAULT_PULL_LIMIT,
    claim_ttl_seconds: int = DEFAULT_CLAIM_TTL_SECONDS,
) -> List[Dict[str, Any]]:
    """Return unprocessed events that nobody currently holds a live claim on, and claim them.

    Claim-then-acknowledge rather than delete-on-read: a consumer that dies after reading must
    not take the customer's message with it.

    Note: select-then-update is not atomic. That is acceptable here because there is exactly one
    consumer (the local bridge). If a second consumer is ever added, this needs to move into a
    single `UPDATE ... RETURNING` via an RPC with `FOR UPDATE SKIP LOCKED`.
    """
    client = get_service_supabase()
    now = datetime.now(timezone.utc)
    claim_cutoff = (now - timedelta(seconds=claim_ttl_seconds)).isoformat()

    query = client.table(_TABLE).select("*").is_("processed_at", "null")
    # The installed postgrest-py (0.13.2) has no .or_() helper — it was added in a later
    # release. Add the raw "or" query param the same way .filter() does internally
    # (self.params = self.params.add(key, val)), producing PostgREST's documented
    # `or=(cond1,cond2)` syntax, ANDed with the .is_() filter above.
    query.params = query.params.add(
        "or", f"(claimed_at.is.null,claimed_at.lt.{claim_cutoff})"
    )
    result = query.order("created_at").limit(limit).execute()
    events = result.data or []
    if not events:
        return []

    client.table(_TABLE).update({"claimed_at": now.isoformat()}).in_(
        "id", [e["id"] for e in events]
    ).execute()

    return events


def acknowledge(event_ids: List[str]) -> int:
    """Mark events processed. Called only after Chatwoot has accepted the injected message, so a
    failure in between results in redelivery rather than a lost message."""
    if not event_ids:
        return 0

    client = get_service_supabase()
    client.table(_TABLE).update(
        {"processed_at": datetime.now(timezone.utc).isoformat()}
    ).in_("id", event_ids).execute()

    return len(event_ids)


def inbox_health() -> Dict[str, Any]:
    """Backlog depth and the age of the oldest unprocessed event.

    Exists because the failure mode this change introduces is a silent one: when the local node is
    offline, events accumulate correctly and nothing looks broken. A durable queue nobody watches
    is a queue that quietly grows.
    """
    client = get_service_supabase()
    result = (
        client.table(_TABLE)
        .select("created_at", count="exact")
        .is_("processed_at", "null")
        .order("created_at")
        .limit(1)
        .execute()
    )
    rows = result.data or []

    return {
        "pending": result.count or 0,
        "oldest_pending_at": rows[0]["created_at"] if rows else None,
    }
