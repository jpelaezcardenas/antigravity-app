"""
Credential-free unit tests for channels/whatsapp.py (taty-whatsapp-sales-router, Change D).

normalize_whatsapp_webhook is pure (no network, no credentials). send_whatsapp_message is tested
against a mocked httpx client plus the "not configured" no-credentials case, mirroring the
credential-free pattern established throughout the Sell Machine changes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from channels.whatsapp import (
    download_whatsapp_media,
    normalize_whatsapp_webhook,
    send_whatsapp_message,
)


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


def _fabricated_document_message_payload(phone="573001234567", media_id="MEDIA_ID_123"):
    return {
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "PHONE_ID"},
                            "contacts": [{"profile": {"name": "Doc Lead"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": "wamid.DOC123",
                                    "timestamp": "1721400000",
                                    "type": "document",
                                    "document": {
                                        "filename": "rut.pdf",
                                        "mime_type": "application/pdf",
                                        "sha256": "abc123",
                                        "id": media_id,
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ]
    }


def _fabricated_image_message_payload(phone="573001234567", media_id="MEDIA_ID_456"):
    return {
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "PHONE_ID"},
                            "contacts": [{"profile": {"name": "Img Lead"}, "wa_id": phone}],
                            "messages": [
                                {
                                    "from": phone,
                                    "id": "wamid.IMG456",
                                    "timestamp": "1721400000",
                                    "type": "image",
                                    "image": {
                                        "mime_type": "image/jpeg",
                                        "sha256": "def456",
                                        "id": media_id,
                                    },
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

    def test_document_message_normalizes_with_media_id_and_mime_type(self):
        events = normalize_whatsapp_webhook(_fabricated_document_message_payload())

        assert len(events) == 1
        event = events[0]
        assert event["channel"] == "whatsapp"
        assert event["account_id"] == "573001234567"
        assert event["media_id"] == "MEDIA_ID_123"
        assert event["mime_type"] == "application/pdf"
        assert event["text"] == ""

    def test_image_message_normalizes_the_same_way(self):
        events = normalize_whatsapp_webhook(_fabricated_image_message_payload())

        assert len(events) == 1
        event = events[0]
        assert event["media_id"] == "MEDIA_ID_456"
        assert event["mime_type"] == "image/jpeg"
        assert event["text"] == ""


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


class TestDownloadWhatsappMedia:
    @pytest.mark.asyncio
    async def test_returns_none_when_not_configured(self):
        with patch("channels.whatsapp.os.getenv", return_value=None):
            result = await download_whatsapp_media("MEDIA_ID_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_downloads_via_two_step_graph_api_flow_when_configured(self):
        metadata_response = AsyncMock()
        metadata_response.status_code = 200
        metadata_response.json = lambda: {
            "url": "https://media.whatsapp.example/download-me",
            "mime_type": "application/pdf",
        }
        file_response = AsyncMock()
        file_response.status_code = 200
        file_response.content = b"fake-pdf-bytes"

        with patch(
            "channels.whatsapp.os.getenv",
            side_effect=lambda key, default=None: {"WHATSAPP_TOKEN": "fake-token"}.get(
                key, default
            ),
        ), patch("channels.whatsapp.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = [metadata_response, file_response]
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await download_whatsapp_media("MEDIA_ID_123")

        assert result == {"content": b"fake-pdf-bytes", "mime_type": "application/pdf"}
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_metadata_fetch_fails(self):
        metadata_response = AsyncMock()
        metadata_response.status_code = 404

        with patch(
            "channels.whatsapp.os.getenv",
            side_effect=lambda key, default=None: {"WHATSAPP_TOKEN": "fake-token"}.get(
                key, default
            ),
        ), patch("channels.whatsapp.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = metadata_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await download_whatsapp_media("MEDIA_ID_123")

        assert result is None
