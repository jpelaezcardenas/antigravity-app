"""
Credential-free unit tests for channels/whatsapp.py (taty-whatsapp-sales-router, Change D).

normalize_whatsapp_webhook is pure (no network, no credentials). send_whatsapp_message is tested
against a mocked httpx client plus the "not configured" no-credentials case, mirroring the
credential-free pattern established throughout the Sell Machine changes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from channels.whatsapp import normalize_whatsapp_webhook, send_whatsapp_message


def _fabricated_text_message_payload(phone="573001234567", text="Hola, quiero saber de la declaracion de renta"):
    return {
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "573009999999", "phone_number_id": "PHONE_ID"},
                            "contacts": [{"profile": {"name": "Maria Lead"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": "wamid.ABC123",
                                    "timestamp": "1721400000",
                                    "text": {"body": text},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ]
    }


def _status_only_payload():
    return {
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "PHONE_ID"},
                            "statuses": [{"id": "wamid.ABC123", "status": "delivered"}],
                        },
                        "field": "messages",
                    }
                ],
            }
        ]
    }


class TestNormalizeWhatsappWebhook:
    def test_well_formed_text_message_normalizes(self):
        events = normalize_whatsapp_webhook(_fabricated_text_message_payload())

        assert len(events) == 1
        event = events[0]
        assert event["channel"] == "whatsapp"
        assert event["account_id"] == "573001234567"
        assert event["text"] == "Hola, quiero saber de la declaracion de renta"
        assert event["actor_name"] == "Maria Lead"

    def test_status_only_payload_returns_empty_list(self):
        events = normalize_whatsapp_webhook(_status_only_payload())
        assert events == []

    def test_missing_entry_key_does_not_raise(self):
        events = normalize_whatsapp_webhook({})
        assert events == []

    def test_malformed_nested_structure_does_not_raise(self):
        events = normalize_whatsapp_webhook({"entry": [{"changes": [{"value": {}}]}]})
        assert events == []


class TestSendWhatsappMessage:
    @pytest.mark.asyncio
    async def test_returns_false_when_not_configured(self):
        with patch("channels.whatsapp.os.getenv", return_value=None):
            result = await send_whatsapp_message("573001234567", "hola")
        assert result is False

    @pytest.mark.asyncio
    async def test_sends_via_graph_api_when_configured(self):
        mock_response = AsyncMock()
        mock_response.status_code = 200

        with patch(
            "channels.whatsapp.os.getenv",
            side_effect=lambda key, default=None: {
                "WHATSAPP_TOKEN": "fake-token",
                "WHATSAPP_PHONE_NUMBER_ID": "PHONE_ID",
            }.get(key, default),
        ), patch("channels.whatsapp.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await send_whatsapp_message("573001234567", "hola")

        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "PHONE_ID" in call_args[0][0]
