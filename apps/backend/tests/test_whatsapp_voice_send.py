"""Outbound WhatsApp audio via the Graph API (voicebox-local-voice-adoption).

Sending a voice note is a TWO-step Graph flow, the mirror image of the existing
`download_whatsapp_media`: upload the bytes to `/{phone_number_id}/media` to get a media id, then
post a `type: "audio"` message referencing that id.

These tests drive the real functions through an `httpx.MockTransport`, so httpx itself builds the
multipart body and the JSON payload and the assertions run against what would actually go on the
wire. Nothing patches `upload_whatsapp_media` or `send_whatsapp_audio` — patching the function
under test would assert only that the mock was called (ARCHITECTURE.md Decisión #22).

Credential-free: every test sets fake env values or explicitly clears them.
"""

from __future__ import annotations

import httpx
import pytest

from channels.whatsapp import send_whatsapp_audio, upload_whatsapp_media

_FAKE_TOKEN = "test-token"
_FAKE_PHONE_ID = "PHONE_ID"
_OGG = b"OggS\x00fake-opus-bytes"


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("WHATSAPP_TOKEN", _FAKE_TOKEN)
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", _FAKE_PHONE_ID)


@pytest.fixture
def unconfigured(monkeypatch):
    monkeypatch.delenv("WHATSAPP_TOKEN", raising=False)
    monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)


# Captured before any monkeypatching, so the factory below builds a REAL client rather than
# re-entering the patched name.
_RealAsyncClient = httpx.AsyncClient


def _install_transport(monkeypatch, handler, calls):
    """Point every `httpx.AsyncClient()` in the code under test at a MockTransport.

    httpx builds the real request (multipart encoding included) and hands it to `handler`, so the
    assertions run against what would genuinely go on the wire.
    """

    def _record(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    transport = httpx.MockTransport(_record)

    def _factory(*args, **kwargs):
        kwargs["transport"] = transport
        return _RealAsyncClient(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", _factory)


# --- upload_whatsapp_media ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_posts_multipart_and_returns_media_id(configured, monkeypatch):
    calls: list[httpx.Request] = []

    def handler(request):
        return httpx.Response(200, json={"id": "MEDIA_123"})

    _install_transport(monkeypatch, handler, calls)

    media_id = await upload_whatsapp_media(_OGG, "audio/ogg")

    assert media_id == "MEDIA_123"
    assert len(calls) == 1
    request = calls[0]
    assert request.method == "POST"
    assert request.url.path.endswith(f"/{_FAKE_PHONE_ID}/media")
    assert request.headers["authorization"] == f"Bearer {_FAKE_TOKEN}"

    body = request.content
    assert b"multipart/form-data" in request.headers["content-type"].encode()
    assert b"whatsapp" in body, "messaging_product must be in the multipart body"
    assert _OGG in body, "the audio bytes must be uploaded, not a path or a placeholder"


@pytest.mark.asyncio
async def test_upload_returns_none_and_makes_no_call_when_unconfigured(unconfigured, monkeypatch):
    calls: list[httpx.Request] = []
    _install_transport(monkeypatch, lambda r: httpx.Response(200, json={"id": "X"}), calls)

    assert await upload_whatsapp_media(_OGG, "audio/ogg") is None
    assert calls == [], "must never call out with empty credentials"


@pytest.mark.asyncio
async def test_upload_returns_none_on_non_200(configured, monkeypatch):
    calls: list[httpx.Request] = []
    _install_transport(monkeypatch, lambda r: httpx.Response(400, json={"error": "bad"}), calls)

    assert await upload_whatsapp_media(_OGG, "audio/ogg") is None


@pytest.mark.asyncio
async def test_upload_returns_none_when_response_has_no_id(configured, monkeypatch):
    """A 200 without an `id` is a failed upload, not a success."""
    calls: list[httpx.Request] = []
    _install_transport(monkeypatch, lambda r: httpx.Response(200, json={}), calls)

    assert await upload_whatsapp_media(_OGG, "audio/ogg") is None


# --- send_whatsapp_audio ------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_posts_type_audio_referencing_the_media_id(configured, monkeypatch):
    calls: list[httpx.Request] = []
    _install_transport(monkeypatch, lambda r: httpx.Response(200, json={"messages": [{"id": "wamid.X"}]}), calls)

    assert await send_whatsapp_audio("573001234567", "MEDIA_123") is True

    import json

    payload = json.loads(calls[0].content)
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "573001234567"
    assert payload["type"] == "audio", "a voice note is type 'audio', not 'text'"
    assert payload["audio"] == {"id": "MEDIA_123"}
    assert calls[0].url.path.endswith(f"/{_FAKE_PHONE_ID}/messages")


@pytest.mark.asyncio
async def test_send_returns_false_and_makes_no_call_when_unconfigured(unconfigured, monkeypatch):
    calls: list[httpx.Request] = []
    _install_transport(monkeypatch, lambda r: httpx.Response(200, json={}), calls)

    assert await send_whatsapp_audio("573001234567", "MEDIA_123") is False
    assert calls == []


@pytest.mark.asyncio
async def test_send_returns_false_on_non_200(configured, monkeypatch):
    calls: list[httpx.Request] = []
    _install_transport(monkeypatch, lambda r: httpx.Response(401, json={"error": "nope"}), calls)

    assert await send_whatsapp_audio("573001234567", "MEDIA_123") is False


@pytest.mark.asyncio
async def test_send_never_raises_on_transport_error(configured, monkeypatch):
    """A delivery failure must not become the caller's exception — same contract as
    send_whatsapp_message."""

    def boom(request):
        raise httpx.ConnectError("network down")

    _install_transport(monkeypatch, boom, [])

    assert await send_whatsapp_audio("573001234567", "MEDIA_123") is False
