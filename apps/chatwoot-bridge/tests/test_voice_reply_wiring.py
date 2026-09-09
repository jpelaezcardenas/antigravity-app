"""The voice step inside process_incoming_message (voicebox-local-voice-adoption).

Voice is ADDITIVE. Every test here is really one assertion in different clothes: whatever the voice
path does — succeed, fail, be disabled, raise — the text reply must have been sent and the
conversation must be unaffected.

The dark-launch certification is `test_no_voice_work_happens_when_the_flag_is_off`: with
VOICE_ENABLED false, which is the shipped production state, VoiceBox must not be contacted at all.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

import main
from config import settings

_TATY_RESULT_SPEAKABLE = {
    "intent": "sales_interest",
    "confidence": 0.9,
    "reply": "Hola, soy Taty. Con gusto te ayudo.",
    "persona_fields": {},
    "voice_allowed": True,
}


@pytest.fixture
def voice_on(monkeypatch):
    monkeypatch.setattr(settings, "VOICE_ENABLED", True)


async def _run(taty_result, voice_patches=None):
    """Drive process_incoming_message with its collaborators faked, and return the voice mocks."""
    voice_patches = voice_patches or {}
    synthesize = voice_patches.get("synthesize", AsyncMock(return_value=b"RIFFfake-wav"))
    convert = voice_patches.get("convert", lambda _wav: b"OggSfake-opus")
    send_voice = voice_patches.get("send_voice", AsyncMock(return_value=True))
    send_reply = AsyncMock()

    with patch.object(main.backend_client, "whatsapp_intake", AsyncMock(
        return_value={"lead_id": "lead-1", "is_new": False, "stage": "NUEVOS"}
    )), patch.object(
        main.backend_client, "taty_reply", AsyncMock(return_value=taty_result)
    ), patch.object(
        main.chatwoot_client, "send_reply", send_reply
    ), patch.object(
        main.chatwoot_client, "set_contact_attributes", AsyncMock()
    ), patch.object(
        main.chatwoot_client, "set_conversation_attributes", AsyncMock()
    ), patch.object(
        main.voicebox_client, "synthesize", synthesize
    ), patch.object(
        main.audio_converter, "wav_to_ogg_opus", convert
    ), patch.object(
        main.backend_client, "send_voice_note", send_voice
    ):
        await main.process_incoming_message(
            conversation_id=1,
            content="hola",
            attachments=[],
            contact_id=7,
            phone="573001234567",
        )
        # The voice step is a fire-and-forget task; let it run before asserting.
        await asyncio.sleep(0)
        await asyncio.sleep(0)

    return {"synthesize": synthesize, "send_voice": send_voice, "send_reply": send_reply}


@pytest.mark.asyncio
async def test_no_voice_work_happens_when_the_flag_is_off(monkeypatch):
    """Dark-launch certification: production today must never contact VoiceBox."""
    monkeypatch.setattr(settings, "VOICE_ENABLED", False)

    mocks = await _run(_TATY_RESULT_SPEAKABLE)

    mocks["synthesize"].assert_not_awaited()
    mocks["send_voice"].assert_not_awaited()
    mocks["send_reply"].assert_awaited_once()


@pytest.mark.asyncio
async def test_no_voice_work_when_backend_says_not_allowed(voice_on):
    """The backend owns the verdict; the bridge must not second-guess it."""
    mocks = await _run(dict(_TATY_RESULT_SPEAKABLE, voice_allowed=False))

    mocks["synthesize"].assert_not_awaited()
    mocks["send_reply"].assert_awaited_once()


@pytest.mark.asyncio
async def test_missing_voice_allowed_field_is_treated_as_not_allowed(voice_on):
    """An older backend that does not send the field must not enable voice by accident."""
    result = {k: v for k, v in _TATY_RESULT_SPEAKABLE.items() if k != "voice_allowed"}
    mocks = await _run(result)

    mocks["synthesize"].assert_not_awaited()


@pytest.mark.asyncio
async def test_voice_is_sent_when_allowed_and_enabled(voice_on):
    mocks = await _run(_TATY_RESULT_SPEAKABLE)

    mocks["synthesize"].assert_awaited_once()
    mocks["send_voice"].assert_awaited_once()
    # And the text still went out first.
    mocks["send_reply"].assert_awaited_once()


@pytest.mark.asyncio
async def test_text_reply_survives_a_synthesis_failure(voice_on):
    mocks = await _run(
        _TATY_RESULT_SPEAKABLE, {"synthesize": AsyncMock(return_value=None)}
    )

    mocks["send_voice"].assert_not_awaited()
    mocks["send_reply"].assert_awaited_once()


@pytest.mark.asyncio
async def test_text_reply_survives_a_conversion_failure(voice_on):
    mocks = await _run(_TATY_RESULT_SPEAKABLE, {"convert": lambda _wav: None})

    mocks["send_voice"].assert_not_awaited()
    mocks["send_reply"].assert_awaited_once()


@pytest.mark.asyncio
async def test_text_reply_survives_a_raising_voice_path(voice_on):
    """Even an unexpected exception inside the voice task must stay contained."""
    mocks = await _run(
        _TATY_RESULT_SPEAKABLE,
        {"synthesize": AsyncMock(side_effect=RuntimeError("voicebox exploded"))},
    )

    mocks["send_reply"].assert_awaited_once()
