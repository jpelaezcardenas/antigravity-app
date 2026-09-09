"""Tests for backend_client.send_voice_note (voicebox-local-voice-adoption).

This is the hop that carries locally-synthesised audio to the backend, which performs the Graph API
delivery. Two things make it different from the other backend_client calls:

1. It targets `/internal/*`, NOT `/api/v1/*`. That distinction is a security boundary, not a
   detail: `vercel.json` rewrites `/api/v1/:path*` to Railway and publishes it to the internet,
   while `/internal` is reachable only by callers that already know the host. Deriving the URL by
   appending to `CONTEXIA_API_URL` would silently produce `/api/v1/internal/...` and publish a
   machine-to-machine endpoint.
2. It authenticates with `INTERNAL_API_KEY`, the same shared key the Siigo and Gmail pollers use —
   not the tenant JWT the other calls sign.

Fail-soft: returns False on every failure, never raises.
"""

from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx
from httpx import Response

from config import settings

API_URL = "http://127.0.0.1:8080/api/v1"
INTERNAL_URL = "http://127.0.0.1:8080/internal/whatsapp/voice-note"
AUDIO = b"OggS\x00fake-opus-bytes"
KEY = "test-internal-key"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "CONTEXIA_API_URL", API_URL)
    monkeypatch.setattr(settings, "INTERNAL_API_KEY", KEY)


@respx.mock
@pytest.mark.asyncio
async def test_posts_to_internal_not_api_v1():
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"sent": True}))

    import backend_client

    assert await backend_client.send_voice_note("lead-1", "Hola", AUDIO) is True
    assert route.called, "must post to /internal/whatsapp/voice-note, not under /api/v1"


@respx.mock
@pytest.mark.asyncio
async def test_sends_base64_audio_text_and_mime():
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"sent": True}))

    import backend_client

    await backend_client.send_voice_note("lead-1", "Hola", AUDIO)

    body = json.loads(route.calls[0].request.content)
    assert body["lead_id"] == "lead-1"
    assert body["text"] == "Hola"
    assert body["mime_type"] == "audio/ogg"
    assert base64.b64decode(body["audio_base64"]) == AUDIO


@respx.mock
@pytest.mark.asyncio
async def test_sends_the_internal_api_key_header():
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"sent": True}))

    import backend_client

    await backend_client.send_voice_note("lead-1", "Hola", AUDIO)

    assert route.calls[0].request.headers["x-internal-api-key"] == KEY


@respx.mock
@pytest.mark.asyncio
async def test_returns_false_when_backend_reports_not_sent():
    """A 200 with sent:false is a non-delivery (no phone, upload failed), not a success."""
    respx.post(INTERNAL_URL).mock(
        return_value=Response(200, json={"sent": False, "reason": "no_phone"})
    )

    import backend_client

    assert await backend_client.send_voice_note("lead-1", "Hola", AUDIO) is False


@respx.mock
@pytest.mark.asyncio
async def test_returns_false_on_503_voice_disabled():
    """The expected production response today: the feature ships switched off."""
    respx.post(INTERNAL_URL).mock(return_value=Response(503, json={"detail": "Voice is disabled"}))

    import backend_client

    assert await backend_client.send_voice_note("lead-1", "Hola", AUDIO) is False


@respx.mock
@pytest.mark.asyncio
async def test_returns_false_on_401():
    respx.post(INTERNAL_URL).mock(return_value=Response(401, json={"detail": "Invalid key"}))

    import backend_client

    assert await backend_client.send_voice_note("lead-1", "Hola", AUDIO) is False


@respx.mock
@pytest.mark.asyncio
async def test_never_raises_on_network_failure():
    respx.post(INTERNAL_URL).mock(side_effect=httpx.ConnectError("backend down"))

    import backend_client

    assert await backend_client.send_voice_note("lead-1", "Hola", AUDIO) is False


@respx.mock
@pytest.mark.asyncio
async def test_returns_false_without_an_internal_key(monkeypatch):
    """No key configured means no call — the backend would answer 401 anyway."""
    monkeypatch.setattr(settings, "INTERNAL_API_KEY", "")
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"sent": True}))

    import backend_client

    assert await backend_client.send_voice_note("lead-1", "Hola", AUDIO) is False
    assert not route.called
