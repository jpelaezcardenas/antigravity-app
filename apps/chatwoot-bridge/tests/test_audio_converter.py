"""Tests for audio_converter.py (voicebox-local-voice-adoption).

WhatsApp plays voice notes as OGG/Opus. A WAV uploads without complaint and then simply does not
play, so the conversion is not cosmetic.

These tests build a **real, valid WAV** with the standard library's `wave` module and hand it to
the real ffmpeg. ARCHITECTURE.md Decisión #22 recorded the alternative and why it is forbidden: a
previous change shipped two bugs to production behind tests whose inline fixture was invalid, which
*forced* the test to mock the very function it claimed to verify. A synthesised-but-genuine WAV
costs nothing and exercises the actual encoder.

`test_missing_ffmpeg_returns_none` is the one test that patches — and it patches the *environment*
(the resolved ffmpeg binary), not the function under test.
"""

from __future__ import annotations

import io
import math
import struct
import wave

import pytest

import audio_converter


def _real_wav(seconds: float = 0.25, rate: int = 16000, freq: float = 440.0) -> bytes:
    """A genuine mono 16-bit PCM WAV containing an audible sine tone."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        frames = bytearray()
        for i in range(int(rate * seconds)):
            sample = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / rate))
            frames += struct.pack("<h", sample)
        handle.writeframes(bytes(frames))
    return buffer.getvalue()


@pytest.fixture
def ffmpeg_or_skip():
    if not audio_converter.ffmpeg_path():
        pytest.skip("ffmpeg is not installed on this machine")


def test_converts_a_real_wav_to_ogg_opus(ffmpeg_or_skip):
    result = audio_converter.wav_to_ogg_opus(_real_wav())

    assert result, "conversion produced no bytes"
    assert result.startswith(b"OggS"), "output must be an Ogg container"
    assert b"OpusHead" in result[:200], "output must be Opus-encoded, not Vorbis or PCM"


def test_output_is_smaller_than_the_wav(ffmpeg_or_skip):
    """Sanity check that real encoding happened rather than a passthrough copy."""
    wav = _real_wav(seconds=1.0)
    result = audio_converter.wav_to_ogg_opus(wav)

    assert result is not None
    assert len(result) < len(wav)


def test_garbage_input_returns_none_without_raising(ffmpeg_or_skip):
    """ffmpeg exits non-zero on input that is not audio. That is a soft failure: no voice note."""
    assert audio_converter.wav_to_ogg_opus(b"this is definitely not a wav file") is None


def test_empty_input_returns_none():
    assert audio_converter.wav_to_ogg_opus(b"") is None


def test_missing_ffmpeg_returns_none(monkeypatch):
    """On a host without ffmpeg the bridge must degrade to text-only, not crash the reply path."""
    monkeypatch.setattr(audio_converter, "ffmpeg_path", lambda: None)

    assert audio_converter.wav_to_ogg_opus(_real_wav()) is None
