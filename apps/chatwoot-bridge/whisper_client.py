"""Client for a local Whisper transcription server (taty-voice-outbound-calls, Task 3).

Mirrors `voicebox_client.py`'s shape and fail-soft contract: `LOCAL_WHISPER_URL` has existed since
`voicebox-local-voice-adoption` as a documented, unused placeholder (ARCHITECTURE.md Decisión #24,
"Fuera de alcance": "el micrófono... `LOCAL_WHISPER_URL` sigue siendo un placeholder documentado y
sin usar"). This module is the first to actually point it at a running instance and call it.

Standing up a real local Whisper server is a founder/infra action outside this repo's scope for
this session — this module only provides the calling code so the qualification flow (Task 4) has
a real function to invoke once that server exists.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _timeout() -> httpx.Timeout:
    return httpx.Timeout(60.0, connect=5.0)


async def transcribe(audio_bytes: bytes, mime_type: str = "audio/wav") -> Optional[str]:
    """Posts recorded call-response audio to `LOCAL_WHISPER_URL` and returns the transcript.

    Returns None on any failure or misconfiguration — never raises, matching
    `voicebox_client.synthesize`'s fail-soft contract, since a missed transcription should not
    crash the call flow calling this.
    """
    if not audio_bytes:
        logger.warning("whisper_client: refusing to transcribe empty audio")
        return None

    if not settings.LOCAL_WHISPER_URL:
        logger.warning("whisper_client: LOCAL_WHISPER_URL is not set; transcription unavailable")
        return None

    url = settings.LOCAL_WHISPER_URL.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.post(
                url,
                files={"audio": ("audio", audio_bytes, mime_type)},
            )
            if response.status_code != 200:
                logger.error(
                    "whisper_client: transcription server returned %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None

            body = response.json() or {}
            transcript = body.get("text")
            if not transcript:
                logger.error("whisper_client: response had no 'text' field")
                return None

            return transcript
    except Exception:
        # Includes the ordinary case of no local Whisper server configured/running yet.
        logger.exception("whisper_client: transcription failed")
        return None
