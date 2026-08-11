"""Durable-inbox poller (change: whatsapp-durable-inbox).

Pulls events the backend's webhook already persisted, mirrors each into Chatwoot for human
visibility, and drives Taty's reply directly. This is what gives Tatiana an inbox again: the
WhatsApp webhook now lands on Railway (taty-channel-consolidation), not on Chatwoot directly, so
without this poller answered messages would never appear here.

Reply generation calls main.process_incoming_message() directly — the exact same single-brain,
bot_off-respecting pipeline every other channel goes through (Telegram, and Chatwoot's own
webhook path for a human-typed message) — rather than duplicating that logic here.

CORRECTED 2026-08-11 (taty-whatsapp-renta-sales-capability, found live): the original design
injected the customer's message into Chatwoot as `message_type: "incoming"` and relied on
Chatwoot firing its own message_created webhook back to this bridge to trigger
process_incoming_message — a loopback that only ever worked against the credential-less
Channel::Api test inbox this bridge used before Stage 5's cutover. Chatwoot's Messages API
rejects a fabricated "incoming" message with a 422 for any inbox with a real provider behind it
(Channel::Whatsapp) — "Incoming messages are only allowed in Api inboxes" — so against the real
inbox, injection always failed, the loopback never fired, and Taty never replied to a single real
customer message. The customer's text is now mirrored as a private note instead (succeeds on a
real inbox, visible to a human, but is NOT a trigger — private messages are explicitly filtered by
this bridge's own /webhook handler, by design, for unrelated reasons), and process_incoming_message
is called directly. bot_off is checked here explicitly (via the conversation's live labels)
because bypassing the webhook handler means bypassing the check that handler used to make.
"""

from __future__ import annotations

import asyncio
import logging

import backend_client
import chatwoot_client
from config import settings

logger = logging.getLogger(__name__)


async def poll_once() -> None:
    """One pull-mirror-reply-acknowledge cycle. Each event is handled independently: one failure
    must not block the others, and must leave that one event unacknowledged so it is redelivered
    rather than lost."""
    events = await backend_client.pull_pending_events()
    if not events:
        return

    # Deferred import: main.py imports this module (inbox_poller) to start the background poll
    # loop, so a module-level `from main import ...` here would be a circular import. Safe as a
    # local import — by the time poll_once() actually runs, main.py's own module body (including
    # the `import inbox_poller` line) has already finished executing.
    from main import process_incoming_message

    for event in events:
        try:
            contact_id = await chatwoot_client.find_or_create_contact(
                event["account_id"], event.get("actor_name")
            )
            conversation_id = await chatwoot_client.find_or_create_conversation(
                contact_id=contact_id, phone=event["account_id"]
            )
            body = event.get("body") or ""

            try:
                await chatwoot_client.create_customer_message_note(conversation_id, body)
            except Exception:
                # Human-visibility mirroring is best-effort — a failure here must not prevent
                # Taty from actually answering the customer.
                logger.exception(
                    "Failed to mirror inbound WhatsApp event %s as a Chatwoot note (non-fatal, "
                    "continuing to reply generation)",
                    event.get("id"),
                )

            labels = await chatwoot_client.get_conversation_labels(conversation_id)
            if settings.PAUSE_LABEL in labels:
                logger.info(
                    "Conversation %s is paused (%s) — skipping automated reply for event %s",
                    conversation_id, settings.PAUSE_LABEL, event.get("id"),
                )
            else:
                await process_incoming_message(
                    conversation_id=conversation_id,
                    content=body,
                    attachments=[],
                    contact_id=contact_id,
                    phone=event["account_id"],
                )
        except Exception:
            logger.exception(
                "Failed to process inbound WhatsApp event %s — leaving unacknowledged for "
                "redelivery",
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
