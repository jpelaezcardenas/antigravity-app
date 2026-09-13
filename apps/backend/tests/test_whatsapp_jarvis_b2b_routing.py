"""Tests for D2 (hermes-jarvis-contexia, 2026-09-13): a Growth/Enterprise B2B client writing
on the same WhatsApp number Taty already answers gets proxied to Hermes ("deeper brain for
whoever pays for it") instead of the B2C Renta Natural lead flow. Every other case -- no
b2b_clients phone match, a freemium/starter B2B client, or a Hermes call failure -- falls
through to the exact pre-existing route_lead_message() behavior, unchanged.

Same isolated-app + ASGITransport pattern as test_whatsapp_endpoints.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def wa_app():
    from presentation.whatsapp_endpoints import router as whatsapp_router

    app = FastAPI()
    app.include_router(whatsapp_router, prefix="/channels/whatsapp")
    return app


@pytest.fixture
def reply_client(wa_app):
    from core.deps import get_current_user

    wa_app.dependency_overrides[get_current_user] = lambda: {
        "sub": "bridge",
        "email": "bridge@contexia",
    }
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=wa_app), base_url="http://testserver"
    )


class TestJarvisB2bWhatsappRouting:
    @pytest.mark.asyncio
    async def test_growth_tenant_match_proxies_to_hermes_not_taty(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.get_lead_phone", return_value="573001234567"
            ), patch(
                "presentation.whatsapp_endpoints.resolve_b2b_tenant_for_whatsapp_phone",
                return_value=("tenant-growth-1", "growth"),
            ), patch(
                "presentation.whatsapp_endpoints._call_hermes_for_whatsapp",
                new=AsyncMock(return_value="Tu caja real hoy está sana."),
            ) as mock_hermes, patch(
                "presentation.whatsapp_endpoints.route_lead_message"
            ) as mock_route, patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ):
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply",
                    json={"text": "¿cómo va mi caja?"},
                )

        assert response.status_code == 200
        assert response.json()["reply"] == "Tu caja real hoy está sana."
        mock_hermes.assert_awaited_once_with("¿cómo va mi caja?")
        mock_route.assert_not_called()

    @pytest.mark.asyncio
    async def test_enterprise_tenant_match_also_proxies_to_hermes(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.get_lead_phone", return_value="573001234567"
            ), patch(
                "presentation.whatsapp_endpoints.resolve_b2b_tenant_for_whatsapp_phone",
                return_value=("tenant-ent-1", "enterprise"),
            ), patch(
                "presentation.whatsapp_endpoints._call_hermes_for_whatsapp",
                new=AsyncMock(return_value="Respuesta de Hermes."),
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message"
            ) as mock_route, patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ):
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "hola"}
                )

        assert response.status_code == 200
        mock_route.assert_not_called()

    @pytest.mark.asyncio
    async def test_starter_tenant_match_falls_through_to_taty_unchanged(self, reply_client) -> None:
        """has_feature gate: a matched B2B client without jarvis_chat on their plan must still
        get the exact existing Taty flow -- a phone match alone is not enough."""
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.get_lead_phone", return_value="573001234567"
            ), patch(
                "presentation.whatsapp_endpoints.resolve_b2b_tenant_for_whatsapp_phone",
                return_value=("tenant-starter-1", "starter"),
            ), patch(
                "presentation.whatsapp_endpoints._call_hermes_for_whatsapp",
                new=AsyncMock(),
            ) as mock_hermes, patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={"intent": "unknown", "confidence": 0.0, "reply": "Hola de Taty"},
            ) as mock_route, patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ):
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "hola"}
                )

        assert response.status_code == 200
        assert response.json()["reply"] == "Hola de Taty"
        mock_hermes.assert_not_called()
        mock_route.assert_called_once_with("lead-1", "hola", history=None)

    @pytest.mark.asyncio
    async def test_no_b2b_match_falls_through_to_taty_unchanged(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.get_lead_phone", return_value="573001234567"
            ), patch(
                "presentation.whatsapp_endpoints.resolve_b2b_tenant_for_whatsapp_phone",
                return_value=None,
            ), patch(
                "presentation.whatsapp_endpoints._call_hermes_for_whatsapp",
                new=AsyncMock(),
            ) as mock_hermes, patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={"intent": "sales_interest", "confidence": 0.8, "reply": "..."},
            ) as mock_route, patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ):
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "quiero pagar"}
                )

        assert response.status_code == 200
        mock_hermes.assert_not_called()
        mock_route.assert_called_once_with("lead-1", "quiero pagar", history=None)

    @pytest.mark.asyncio
    async def test_no_phone_on_file_skips_b2b_lookup_entirely(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.get_lead_phone", return_value=None
            ), patch(
                "presentation.whatsapp_endpoints.resolve_b2b_tenant_for_whatsapp_phone"
            ) as mock_lookup, patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={"intent": "unknown", "confidence": 0.0, "reply": "Hola"},
            ):
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "hola"}
                )

        assert response.status_code == 200
        mock_lookup.assert_not_called()

    @pytest.mark.asyncio
    async def test_hermes_failure_gracefully_falls_back_to_taty(self, reply_client) -> None:
        """A Hermes-side failure (gateway offline, timeout, etc.) must never 500 the request or
        leave the client without a reply -- fall back to the existing Taty flow instead."""
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.get_lead_phone", return_value="573001234567"
            ), patch(
                "presentation.whatsapp_endpoints.resolve_b2b_tenant_for_whatsapp_phone",
                return_value=("tenant-growth-1", "growth"),
            ), patch(
                "presentation.whatsapp_endpoints._call_hermes_for_whatsapp",
                new=AsyncMock(side_effect=RuntimeError("Hermes gateway unreachable")),
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={"intent": "unknown", "confidence": 0.0, "reply": "Hola de Taty"},
            ) as mock_route, patch(
                "presentation.whatsapp_endpoints.send_whatsapp_message",
                new=AsyncMock(return_value=True),
            ):
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "hola"}
                )

        assert response.status_code == 200
        assert response.json()["reply"] == "Hola de Taty"
        mock_route.assert_called_once_with("lead-1", "hola", history=None)
