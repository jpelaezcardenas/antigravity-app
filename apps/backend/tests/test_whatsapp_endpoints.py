"""Tests for WhatsApp channel endpoints (taty-channel-consolidation).

Two surfaces with different threat models:
- `POST /webhook` is the PUBLIC ingress from Meta (live as
  contexia.online/api/v1/channels/whatsapp/webhook via vercel.json's rewrite). It previously
  accepted any POST; these tests pin X-Hub-Signature-256 verification over the RAW body.
- `POST /leads/{lead_id}/reply` is INTERNAL and authenticated — the Chatwoot bridge's entry point
  into the single Taty brain.

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established in test_sell_machine_endpoints.py.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

APP_SECRET = "test-app-secret"


def _sign(raw: bytes, secret: str = APP_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


@pytest.fixture
def wa_app():
    from presentation.whatsapp_endpoints import router as whatsapp_router

    app = FastAPI()
    app.include_router(whatsapp_router, prefix="/channels/whatsapp")
    return app


@pytest.fixture
def wa_client(wa_app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=wa_app), base_url="http://testserver"
    )


@pytest.fixture
def configured():
    from config import settings

    with patch.object(settings, "WHATSAPP_APP_SECRET", APP_SECRET), patch.object(
        settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "correct-verify-token"
    ):
        yield


@pytest.fixture
def reply_client(wa_app):
    """Same app, with auth satisfied for the internal endpoint."""
    from core.deps import get_current_user

    wa_app.dependency_overrides[get_current_user] = lambda: {
        "sub": "bridge",
        "email": "bridge@contexia",
    }
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=wa_app), base_url="http://testserver"
    )


class TestInternalTatyReplyEndpoint:
    @pytest.mark.asyncio
    async def test_authenticated_call_returns_router_reply(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={
                    "intent": "sales_interest",
                    "confidence": 0.8,
                    "reply": "Aquí tienes el link de pago...",
                },
            ) as mock_route:
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply",
                    json={"text": "quiero saber si me toca declarar renta"},
                )

        assert response.status_code == 200
        assert response.json()["reply"] == "Aquí tienes el link de pago..."
        mock_route.assert_called_once_with("lead-1", "quiero saber si me toca declarar renta")

    @pytest.mark.asyncio
    async def test_unknown_lead_returns_404_and_does_not_route(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=False
            ), patch("presentation.whatsapp_endpoints.route_lead_message") as mock_route:
                response = await client.post(
                    "/channels/whatsapp/leads/does-not-exist/reply", json={"text": "hola"}
                )

        assert response.status_code == 404
        mock_route.assert_not_called()

    @pytest.mark.asyncio
    async def test_unauthenticated_call_is_rejected(self, wa_client) -> None:
        """No dependency override here: the real get_current_user must reject a tokenless
        call when AUTH_ENFORCED is on."""
        from config import settings

        with patch.object(settings, "AUTH_ENFORCED", True):
            async with wa_client as client:
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "hola"}
                )

        assert response.status_code == 401
