"""Tests for the durable WhatsApp inbox (change: whatsapp-durable-inbox).

The behaviour that matters here is not "does it insert" — it is that duplicates collapse and that
an event without Meta's message id is never written, because a blank id would collide every
un-idded message into a single row through the UNIQUE constraint and silently discard real
customer messages.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _event(message_id: str, text: str = "hola", **extra):
    base = {
        "channel": "whatsapp",
        "account_id": "573001234567",
        "source_event_id": message_id,
        "event_type": "message",
        "actor_handle": "573001234567",
        "actor_name": "Maria Lead",
        "text": text,
        "raw_payload": {"entry": []},
    }
    base.update(extra)
    return base


@pytest.fixture
def fake_supabase():
    client = MagicMock()
    with patch(
        "services.whatsapp_inbox_service.get_service_supabase", return_value=client
    ):
        yield client


class TestStoreInboundEvents:
    def test_stores_a_normal_event(self, fake_supabase) -> None:
        from services.whatsapp_inbox_service import store_inbound_events

        stored = store_inbound_events([_event("wamid.AAA")])

        assert stored == 1
        rows = fake_supabase.table.return_value.upsert.call_args[0][0]
        assert rows[0]["meta_message_id"] == "wamid.AAA"
        assert rows[0]["account_id"] == "573001234567"
        assert rows[0]["body"] == "hola"

    def test_dedup_is_delegated_to_the_database(self, fake_supabase) -> None:
        """ON CONFLICT DO NOTHING — not a read-then-write check, which two concurrent Meta
        retries would race."""
        from services.whatsapp_inbox_service import store_inbound_events

        store_inbound_events([_event("wamid.AAA")])

        kwargs = fake_supabase.table.return_value.upsert.call_args[1]
        assert kwargs.get("on_conflict") == "meta_message_id"
        assert kwargs.get("ignore_duplicates") is True

    def test_event_without_meta_id_is_never_written(self, fake_supabase) -> None:
        """A blank id would collide every un-idded message into one row via the UNIQUE
        constraint, silently discarding real messages. Skipping is the safe failure."""
        from services.whatsapp_inbox_service import store_inbound_events

        stored = store_inbound_events([_event(""), _event("   ")])

        assert stored == 0
        fake_supabase.table.return_value.upsert.assert_not_called()

    def test_mixed_batch_stores_only_identifiable_events(self, fake_supabase) -> None:
        from services.whatsapp_inbox_service import store_inbound_events

        stored = store_inbound_events([_event("wamid.AAA"), _event(""), _event("wamid.BBB")])

        assert stored == 2
        rows = fake_supabase.table.return_value.upsert.call_args[0][0]
        assert [r["meta_message_id"] for r in rows] == ["wamid.AAA", "wamid.BBB"]

    def test_empty_batch_touches_no_database(self, fake_supabase) -> None:
        from services.whatsapp_inbox_service import store_inbound_events

        assert store_inbound_events([]) == 0
        fake_supabase.table.assert_not_called()

    def test_media_event_preserves_media_fields(self, fake_supabase) -> None:
        from services.whatsapp_inbox_service import store_inbound_events

        store_inbound_events(
            [_event("wamid.MEDIA", text="", media_id="MID1", mime_type="application/pdf")]
        )

        rows = fake_supabase.table.return_value.upsert.call_args[0][0]
        assert rows[0]["media_id"] == "MID1"
        assert rows[0]["mime_type"] == "application/pdf"


class TestInboxHealth:
    def test_reports_backlog_depth_and_oldest_age(self, fake_supabase) -> None:
        """An offline local node must be detectable — a durable queue nobody watches is a queue
        that quietly grows."""
        from services.whatsapp_inbox_service import inbox_health

        result = MagicMock()
        result.data = [{"created_at": "2026-07-28T10:00:00+00:00"}]
        result.count = 7
        fake_supabase.table.return_value.select.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value = (
            result
        )

        health = inbox_health()

        assert health["pending"] == 7
        assert health["oldest_pending_at"] == "2026-07-28T10:00:00+00:00"

    def test_empty_queue_reports_zero_and_no_oldest(self, fake_supabase) -> None:
        from services.whatsapp_inbox_service import inbox_health

        result = MagicMock()
        result.data = []
        result.count = 0
        fake_supabase.table.return_value.select.return_value.is_.return_value.order.return_value.limit.return_value.execute.return_value = (
            result
        )

        health = inbox_health()

        assert health["pending"] == 0
        assert health["oldest_pending_at"] is None
