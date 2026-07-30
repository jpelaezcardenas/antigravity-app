"""Durable-inbox poller (change: whatsapp-durable-inbox).

Pulls events the backend's webhook already persisted, injects each into Chatwoot as an incoming
message, and acknowledges only after Chatwoot accepts it. This is what gives Tatiana an inbox
again: the WhatsApp webhook now lands on Railway (taty-channel-consolidation), not on Chatwoot
directly, so without this poller answered messages would never appear here.

Deliberately does NOT call backend_client.taty_reply. Injecting the customer's message into
Chatwoot causes Chatwoot to fire its own existing webhook back to this bridge
(main.py::process_incoming_message), which is what actually drives the reply — through the same
single Taty brain and the same bot_off HITL check every other channel already goes through.
Calling taty_reply here too would re-implement that filtering, which is exactly the second-brain
mistake taty-channel-consolidation removed.
"""

from __future__ import annotations

import asyncio
import logging

import backend_client
import chatwoot_client
from config import settings

logger = logging.getLogger(__name__)


async def poll_once() -> None:
    """One pull-inject-acknowledge cycle. Each event is handled independently: one failing
    injection must not block acknowledgement of the others, and must leave that one event
    unacknowledged so it is redelivered rather than lost."""
    events = await backend_client.pull_pending_events()
    if not events:
        return

    for event in events:
        try:
            contact_id = await chatwoot_client.find_or_create_contact(
                event["account_id"], event.get("actor_name")
            )
            conversation_id = await chatwoot_client.find_or_create_conversation(
                contact_id=contact_id, phone=event["account_id"]
            )
            await chatwoot_client.create_incoming_message(conversation_id, event.get("body") or "")
        except Exception:
            logger.exception(
                "Failed to inject inbound WhatsApp event %s into Chatwoot — leaving "
                "unacknowledged for redelivery",
                event.get("id"),
            )
            continue

        await backend_client.acknowledge_events([event["id"]])


async def run_forever() -> None:
    """The bridge's optional background loop (design.md 4.4 — off by default via
    INBOX_POLLER_ENABLED, so the bridge still runs standalone before this is configured)."""
    logger.info(
        "Starting durable-inbox poller (interval=%ss)", settings.INBOX_POLL_INTERVAL_SECONDS
    )
    while True:
        try:
            await poll_once()
        except Exception:
            logger.exception("Poll cycle failed — will retry next tick")
        await asyncio.sleep(settings.INBOX_POLL_INTERVAL_SECONDS)
