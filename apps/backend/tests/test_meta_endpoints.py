"""Tests for the Meta social webhook (taty-channel-consolidation, section 5).

This endpoint feeds Social Content Ops with Instagram/Facebook events — it is NOT a WhatsApp
receiver (channels/meta.py discards anything that is not facebook/instagram). It was public and
unauthenticated with a hardcoded default verify token; these tests pin the two controls that
close that: X-Hub-Signature-256 over the RAW body, and fail-closed verify tokens.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

APP_SECRET = "test-app-secret"


def _sign(raw: bytes, secret: str = APP_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


@pytest.fixture
def meta_client():
    from presentation.meta_endpoints import router as meta_router

    app = FastAPI()
    app.include_router(meta_router, prefix="/channels/meta")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def configured():
    """App secret + verify token present."""
    from config import settings

    with patch.object(settings, "META_APP_SECRET", APP_SECRET), patch.object(
        settings, "META_WEBHOOK_VERIFY_TOKEN", "correct-verify-token"
    ):
        yield


class TestSignatureVerification:
    @pytest.mark.asyncio
    async def test_correctly_signed_payload_is_processed(self, meta_client, configured) -> None:
        raw = json.dumps({"object": "instagram", "entry": []}).encode()

        async with meta_client as client:
            with patch(
                "presentation.meta_endpoints.normalize_meta_webhook", return_value=[{"a": 1}]
            ), patch(
                "presentation.meta_endpoints.get_social_ops_service", return_value=MagicMock()
            ):
                response = await client.post(
                    "/channels/meta/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 200
        assert response.json()["events_ingested"] == 1

    @pytest.mark.asyncio
    async def test_missing_signature_is_rejected_without_ingesting(
        self, meta_client, configured
    ) -> None:
        raw = json.dumps({"object": "instagram", "entry": []}).encode()

        async with meta_client as client:
            with patch(
                "presentation.meta_endpoints.normalize_meta_webhook"
            ) as mock_normalize:
                response = await client.post(
                    "/channels/meta/webhook",
                    content=raw,
                    headers={"Content-Type": "application/json"},
                )

        assert response.status_code == 403
        mock_normalize.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrong_signature_is_rejected(self, meta_client, configured) -> None:
        raw = json.dumps({"object": "instagram", "entry": []}).encode()

        async with meta_client as client:
            with patch("presentation.meta_endpoints.normalize_meta_webhook") as mock_normalize:
                response = await client.post(
                    "/channels/meta/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw, "attacker-secret"),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 403
        mock_normalize.assert_not_called()

    @pytest.mark.asyncio
    async def test_verification_uses_raw_bytes_not_reserialized_json(
        self, meta_client, configured
    ) -> None:
        """Non-canonical key order and whitespace must still verify. If the handler parsed the
        body and re-serialized it before hashing, this signature would never match."""
        raw = b'{"entry":   [],   "object": "instagram"}'

        async with meta_client as client:
            with patch(
                "presentation.meta_endpoints.normalize_meta_webhook", return_value=[]
            ), patch(
                "presentation.meta_endpoints.get_social_ops_service", return_value=MagicMock()
            ):
                response = await client.post(
                    "/channels/meta/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unconfigured_app_secret_rejects_everything(self, meta_client) -> None:
        from config import settings

        raw = json.dumps({"object": "instagram", "entry": []}).encode()

        async with meta_client as client:
            with patch.object(settings, "META_APP_SECRET", ""), patch(
                "presentation.meta_endpoints.normalize_meta_webhook"
            ) as mock_normalize:
                response = await client.post(
                    "/channels/meta/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 403
        mock_normalize.assert_not_called()


class TestVerifyTokenFailsClosed:
    @pytest.mark.asyncio
    async def test_valid_token_echoes_challenge(self, meta_client, configured) -> None:
        async with meta_client as client:
            response = await client.get(
                "/channels/meta/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "correct-verify-token",
                    "hub.challenge": "12345",
                },
            )

        assert response.status_code == 200
        assert response.text == "12345"

    @pytest.mark.asyncio
    async def test_unconfigured_verify_token_rejects_handshake(self, meta_client) -> None:
        """No hardcoded default may be accepted."""
        from config import settings

        async with meta_client as client:
            with patch.object(settings, "META_WEBHOOK_VERIFY_TOKEN", ""):
                response = await client.get(
                    "/channels/meta/webhook",
                    params={
                        "hub.mode": "subscribe",
                        "hub.verify_token": "contexia-meta-webhook",
                        "hub.challenge": "12345",
                    },
                )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_wrong_token_rejected(self, meta_client, configured) -> None:
        async with meta_client as client:
            response = await client.get(
                "/channels/meta/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong",
                    "hub.challenge": "12345",
                },
            )

        assert response.status_code == 403
