"""Client for the local VoiceBox speech server (voicebox-local-voice-adoption).

Synthesis runs HERE, on the local node, not on Railway. The model, the cloned voice profile and the
customer's reply text never leave this machine — the same data-sovereignty principle that keeps
Hermes, GBrain and the Siigo/Gmail pollers local (ARCHITECTURE.md Decisiones #1/#10/#20/#22). Only
the finished audio bytes are handed to the backend, which performs the Graph API delivery Railway
can reach and the bridge cannot.

The two-call flow
-----------------
Verified against the running server's own OpenAPI document on 2026-09-08, not the README:

    POST /generate            -> GenerationResponse (JSON: id, status, error, audio_path...)
    GET  /audio/{id}          -> the audio bytes

`POST /generate` does NOT return audio. And two of its request defaults are wrong for Contexia:
`language` defaults to `en`, and `model_size` defaults to `1.7B` — the model Phase 0 measured at
30-60 minutes per phrase on CPU. Both are always sent explicitly below.

Fail-soft contract, identical to `backend_client.whatsapp_intake`: every failure path returns None
and logs. Nothing here raises. The text reply has already reached the customer by the time this is
called, so a missing voice note is a non-event; an exception escaping into the reply pipeline would
not be.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _timeout() -> httpx.Timeout:
    """Generation is slow (minutes on CPU, seconds on GPU) while connecting is not.

    A single flat timeout would either abort real generations or hang on a dead port.
    """
    return httpx.Timeout(float(settings.VOICEBOX_TIMEOUT_SECONDS), connect=5.0)


def _generation_request(text: str) -> dict[str, Any]:
    return {
        "profile_id": settings.VOICEBOX_PROFILE_ID,
        "text": text,
        # Both explicit: VoiceBox's own defaults ("en", "1.7B") are wrong for this product.
        "language": settings.VOICEBOX_LANGUAGE,
        "engine": settings.VOICEBOX_ENGINE,
        "model_size": settings.VOICEBOX_MODEL_SIZE,
        # `personality: true` makes VoiceBox rewrite the text in character. The backend's safety
        # gate judged these exact words; letting the engine rewrite them afterwards would put
        # unreviewed text into Tatiana's cloned voice.
        "personality": False,
    }


async def synthesize(text: str) -> Optional[bytes]:
    """Render `text` as audio in the configured cloned voice. Returns None on any failure."""
    if not text or not text.strip():
        logger.warning("voicebox: refusing to synthesize empty text")
        return None

    if not settings.VOICEBOX_PROFILE_ID:
        # Never guess: a wrong profile id speaks in someone else's voice.
        logger.warning("voicebox: VOICEBOX_PROFILE_ID is not set; voice unavailable")
        return None

    base = settings.VOICEBOX_URL.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=_timeout()) as client:
            response = await client.post(f"{base}/generate", json=_generation_request(text))
            if response.status_code != 200:
                logger.error(
                    "voicebox /generate returned %s: %s", response.status_code, response.text[:200]
                )
                return None

            generation = response.json() or {}

            # A 200 carrying `error` is a FAILED generation. Treating it as success would fetch
            # audio for a generation that produced none.
            if generation.get("error"):
                logger.error("voicebox generation failed: %s", generation["error"])
                return None

            generation_id = generation.get("id")
            if not generation_id:
                logger.error("voicebox /generate returned 200 without an 'id'")
                return None

            audio_response = await client.get(f"{base}/audio/{generation_id}")
            if audio_response.status_code != 200:
                logger.error(
                    "voicebox /audio/%s returned %s", generation_id, audio_response.status_code
                )
                return None

            audio = audio_response.content
            if not audio:
                logger.error("voicebox /audio/%s returned no bytes", generation_id)
                return None

            return audio
    except Exception:
        # Includes the ordinary case on a machine without the inference node: nothing listening on
        # 17493. Logged, never raised.
        logger.exception("voicebox synthesis failed")
        return None
