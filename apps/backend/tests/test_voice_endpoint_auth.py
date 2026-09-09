"""POST /internal/whatsapp/voice-note (voicebox-local-voice-adoption).

The endpoint exists because Railway cannot reach the local VoiceBox and Chatwoot cannot deliver to
WhatsApp at all (its channel believes the 24h window is permanently closed —
apps/chatwoot-bridge/backend_client.py:85-101). So the LOCAL bridge synthesises the audio and posts
the finished bytes here, and this endpoint performs the Graph send.

Everything below is about refusing to send. The happy path is one test; the other twelve are the
ways this must say no — because the whole feature ships switched off, and "off" has to be provably
airtight rather than merely configured.

The endpoint coroutine is awaited directly rather than driven through `TestClient`: httpx 0.28.1
removed the `app=` shortcut that starlette 0.27.0's TestClient still passes, so TestClient raises
`TypeError` for every test in this repo right now. Pre-existing, unrelated to this change.
"""

from __future__ import annotations

import base64

import pytest
from fastapi import HTTPException

from presentation.voice_endpoints import VoiceNoteRequest, send_voice_note_endpoint

_KEY = "test-internal-key"
_OGG_B64 = base64.b64encode(b"OggS\x00fake-opus").decode()
_SPEAKABLE = "Hola, soy Taty. Con gusto te ayudo."


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)


@pytest.fixture
def voice_on(monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "VOICE_ENABLED", True)
    monkeypatch.setattr(settings, "VOICE_MAX_CHARS", 320)
    monkeypatch.setattr(settings, "VOICE_MAX_AUDIO_BYTES", 16777216)


def _request(**overrides) -> VoiceNoteRequest:
    payload = {
        "lead_id": "lead-1",
        "text": _SPEAKABLE,
        "audio_base64": _OGG_B64,
        "mime_type": "audio/ogg",
    }
    payload.update(overrides)
    return VoiceNoteRequest(**payload)


async def _call(request, key=_KEY):
    return await send_voice_note_endpoint(payload=request, x_internal_api_key=key)


def _status_of(excinfo) -> int:
    return excinfo.value.status_code


# --- Auth: fails closed -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_internal_key_env_returns_503(monkeypatch, voice_on):
    """No INTERNAL_API_KEY in the environment must reject everything, not wave traffic through."""
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


@pytest.mark.asyncio
async def test_empty_internal_key_env_returns_503(monkeypatch, voice_on):
    monkeypatch.setenv("INTERNAL_API_KEY", "")

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


@pytest.mark.asyncio
async def test_wrong_key_returns_401(keyed, voice_on):
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(), key="not-the-key")
    assert _status_of(excinfo) == 401


@pytest.mark.asyncio
async def test_absent_header_returns_401(keyed, voice_on):
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(), key=None)
    assert _status_of(excinfo) == 401


# --- The feature flag ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_voice_disabled_returns_503(keyed, monkeypatch):
    """This is the production behaviour for this change: shipped and switched off."""
    from config import settings

    monkeypatch.setattr(settings, "VOICE_ENABLED", False)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


@pytest.mark.asyncio
async def test_auth_is_checked_before_the_flag(monkeypatch):
    """An unauthenticated caller must not be able to learn whether voice is enabled."""
    from config import settings

    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)
    monkeypatch.setattr(settings, "VOICE_ENABLED", False)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(), key="wrong")
    assert _status_of(excinfo) == 401, "must reject on auth, not leak the flag state via 503"


# --- Payload validation -------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wrong_mime_type_returns_415(keyed, voice_on):
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(mime_type="audio/wav"))
    assert _status_of(excinfo) == 415, "WhatsApp voice notes are OGG/Opus only"


@pytest.mark.asyncio
async def test_oversize_payload_returns_413(keyed, voice_on, monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "VOICE_MAX_AUDIO_BYTES", 8)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(audio_base64=base64.b64encode(b"x" * 64).decode()))
    assert _status_of(excinfo) == 413


@pytest.mark.asyncio
async def test_undecodable_base64_returns_400(keyed, voice_on):
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(audio_base64="!!!not-base64!!!"))
    assert _status_of(excinfo) == 400


# --- The safety gate is re-checked here ---------------------------------------------------------

@pytest.mark.asyncio
async def test_text_with_a_figure_returns_422(keyed, voice_on):
    """Defence in depth: the bridge already saw voice_allowed=false, so asking anyway means the
    bridge is modified or stale. Refuse rather than trust it."""
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(text="Tu caja real de hoy es de $350.000."))
    assert _status_of(excinfo) == 422


@pytest.mark.asyncio
async def test_gate_is_the_real_one_not_a_reimplementation(keyed, voice_on):
    """The endpoint must call services.voice_safety.should_speak, not its own copy of the rule."""
    import presentation.voice_endpoints as voice_endpoints

    assert voice_endpoints.should_speak is __import__(
        "services.voice_safety", fromlist=["should_speak"]
    ).should_speak


# --- Delivery outcomes --------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_lead_returns_404(keyed, voice_on, monkeypatch):
    import presentation.voice_endpoints as voice_endpoints

    monkeypatch.setattr(voice_endpoints, "lead_exists", lambda _id: False)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 404


@pytest.mark.asyncio
async def test_missing_phone_reports_not_sent_without_failing(keyed, voice_on, monkeypatch):
    """A delivery failure is not the request's failure — the text reply already reached the
    customer, and a 5xx would make the bridge retry a send it must not repeat."""
    import presentation.voice_endpoints as voice_endpoints

    monkeypatch.setattr(voice_endpoints, "lead_exists", lambda _id: True)
    monkeypatch.setattr(voice_endpoints, "get_lead_phone", lambda _id: None)

    result = await _call(_request())
    assert result.sent is False
    assert result.reason == "no_phone"


@pytest.mark.asyncio
async def test_upload_failure_reports_not_sent(keyed, voice_on, monkeypatch):
    import presentation.voice_endpoints as voice_endpoints

    async def _upload_fails(_content, _mime):
        return None

    monkeypatch.setattr(voice_endpoints, "lead_exists", lambda _id: True)
    monkeypatch.setattr(voice_endpoints, "get_lead_phone", lambda _id: "573001234567")
    monkeypatch.setattr(voice_endpoints, "upload_whatsapp_media", _upload_fails)

    result = await _call(_request())
    assert result.sent is False
    assert result.reason == "upload_failed"


@pytest.mark.asyncio
async def test_happy_path_uploads_then_sends(keyed, voice_on, monkeypatch):
    import presentation.voice_endpoints as voice_endpoints

    calls = {}

    async def _upload(content, mime):
        calls["upload"] = (content, mime)
        return "MEDIA_123"

    async def _send(to, media_id):
        calls["send"] = (to, media_id)
        return True

    monkeypatch.setattr(voice_endpoints, "lead_exists", lambda _id: True)
    monkeypatch.setattr(voice_endpoints, "get_lead_phone", lambda _id: "573001234567")
    monkeypatch.setattr(voice_endpoints, "upload_whatsapp_media", _upload)
    monkeypatch.setattr(voice_endpoints, "send_whatsapp_audio", _send)

    result = await _call(_request())

    assert result.sent is True
    assert calls["upload"] == (b"OggS\x00fake-opus", "audio/ogg")
    assert calls["send"] == ("573001234567", "MEDIA_123"), "must send the id the upload returned"
