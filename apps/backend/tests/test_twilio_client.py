"""Tests for services/twilio_client.py (taty-voice-outbound-calls, Task 2.4).

Mirrors channels/whatsapp.py's own test convention (tests/test_whatsapp_channel.py): patch
`services.twilio_client.httpx.AsyncClient` with an AsyncMock, never a real network call.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from config import settings
from services import twilio_client


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACxxxx")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "fake-token")
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "+15551234567")


class TestIsConfigured:
    def test_true_when_all_three_present(self):
        assert twilio_client.is_configured() is True

    def test_false_when_missing_one(self, monkeypatch):
        monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "")
        assert twilio_client.is_configured() is False


class TestPlaceCall:
    @pytest.mark.asyncio
    async def test_refuses_when_not_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "")
        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            result = await twilio_client.place_call("573001234567", "<Response/>")
        assert result is None
        mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_places_call_and_returns_sid(self):
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json = lambda: {"sid": "CAxxxx"}

        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await twilio_client.place_call("573001234567", "<Response/>")

        assert result == "CAxxxx"
        call_args = mock_client.post.call_args
        assert call_args.kwargs["data"]["To"] == "573001234567"
        assert call_args.kwargs["data"]["From"] == "+15551234567"
        assert call_args.kwargs["data"]["Twiml"] == "<Response/>"
        assert call_args.kwargs["auth"] == ("ACxxxx", "fake-token")

    @pytest.mark.asyncio
    async def test_returns_none_on_non_2xx(self):
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await twilio_client.place_call("573001234567", "<Response/>")

        assert result is None

    @pytest.mark.asyncio
    async def test_never_raises_on_exception(self):
        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value.__aenter__.side_effect = Exception("boom")
            result = await twilio_client.place_call("573001234567", "<Response/>")
        assert result is None


class TestPlaceCallViaUrl:
    """place_call_via_url uses Twilio's `Url` param (trial-compatible), never inline `Twiml` —
    confirmed live 2026-09-10 that Twilio trial rejects inline `Twiml` with a 400."""

    @pytest.mark.asyncio
    async def test_refuses_when_not_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "")
        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            result = await twilio_client.place_call_via_url(
                "573001234567", "https://handler.twilio.com/twiml/EHxxxx"
            )
        assert result is None
        mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_places_call_and_returns_sid(self):
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.json = lambda: {"sid": "CAyyyy"}

        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await twilio_client.place_call_via_url(
                "573001234567", "https://handler.twilio.com/twiml/EHxxxx"
            )

        assert result == "CAyyyy"
        call_args = mock_client.post.call_args
        assert call_args.kwargs["data"]["To"] == "573001234567"
        assert call_args.kwargs["data"]["From"] == "+15551234567"
        assert call_args.kwargs["data"]["Url"] == "https://handler.twilio.com/twiml/EHxxxx"
        assert "Twiml" not in call_args.kwargs["data"]
        assert call_args.kwargs["auth"] == ("ACxxxx", "fake-token")

    @pytest.mark.asyncio
    async def test_returns_none_on_non_2xx(self):
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            result = await twilio_client.place_call_via_url(
                "573001234567", "https://handler.twilio.com/twiml/EHxxxx"
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_never_raises_on_exception(self):
        with patch("services.twilio_client.httpx.AsyncClient") as mock_client_cls:
            mock_client_cls.return_value.__aenter__.side_effect = Exception("boom")
            result = await twilio_client.place_call_via_url(
                "573001234567", "https://handler.twilio.com/twiml/EHxxxx"
            )
        assert result is None
