"""Tests for whisper_client.py (taty-voice-outbound-calls, Task 3).

Mirrors test_voicebox_client.py's respx convention — no real Whisper server in tests.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response

from config import settings

WHISPER_URL = "http://127.0.0.1:9000/transcribe"
AUDIO = b"RIFF....WAVEfmt fake-wav-bytes"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_WHISPER_URL", WHISPER_URL)


class TestTranscribe:
    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_transcript_on_success(self):
        respx.post(WHISPER_URL).mock(return_value=Response(200, json={"text": "hola quiero declarar"}))

        import whisper_client

        result = await whisper_client.transcribe(AUDIO)

        assert result == "hola quiero declarar"

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_when_not_configured(self, monkeypatch):
        monkeypatch.setattr(settings, "LOCAL_WHISPER_URL", "")
        route = respx.post(WHISPER_URL).mock(return_value=Response(200, json={"text": "x"}))

        import whisper_client

        assert await whisper_client.transcribe(AUDIO) is None
        assert not route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_for_empty_audio(self):
        route = respx.post(WHISPER_URL).mock(return_value=Response(200, json={"text": "x"}))

        import whisper_client

        assert await whisper_client.transcribe(b"") is None
        assert not route.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_on_non_200(self):
        respx.post(WHISPER_URL).mock(return_value=Response(500, text="server error"))

        import whisper_client

        assert await whisper_client.transcribe(AUDIO) is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_when_response_has_no_text_field(self):
        respx.post(WHISPER_URL).mock(return_value=Response(200, json={}))

        import whisper_client

        assert await whisper_client.transcribe(AUDIO) is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_never_raises_when_server_is_down(self):
        respx.post(WHISPER_URL).mock(side_effect=httpx.ConnectError("refused"))

        import whisper_client

        assert await whisper_client.transcribe(AUDIO) is None
