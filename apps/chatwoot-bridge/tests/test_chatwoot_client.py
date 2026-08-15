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
    monkeypatch.setattr(settings, "CHATWOOT_WHATSAPP_INBOX_ID", "7")


class TestFindOrCreateContact:
    """whatsapp-durable-inbox: the poller injects a message Meta already delivered — there is
    no Chatwoot-native webhook creating the contact for us, so the bridge must do it."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_existing_contact_is_reused(self):
        import chatwoot_client

        respx.get(f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/search").mock(
            return_value=Response(200, json={"payload": [{"id": 55, "name": "Maria"}]})
        )
        create_route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts"
        ).mock(return_value=Response(200, json={"payload": {"contact": {"id": 999}}}))

        contact_id = await chatwoot_client.find_or_create_contact("573001234567", "Maria")

        assert contact_id == 55
        assert not create_route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_new_contact_is_created_when_search_is_empty(self):
        import chatwoot_client

        respx.get(f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/search").mock(
            return_value=Response(200, json={"payload": []})
        )
        respx.post(f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts").mock(
            return_value=Response(200, json={"payload": {"contact": {"id": 999}}})
        )

        contact_id = await chatwoot_client.find_or_create_contact("573001234567", "Maria")

        assert contact_id == 999


class TestFindOrCreateConversation:
    @respx.mock
    @pytest.mark.asyncio
    async def test_existing_open_conversation_is_reused(self):
        import chatwoot_client

        respx.get(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/55/conversations"
        ).mock(
            return_value=Response(
                200, json={"payload": [{"id": 42, "inbox_id": 7, "status": "open"}]}
            )
        )
        create_route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"
        ).mock(return_value=Response(200, json={"id": 999}))

        conversation_id = await chatwoot_client.find_or_create_conversation(
            contact_id=55, phone="573001234567"
        )

        assert conversation_id == 42
        assert not create_route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_conversation_created_on_the_whatsapp_inbox_when_none_open(self):
        import chatwoot_client

        respx.get(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/55/conversations"
        ).mock(return_value=Response(200, json={"payload": []}))
        create_route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations"
        ).mock(return_value=Response(200, json={"id": 999}))

        conversation_id = await chatwoot_client.find_or_create_conversation(
            contact_id=55, phone="573001234567"
        )

        assert conversation_id == 999
        sent = create_route.calls.last.request
        import json as _json

        body = _json.loads(sent.content)
        assert body["inbox_id"] == "7"
        assert body["contact_id"] == 55


class TestCreateIncomingMessage:
    @respx.mock
    @pytest.mark.asyncio
    async def test_posts_an_incoming_message(self):
        import chatwoot_client

        route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/42/messages"
        ).mock(return_value=Response(200, json={"id": 1}))

        await chatwoot_client.create_incoming_message(42, "hola desde WhatsApp")

        assert route.called
        import json as _json

        body = _json.loads(route.calls.last.request.content)
        assert body["message_type"] == "incoming"
        assert body["content"] == "hola desde WhatsApp"


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
    """Chatwoot has no dedicated custom_attributes route for contacts (that member action
    exists only on conversations, per config/routes.rb) — setting them is a PATCH on the
    contact's own update endpoint, whose permitted_params includes custom_attributes and merges
    it with the contact's existing ones. A respx mock against the wrong URL/verb would still
    have passed here, the same way the wrong path shipped undetected before a real end-to-end
    run against live Chatwoot surfaced the 404 — the fix is verified against Chatwoot's actual
    ContactsController#update, not just re-mocked."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_custom_attributes(self):
        import chatwoot_client

        route = respx.patch(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/contacts/7"
        ).mock(return_value=Response(200, json={}))

        await chatwoot_client.set_contact_attributes(
            7, {"tipo_lead": "b2c", "estado": "nuevo"}
        )

        assert route.called
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["custom_attributes"] == {"tipo_lead": "b2c", "estado": "nuevo"}


class TestSetConversationAttributes:
    """chatwoot-auto-tagging: unlike contacts, conversations have a dedicated custom_attributes
    member route (config/routes.rb) — POST, not PATCH on the conversation itself."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_sets_custom_attributes(self):
        import chatwoot_client

        route = respx.post(
            f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/42/custom_attributes"
        ).mock(return_value=Response(200, json={}))

        await chatwoot_client.set_conversation_attributes(
            42, {"intencion": "ventas", "prioridad": "alta"}
        )

        assert route.called
        import json

        body = json.loads(route.calls[0].request.content)
        assert body["custom_attributes"] == {"intencion": "ventas", "prioridad": "alta"}
