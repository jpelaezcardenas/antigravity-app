"""Tests for POST /webhook filtering + HITL truth table (Task Group 6).

Covers the full truth table from
openspec/changes/chatwoot-hermes-taty-bridge/specs/chatwoot-hermes-bridge/spec.md:
incoming+not-private -> process, outgoing -> skip, private -> skip,
non-message_created event -> skip, missing/invalid WEBHOOK_TOKEN -> 401,
bot_off label present -> paused (no Hermes call).

process_incoming_message is patched out entirely — this module only tests the
filter/auth/HITL decision layer, not the background pipeline (see
test_process_message.py for that).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

from config import settings


def _base_payload(**overrides):
    payload = {
        "event": "message_created",
        "message_type": "incoming",
        "private": False,
        "content": "Hola, necesito ayuda",
        "conversation": {"id": 42, "labels": []},
        "sender": {"id": 7, "phone_number": "+573001234567"},
        "attachments": [],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def app_and_client(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_TOKEN", "test-token")

    import main as main_module

    transport = httpx.ASGITransport(app=main_module.app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    return main_module, client


class TestWebhookAuth:
    @pytest.mark.asyncio
    async def test_missing_token_is_rejected(self, app_and_client):
        _, client = app_and_client
        async with client as c:
            response = await c.post("/webhook", json=_base_payload())
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_token_is_rejected(self, app_and_client):
        _, client = app_and_client
        async with client as c:
            response = await c.post(
                "/webhook", json=_base_payload(), params={"token": "wrong"}
            )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_token_check_happens_before_event_parsing(self, app_and_client):
        """An invalid token must be rejected even with a malformed/garbage body."""
        _, client = app_and_client
        async with client as c:
            response = await c.post("/webhook", content=b"not json at all")
        assert response.status_code == 401


class TestWebhookFilterTruthTable:
    @pytest.mark.asyncio
    async def test_incoming_not_private_is_processed(self, app_and_client):
        main_module, client = app_and_client
        with patch.object(main_module, "process_incoming_message") as mock_process:
            async with client as c:
                response = await c.post(
                    "/webhook", json=_base_payload(), params={"token": "test-token"}
                )
        assert response.status_code == 200
        assert response.json() == {"status": "processing_started"}
        # Scheduled via BackgroundTasks; ASGITransport runs it before returning
        # control here, so by now it has been invoked exactly once.
        mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_outgoing_message_is_skipped(self, app_and_client):
        main_module, client = app_and_client
        with patch.object(main_module, "process_incoming_message") as mock_process:
            async with client as c:
                response = await c.post(
                    "/webhook",
                    json=_base_payload(message_type="outgoing"),
                    params={"token": "test-token"},
                )
        assert response.status_code == 200
        assert response.json() == {"status": "skipped"}
        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_private_note_is_skipped(self, app_and_client):
        main_module, client = app_and_client
        with patch.object(main_module, "process_incoming_message") as mock_process:
            async with client as c:
                response = await c.post(
                    "/webhook",
                    json=_base_payload(private=True),
                    params={"token": "test-token"},
                )
        assert response.status_code == 200
        assert response.json() == {"status": "skipped"}
        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_message_created_event_is_skipped(self, app_and_client):
        main_module, client = app_and_client
        with patch.object(main_module, "process_incoming_message") as mock_process:
            async with client as c:
                response = await c.post(
                    "/webhook",
                    json=_base_payload(event="conversation_status_changed"),
                    params={"token": "test-token"},
                )
        assert response.status_code == 200
        assert response.json() == {"status": "skipped"}
        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_bot_off_label_pauses_processing(self, app_and_client):
        main_module, client = app_and_client
        payload = _base_payload(conversation={"id": 42, "labels": ["bot_off"]})
        with patch.object(main_module, "process_incoming_message") as mock_process:
            async with client as c:
                response = await c.post(
                    "/webhook", json=payload, params={"token": "test-token"}
                )
        assert response.status_code == 200
        assert response.json() == {"status": "paused", "reason": "bot_off tag active"}
        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_bot_off_label_processes_normally(self, app_and_client):
        main_module, client = app_and_client
        payload = _base_payload(conversation={"id": 42, "labels": ["vip"]})
        with patch.object(main_module, "process_incoming_message") as mock_process:
            async with client as c:
                response = await c.post(
                    "/webhook", json=payload, params={"token": "test-token"}
                )
        assert response.status_code == 200
        assert response.json() == {"status": "processing_started"}
        mock_process.assert_called_once()
