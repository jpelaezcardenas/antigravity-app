"""WAV to OGG/Opus conversion for WhatsApp voice notes (voicebox-local-voice-adoption).

WhatsApp plays voice notes as OGG/Opus. A WAV uploads to the Graph API without complaint and then
silently fails to play on the customer's phone, so this step is not cosmetic — it is the difference
between a voice note and nothing.

VoiceBox returns WAV; Meta wants Opus in an Ogg container, mono, 48 kHz. ffmpeg does the encode.

Fail-soft like every other step in this pipeline: a missing ffmpeg, an unencodable input or a
non-zero exit returns None and logs. The text reply has already been delivered by the time this
runs, so the worst outcome of a failure here is a reply without audio.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# WhatsApp voice notes: Opus, mono, 48 kHz. 32 kbit/s is comfortably transparent for speech and
# keeps a short note well inside Meta's audio size limit.
_OPUS_BITRATE = "32k"
_SAMPLE_RATE = "48000"
_CHANNELS = "1"

_CONVERSION_TIMEOUT_SECONDS = 60


def ffmpeg_path() -> Optional[str]:
    """Resolve the ffmpeg binary, honouring an explicit FFMPEG_BINARY override.

    Separate function so tests can simulate a host without ffmpeg by patching the environment
    rather than the conversion itself.
    """
    return os.environ.get("FFMPEG_BINARY") or shutil.which("ffmpeg")


def wav_to_ogg_opus(wav_bytes: bytes) -> Optional[bytes]:
    """Encode WAV bytes as OGG/Opus. Returns None on any failure; never raises."""
    if not wav_bytes:
        logger.warning("audio_converter: no input bytes")
        return None

    binary = ffmpeg_path()
    if not binary:
        logger.warning("audio_converter: ffmpeg not found; voice notes unavailable on this host")
        return None

    # Temp files rather than pipes: ffmpeg needs to seek the WAV header, which a stdin pipe cannot
    # do, and Ogg muxing wants a seekable output.
    input_path = output_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as source:
            source.write(wav_bytes)
            input_path = source.name
        output_path = input_path[: -len(".wav")] + ".ogg"

        result = subprocess.run(
            [
                binary,
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-i", input_path,
                "-c:a", "libopus",
                "-b:a", _OPUS_BITRATE,
                "-ar", _SAMPLE_RATE,
                "-ac", _CHANNELS,
                output_path,
            ],
            capture_output=True,
            timeout=_CONVERSION_TIMEOUT_SECONDS,
        )

        if result.returncode != 0:
            logger.error(
                "audio_converter: ffmpeg exited %s: %s",
                result.returncode,
                result.stderr.decode("utf-8", "replace")[:300],
            )
            return None

        with open(output_path, "rb") as encoded:
            audio = encoded.read()

        if not audio:
            logger.error("audio_converter: ffmpeg produced an empty file")
            return None

        return audio
    except Exception:
        logger.exception("audio_converter: conversion failed")
        return None
    finally:
        for path in (input_path, output_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    logger.warning("audio_converter: could not remove temp file %s", path)
