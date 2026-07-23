"""Tests for chatwoot_client.py (Task Group 7): history fetch, reply dispatch,
contact custom attributes. All HTTP mocked with respx — no real network calls."""

from __future__ import annotations

import respx
import pytest
from httpx import Response

from config import settings

CHATWOOT_URL = "http://localhost:3020"
ACCOUNT_ID = "1"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "CHATWOOT_URL", CHATWOOT_URL)
    monkeypatch.setattr(settings, "CHATWOOT_ACCOUNT_ID", ACCOUNT_ID)
    monkeypatch.setattr(settings, "CHATWOOT_API_TOKEN", "test-chatwoot-token")
    monkeypatch.setattr(settings, "MAX_HISTORY", 3)


class TestGetRecentMessages:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_last_max_history_messages_mapped_to_role_content(self):
        import chatwoot_client

        route = respx.get(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/42/messages"
        ).mock(
            return_value=Response(
                200,
                json={
                    "payload": [
                        {"content": "msg1", "message_type": 0},
                        {"content": "msg2", "message_type": 1},
                        {"content": "msg3", "message_type": 0},
                        {"content": "msg4", "message_type": 1},
                        {"content": "msg5", "message_type": 0},
                    ]
                },
            )
        )

        history = await chatwoot_client.get_recent_messages(42)

        assert route.called
        assert history == [
            {"role": "user", "content": "msg3"},
            {"role": "assistant", "content": "msg4"},
            {"role": "user", "content": "msg5"},
        ]

    @respx.mock
    @pytest.mark.asyncio
    async def test_incoming_message_type_zero_maps_to_user(self):
        import chatwoot_client

        respx.get(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/1/messages"
        ).mock(
            return_value=Response(
                200, json={"payload": [{"content": "hi", "message_type": 0}]}
            )
        )

        history = await chatwoot_client.get_recent_messages(1)

        assert history == [{"role": "user", "content": "hi"}]


class TestSendReply:
    @respx.mock
    @pytest.mark.asyncio
    async def test_posts_outgoing_message(self):
        import chatwoot_client

        route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/42/messages"
        ).mock(return_value=Response(200, json={"id": 99}))

        await chatwoot_client.send_reply(42, "Hola, en que te ayudo?")

        assert route.called
        request = route.calls[0].request
        import json

        body = json.loads(request.content)
        assert body["content"] == "Hola, en que te ayudo?"
        assert body["message_type"] == "outgoing"


class TestSetContactAttributes:
    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_custom_attributes(self):
        import chatwoot_client

        route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/7/custom_attributes"
        ).mock(return_value=Response(200, json={}))

        await chatwoot_client.set_contact_attributes(
            7, {"tipo_lead": "b2c", "estado": "nuevo"}
        )

        assert route.called
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["custom_attributes"] == {"tipo_lead": "b2c", "estado": "nuevo"}
