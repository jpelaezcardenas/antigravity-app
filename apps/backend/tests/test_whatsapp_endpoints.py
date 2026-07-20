"""
Tests for WhatsApp channel endpoints (taty-whatsapp-sales-router, Change D).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established in test_sell_machine_endpoints.py /
test_operator_task_endpoints.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI


class TestWhatsappCanonicalFeatureFlag:
    def test_flag_exists_and_defaults_to_false(self) -> None:
        from config import settings

        assert hasattr(settings, "WHATSAPP_CANONICAL")
        assert settings.WHATSAPP_CANONICAL is False

    def test_router_conditionally_included_on_flag(self) -> None:
        with open("presentation/router.py", "r", encoding="utf-8") as f:
            router_code = f.read()

        assert "if settings.WHATSAPP_CANONICAL:" in router_code
        assert 'prefix="/channels/whatsapp"' in router_code


@pytest.fixture
def wa_client():
    from presentation.whatsapp_endpoints import router as whatsapp_router

    app = FastAPI()
    app.include_router(whatsapp_router, prefix="/channels/whatsapp")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestWebhookVerification:
    @pytest.mark.asyncio
    async def test_valid_verification_echoes_challenge(self, wa_client) -> None:
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.os.getenv",
                side_effect=lambda key, default=None: "correct-token"
                if key == "WHATSAPP_WEBHOOK_VERIFY_TOKEN"
                else default,
            ):
                response = await client.get(
                    "/channels/whatsapp/webhook",
                    params={
                        "hub.mode": "subscribe",
                        "hub.verify_token": "correct-token",
                        "hub.challenge": "12345",
                    },
                )

        assert response.status_code == 200
        assert response.text == "12345"

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, wa_client) -> None:
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.os.getenv",
                side_effect=lambda key, default=None: "correct-token"
                if key == "WHATSAPP_WEBHOOK_VERIFY_TOKEN"
                else default,
            ):
                response = await client.get(
                    "/channels/whatsapp/webhook",
                    params={
                        "hub.mode": "subscribe",
                        "hub.verify_token": "wrong-token",
                        "hub.challenge": "12345",
                    },
                )

        assert response.status_code == 403


class TestInboundWebhook:
    @pytest.mark.asyncio
    async def test_inbound_message_normalizes_and_routes(self, wa_client) -> None:
        fake_events = [
            {
                "channel": "whatsapp",
                "account_id": "573001234567",
                "text": "Quiero saber si me toca declarar renta este año",
                "actor_name": "Maria Lead",
                "raw_payload": {},
            }
        ]
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook",
                return_value=fake_events,
            ), patch(
                "presentation.whatsapp_endpoints.find_or_create_lead", return_value="lead-1"
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={"intent": "sales_interest", "confidence": 0.8, "reply": "..."},
            ) as mock_route:
                response = await client.post("/channels/whatsapp/webhook", json={"entry": []})

        assert response.status_code == 200
        assert response.json()["events_processed"] == 1
        mock_route.assert_called_once_with("lead-1", "Quiero saber si me toca declarar renta este año")

    @pytest.mark.asyncio
    async def test_text_message_reply_is_sent_back_to_the_lead(self, wa_client) -> None:
        fake_events = [
            {
                "channel": "whatsapp",
                "account_id": "573001234567",
                "text": "Quiero saber si me toca declarar renta este año",
                "actor_name": "Maria Lead",
                "raw_payload": {},
            }
        ]
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook",
                return_value=fake_events,
            ), patch(
                "presentation.whatsapp_endpoints.find_or_create_lead", return_value="lead-1"
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={
                    "intent": "sales_interest",
                    "confidence": 0.8,
                    "reply": "Aquí tienes el link de pago...",
                },
            ), patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ) as mock_send:
                response = await client.post("/channels/whatsapp/webhook", json={"entry": []})

        assert response.status_code == 200
        mock_send.assert_called_once_with("573001234567", "Aquí tienes el link de pago...")

    @pytest.mark.asyncio
    async def test_send_failure_does_not_affect_the_webhook_response(self, wa_client) -> None:
        fake_events = [
            {
                "channel": "whatsapp",
                "account_id": "573001234567",
                "text": "hola",
                "actor_name": "Maria Lead",
                "raw_payload": {},
            }
        ]
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook",
                return_value=fake_events,
            ), patch(
                "presentation.whatsapp_endpoints.find_or_create_lead", return_value="lead-1"
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={"intent": "unknown", "confidence": 0.0, "reply": "..."},
            ), patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=False),
            ):
                response = await client.post("/channels/whatsapp/webhook", json={"entry": []})

        assert response.status_code == 200
        assert response.json()["events_processed"] == 1

    @pytest.mark.asyncio
    async def test_document_event_does_not_call_send_directly_from_handler(self, wa_client) -> None:
        """route_lead_document already handles its own sends internally (Change I) — the
        handler must not additionally call send_whatsapp_message for media events."""
        fake_events = [
            {
                "channel": "whatsapp",
                "account_id": "573001234567",
                "media_id": "MEDIA123",
                "mime_type": "application/pdf",
                "text": "",
                "actor_name": "Maria Lead",
                "raw_payload": {},
            }
        ]
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook",
                return_value=fake_events,
            ), patch(
                "presentation.whatsapp_endpoints.find_or_create_lead", return_value="lead-1"
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_document",
                new=AsyncMock(return_value={"processed": True}),
            ), patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ) as mock_send:
                response = await client.post("/channels/whatsapp/webhook", json={"entry": []})

        assert response.status_code == 200
        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_events_returns_ack_without_routing(self, wa_client) -> None:
        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook", return_value=[]
            ), patch("presentation.whatsapp_endpoints.route_lead_message") as mock_route:
                response = await client.post("/channels/whatsapp/webhook", json={"entry": []})

        assert response.status_code == 200
        assert response.json()["events_processed"] == 0
        mock_route.assert_not_called()
