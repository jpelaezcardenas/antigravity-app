"""Tests for the durable-inbox poller (change: whatsapp-durable-inbox).

CORRECTED 2026-08-11 (taty-whatsapp-renta-sales-capability, found live): the poller used to inject
the customer's message as `message_type: "incoming"` and rely on Chatwoot's own webhook looping
back to this bridge to trigger the reply. That loopback only ever worked against the
credential-less Channel::Api test inbox — Chatwoot's Messages API rejects a fabricated "incoming"
message with a 422 for any real-provider inbox (Channel::Whatsapp), so against the real inbox,
Taty never replied to a single real customer message. The poller now mirrors the customer's text
as a private note (visibility only, not a trigger) and calls main.process_incoming_message()
directly, checking the bot_off label itself first since it no longer goes through main.py's
webhook handler (which used to do that check).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


def _event(event_id="e1", account_id="573001234567", body="hola", actor_name="Maria"):
    return {"id": event_id, "account_id": account_id, "body": body, "actor_name": actor_name}


class TestPollOnce:
    @pytest.mark.asyncio
    async def test_mirrors_customer_message_as_private_note(self):
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ), patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock(return_value=55)
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client,
            "create_customer_message_note",
            new=AsyncMock(),
        ) as mock_note, patch.object(
            inbox_poller.chatwoot_client, "get_conversation_labels", new=AsyncMock(return_value=[])
        ), patch("main.process_incoming_message", new=AsyncMock()):
            await inbox_poller.poll_once()

        mock_note.assert_awaited_once_with(42, "hola")

    @pytest.mark.asyncio
    async def test_calls_process_incoming_message_directly(self):
        """The core fix: the poller now drives the reply itself instead of waiting on a Chatwoot
        webhook loopback that cannot happen against a real (non-Api) inbox."""
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ), patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock(return_value=55)
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client, "create_customer_message_note", new=AsyncMock()
        ), patch.object(
            inbox_poller.chatwoot_client, "get_conversation_labels", new=AsyncMock(return_value=[])
        ), patch("main.process_incoming_message", new=AsyncMock()) as mock_process:
            await inbox_poller.poll_once()

        mock_process.assert_awaited_once_with(
            conversation_id=42,
            content="hola",
            attachments=[],
            contact_id=55,
            phone="573001234567",
        )

    @pytest.mark.asyncio
    async def test_bot_off_label_skips_reply_but_still_acknowledges(self):
        """A human-paused conversation must not get an automated reply — but the event is still
        acknowledged (it was successfully delivered to a human-controlled conversation), not left
        to redeliver forever."""
        import inbox_poller
        from config import settings

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock(return_value=55)
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client, "create_customer_message_note", new=AsyncMock()
        ), patch.object(
            inbox_poller.chatwoot_client,
            "get_conversation_labels",
            new=AsyncMock(return_value=[settings.PAUSE_LABEL]),
        ), patch("main.process_incoming_message", new=AsyncMock()) as mock_process:
            await inbox_poller.poll_once()

        mock_process.assert_not_called()
        mock_ack.assert_awaited_once_with(["e1"])

    @pytest.mark.asyncio
    async def test_note_mirroring_failure_does_not_block_the_reply(self):
        """Human-visibility mirroring is best-effort — Taty must still answer even if posting the
        private note fails for some reason."""
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock(return_value=55)
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client,
            "create_customer_message_note",
            new=AsyncMock(side_effect=RuntimeError("chatwoot note failed")),
        ), patch.object(
            inbox_poller.chatwoot_client, "get_conversation_labels", new=AsyncMock(return_value=[])
        ), patch("main.process_incoming_message", new=AsyncMock()) as mock_process:
            await inbox_poller.poll_once()

        mock_process.assert_awaited_once()
        mock_ack.assert_awaited_once_with(["e1"])

    @pytest.mark.asyncio
    async def test_failed_conversation_lookup_leaves_event_unacknowledged(self):
        """A crash before reply generation must redeliver, not lose, the message."""
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_contact",
            new=AsyncMock(side_effect=RuntimeError("chatwoot down")),
        ):
            await inbox_poller.poll_once()

        mock_ack.assert_not_called()

    @pytest.mark.asyncio
    async def test_reply_generation_failure_leaves_event_unacknowledged(self):
        """If process_incoming_message itself raises, the event must redeliver too — not just
        failures in the Chatwoot mirroring/lookup steps."""
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock(return_value=55)
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client, "create_customer_message_note", new=AsyncMock()
        ), patch.object(
            inbox_poller.chatwoot_client, "get_conversation_labels", new=AsyncMock(return_value=[])
        ), patch(
            "main.process_incoming_message",
            new=AsyncMock(side_effect=RuntimeError("backend down")),
        ):
            await inbox_poller.poll_once()

        mock_ack.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_events_does_nothing(self):
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock()
        ) as mock_contact:
            await inbox_poller.poll_once()

        mock_ack.assert_not_called()
        mock_contact.assert_not_called()

    @pytest.mark.asyncio
    async def test_each_event_acknowledged_independently(self):
        """One failing event must not block acknowledgement of the others."""
        import inbox_poller

        events = [_event("e1"), _event("e2"), _event("e3")]

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=events)
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_contact",
            new=AsyncMock(side_effect=[55, RuntimeError("boom"), 57]),
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client, "create_customer_message_note", new=AsyncMock()
        ), patch.object(
            inbox_poller.chatwoot_client, "get_conversation_labels", new=AsyncMock(return_value=[])
        ), patch("main.process_incoming_message", new=AsyncMock()):
            await inbox_poller.poll_once()

        acked_ids = [eid for call in mock_ack.await_args_list for eid in call.args[0]]
        assert "e1" in acked_ids
        assert "e3" in acked_ids
        assert "e2" not in acked_ids
