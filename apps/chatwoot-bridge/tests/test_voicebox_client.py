"""Tests for voicebox_client.py (voicebox-local-voice-adoption).

Synthesis is a TWO-call flow, verified live against the running server's own OpenAPI document on
2026-09-08: `POST /generate` answers with JSON (`GenerationResponse`), not audio, and the bytes come
from a second `GET /audio/{id}`. Code written on the README's summary — that `/generate` returns a
WAV — would be wrong.

Two request defaults are traps and both are asserted here: VoiceBox defaults `language` to `en` and
`model_size` to `1.7B`, the model Phase 0 measured at 30-60 minutes per phrase on CPU. A request
that omits them yields English speech from the slowest model.

Fail-soft throughout, mirroring backend_client.whatsapp_intake: every failure returns None and is
logged. A missing voice note is a non-event — the text reply was already delivered.

All HTTP is mocked with respx, the convention already used across this package.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from httpx import Response

from config import settings

VOICEBOX_URL = "http://127.0.0.1:17493"
PROFILE_ID = "b20f2783-5745-4c1b-b820-33396c0387ea"
AUDIO = b"OggS\x00fake-opus-bytes"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "VOICEBOX_URL", VOICEBOX_URL)
    monkeypatch.setattr(settings, "VOICEBOX_PROFILE_ID", PROFILE_ID)
    monkeypatch.setattr(settings, "VOICEBOX_ENGINE", "qwen")
    monkeypatch.setattr(settings, "VOICEBOX_MODEL_SIZE", "0.6B")
    monkeypatch.setattr(settings, "VOICEBOX_LANGUAGE", "es")
    monkeypatch.setattr(settings, "VOICEBOX_TIMEOUT_SECONDS", 5)


class TestSynthesize:
    @respx.mock
    @pytest.mark.asyncio
    async def test_posts_generate_then_fetches_audio(self):
        generate = respx.post(f"{VOICEBOX_URL}/generate").mock(
            return_value=Response(200, json={"id": "gen-1", "status": "completed"})
        )
        audio = respx.get(f"{VOICEBOX_URL}/audio/gen-1").mock(
            return_value=Response(200, content=AUDIO)
        )

        import voicebox_client

        result = await voicebox_client.synthesize("Hola, soy Taty.")

        assert result == AUDIO
        assert generate.called and audio.called

    @respx.mock
    @pytest.mark.asyncio
    async def test_request_overrides_the_two_dangerous_defaults(self):
        """`language` and `model_size` must always be explicit."""
        generate = respx.post(f"{VOICEBOX_URL}/generate").mock(
            return_value=Response(200, json={"id": "gen-1", "status": "completed"})
        )
        respx.get(f"{VOICEBOX_URL}/audio/gen-1").mock(return_value=Response(200, content=AUDIO))

        import voicebox_client

        await voicebox_client.synthesize("Hola")

        body = json.loads(generate.calls[0].request.content)
        assert body["profile_id"] == PROFILE_ID
        assert body["text"] == "Hola"
        assert body["language"] == "es", "VoiceBox defaults this to 'en'"
        assert body["model_size"] == "0.6B", "VoiceBox defaults this to the unusable 1.7B"
        assert body["engine"] == "qwen"

    @respx.mock
    @pytest.mark.asyncio
    async def test_personality_rewrite_is_disabled(self):
        """`personality: true` makes VoiceBox rewrite the text in character.

        The safety gate already judged the exact words; letting the engine rewrite them afterwards
        would put unreviewed text in Tatiana's cloned voice.
        """
        generate = respx.post(f"{VOICEBOX_URL}/generate").mock(
            return_value=Response(200, json={"id": "gen-1", "status": "completed"})
        )
        respx.get(f"{VOICEBOX_URL}/audio/gen-1").mock(return_value=Response(200, content=AUDIO))

        import voicebox_client

        await voicebox_client.synthesize("Hola")

        assert json.loads(generate.calls[0].request.content)["personality"] is False

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_when_profile_id_is_empty(self, monkeypatch):
        """Never guess a profile id — a wrong one would speak in someone else's voice."""
        monkeypatch.setattr(settings, "VOICEBOX_PROFILE_ID", "")
        route = respx.post(f"{VOICEBOX_URL}/generate").mock(return_value=Response(200, json={}))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None
        assert not route.called, "must not call VoiceBox without a profile"

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_when_response_carries_an_error(self):
        """A 200 with a non-empty `error` is a FAILED generation, not a success."""
        respx.post(f"{VOICEBOX_URL}/generate").mock(
            return_value=Response(
                200, json={"id": "gen-1", "status": "failed", "error": "engine unavailable"}
            )
        )
        audio = respx.get(f"{VOICEBOX_URL}/audio/gen-1").mock(
            return_value=Response(200, content=AUDIO)
        )

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None
        assert not audio.called, "must not fetch audio for a failed generation"

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_when_generate_has_no_id(self):
        respx.post(f"{VOICEBOX_URL}/generate").mock(return_value=Response(200, json={}))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_on_generate_non_200(self):
        respx.post(f"{VOICEBOX_URL}/generate").mock(return_value=Response(422, json={"detail": "x"}))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_on_audio_fetch_non_200(self):
        respx.post(f"{VOICEBOX_URL}/generate").mock(
            return_value=Response(200, json={"id": "gen-1", "status": "completed"})
        )
        respx.get(f"{VOICEBOX_URL}/audio/gen-1").mock(return_value=Response(404))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_on_empty_audio(self):
        respx.post(f"{VOICEBOX_URL}/generate").mock(
            return_value=Response(200, json={"id": "gen-1", "status": "completed"})
        )
        respx.get(f"{VOICEBOX_URL}/audio/gen-1").mock(return_value=Response(200, content=b""))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_never_raises_when_voicebox_is_down(self):
        """The normal state on a machine without the inference node: nothing listening on 17493."""
        respx.post(f"{VOICEBOX_URL}/generate").mock(side_effect=httpx.ConnectError("refused"))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_never_raises_on_timeout(self):
        respx.post(f"{VOICEBOX_URL}/generate").mock(side_effect=httpx.ReadTimeout("too slow"))

        import voicebox_client

        assert await voicebox_client.synthesize("Hola") is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_returns_none_for_blank_text(self):
        route = respx.post(f"{VOICEBOX_URL}/generate").mock(return_value=Response(200, json={}))

        import voicebox_client

        assert await voicebox_client.synthesize("   ") is None
        assert not route.called
