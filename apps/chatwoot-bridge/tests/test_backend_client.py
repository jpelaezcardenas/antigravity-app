"""Tests for backend_client.py (Task Group 9): tenant JWT signing matching the
Hermes-operator contract, lead intake, fail-soft on any failure. All HTTP
mocked with respx."""

from __future__ import annotations

import json

import httpx
import respx
import pytest
from httpx import Response
from jose import jwt

from config import settings

BACKEND_URL = "http://127.0.0.1:8080/api/v1"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "CONTEXIA_API_URL", BACKEND_URL)
    monkeypatch.setattr(settings, "CONTEXIA_JWT_SECRET", "shared-test-secret-1234567890")


class TestSignTenantJwt:
    def test_jwt_has_sub_tenant_id_and_exp_claims(self):
        import backend_client

        token = backend_client.sign_tenant_jwt()
        payload = jwt.decode(
            token, "shared-test-secret-1234567890", algorithms=["HS256"]
        )

        assert payload["sub"] == "chatwoot-bridge"
        assert "tenant_id" in payload
        assert payload["tenant_id"]
        assert "exp" in payload

    def test_jwt_is_signed_hs256(self):
        import backend_client

        token = backend_client.sign_tenant_jwt()
        header = jwt.get_unverified_header(token)

        assert header["alg"] == "HS256"


class TestWhatsappIntake:
    @respx.mock
    @pytest.mark.asyncio
    async def test_maps_response_correctly(self):
        import backend_client

        route = respx.post(f"{BACKEND_URL}/crm/leads/whatsapp-intake").mock(
            return_value=Response(
                200, json={"lead_id": "abc", "is_new": True, "stage": "NUEVOS"}
            )
        )

        result = await backend_client.whatsapp_intake("+573001234567")

        assert result == {"lead_id": "abc", "is_new": True, "stage": "NUEVOS"}
        request = route.calls[0].request
        assert request.headers["authorization"].startswith("Bearer ")
        body = json.loads(request.content)
        assert body == {"whatsapp_phone": "+573001234567"}

    @respx.mock
    @pytest.mark.asyncio
    async def test_network_failure_returns_none_without_raising(self):
        import backend_client

        respx.post(f"{BACKEND_URL}/crm/leads/whatsapp-intake").mock(
            side_effect=httpx.ConnectError("refused")
        )

        result = await backend_client.whatsapp_intake("+573001234567")

        assert result is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_non_200_returns_none_without_raising(self):
        import backend_client

        respx.post(f"{BACKEND_URL}/crm/leads/whatsapp-intake").mock(
            return_value=Response(500, json={"error": "boom"})
        )

        result = await backend_client.whatsapp_intake("+573001234567")

        assert result is None
