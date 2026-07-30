"""Tests for the durable-inbox poller (change: whatsapp-durable-inbox).

The poller pulls events the backend's webhook already persisted, injects each into Chatwoot, and
acknowledges only on success. It deliberately does NOT call taty_reply — Chatwoot's own webhook to
this bridge drives the reply (main.py::process_incoming_message), preserving the single-brain
invariant and the bot_off HITL check rather than re-implementing them here.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


def _event(event_id="e1", account_id="573001234567", body="hola", actor_name="Maria"):
    return {"id": event_id, "account_id": account_id, "body": body, "actor_name": actor_name}


class TestPollOnce:
    @pytest.mark.asyncio
    async def test_injects_pulled_event_into_chatwoot_and_acknowledges(self):
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ) as mock_ack, patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_contact",
            new=AsyncMock(return_value=55),
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client, "create_incoming_message", new=AsyncMock()
        ) as mock_create_msg:
            await inbox_poller.poll_once()

        mock_create_msg.assert_awaited_once_with(42, "hola")
        mock_ack.assert_awaited_once_with(["e1"])

    @pytest.mark.asyncio
    async def test_does_not_call_taty_reply(self):
        """Chatwoot's own webhook drives the reply — the poller only injects the customer's
        message. Calling taty_reply here would duplicate the bridge's filtering and the bot_off
        HITL check (design.md Decision 6)."""
        import inbox_poller

        with patch.object(
            inbox_poller.backend_client, "pull_pending_events", new=AsyncMock(return_value=[_event()])
        ), patch.object(
            inbox_poller.backend_client, "acknowledge_events", new=AsyncMock()
        ), patch.object(
            inbox_poller.backend_client, "taty_reply", new=AsyncMock()
        ) as mock_reply, patch.object(
            inbox_poller.chatwoot_client, "find_or_create_contact", new=AsyncMock(return_value=55)
        ), patch.object(
            inbox_poller.chatwoot_client,
            "find_or_create_conversation",
            new=AsyncMock(return_value=42),
        ), patch.object(
            inbox_poller.chatwoot_client, "create_incoming_message", new=AsyncMock()
        ):
            await inbox_poller.poll_once()

        mock_reply.assert_not_called()

    @pytest.mark.asyncio
    async def test_failed_injection_leaves_event_unacknowledged(self):
        """A crash between pulling and injecting must redeliver, not lose, the message."""
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

        async def flaky_create_conversation(contact_id, phone):
            if phone == events[1]["account_id"] and contact_id == "fail-marker":
                raise RuntimeError("boom")
            return 42

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
            inbox_poller.chatwoot_client, "create_incoming_message", new=AsyncMock()
        ):
            await inbox_poller.poll_once()

        acked_ids = [eid for call in mock_ack.await_args_list for eid in call.args[0]]
        assert "e1" in acked_ids
        assert "e3" in acked_ids
        assert "e2" not in acked_ids
