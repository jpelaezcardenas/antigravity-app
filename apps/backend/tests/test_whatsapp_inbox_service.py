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


class TestPullPendingQueryConstruction:
    """Real incident, twice over (2026-09-11): the query used to splice an "or=(...)" param
    directly into the postgrest builder's private internal attributes (`query.params`, then
    `query.request.params`). Both versions passed every local test and both raised a live
    AttributeError in production, because this repo's local dev venv (postgrest 2.31.0) and the
    version actually pinned for production (`supabase==2.0.3` in requirements.txt, which Railway
    installs) expose that internal state completely differently. Fixed by never touching those
    attributes at all: the query only uses the builder's public, stable `.select()`/`.is_()`/
    `.order()` methods, and the claimed_at-null-or-expired OR logic is applied in plain Python
    after `.execute()` returns. These tests build the query against the REAL installed postgrest
    client class (no network — `.execute()` is monkeypatched) specifically so a future
    reintroduction of a private-attribute hack would fail here again, on any interpreter."""

    def test_query_builds_against_the_real_client_without_raising(self, fake_supabase) -> None:
        import postgrest

        from services.whatsapp_inbox_service import pull_pending

        real_query = (
            postgrest.SyncPostgrestClient(base_url="http://localhost/rest/v1")
            .from_("whatsapp_inbound_events")
            .select("*")
            .is_("processed_at", "null")
        )
        fake_supabase.table.return_value.select.return_value.is_.return_value = real_query
        real_query.order = MagicMock(return_value=real_query)
        real_query.execute = lambda: MagicMock(data=[])

        pull_pending(limit=5)  # would raise on any private-attribute access removed by this fix

    def test_events_with_no_claim_or_an_expired_claim_are_returned(self, fake_supabase) -> None:
        from datetime import datetime, timedelta, timezone

        from services.whatsapp_inbox_service import pull_pending

        now = datetime.now(timezone.utc)
        expired = (now - timedelta(seconds=600)).isoformat()
        fresh = (now - timedelta(seconds=5)).isoformat()
        rows = [
            {"id": "1", "claimed_at": None},
            {"id": "2", "claimed_at": expired},
            {"id": "3", "claimed_at": fresh},
        ]
        query = MagicMock()
        query.execute.return_value = MagicMock(data=rows)
        fake_supabase.table.return_value.select.return_value.is_.return_value.order.return_value = (
            query
        )

        events = pull_pending(limit=50, claim_ttl_seconds=300)

        assert {e["id"] for e in events} == {"1", "2"}

    def test_limit_is_applied_after_client_side_filtering(self, fake_supabase) -> None:
        from services.whatsapp_inbox_service import pull_pending

        rows = [{"id": str(i), "claimed_at": None} for i in range(10)]
        query = MagicMock()
        query.execute.return_value = MagicMock(data=rows)
        fake_supabase.table.return_value.select.return_value.is_.return_value.order.return_value = (
            query
        )

        events = pull_pending(limit=3)

        assert len(events) == 3


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
