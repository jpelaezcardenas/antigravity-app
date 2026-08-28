"""
Tests for POST /agents/pulso-diario/insights (pulso-diario-agent-insight-bridge).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)), service layer mocked —
same pattern as test_operator_task_endpoints.py. `require_hermes_bridge_token` is imported from
presentation.sell_machine_endpoints and reused as-is.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def pulso_client():
    from presentation.pulso_diario_endpoints import router as pulso_diario_router

    app = FastAPI()
    app.include_router(pulso_diario_router, prefix="/agents/pulso-diario")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


PAYLOAD = {
    "tenant_id": "tenant-1",
    "caja_real": 500_000,
    "dinero_disponible": 500_000,
    "ventas_ayer": 0,
    "gastos_ayer": 0,
}


class TestPostPulsoDiarioInsight:
    @pytest.mark.asyncio
    async def test_valid_token_creates_insight(self, pulso_client) -> None:
        async with pulso_client as client:
            with patch(
                "presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"
            ), patch(
                "presentation.pulso_diario_endpoints.submit_completed_insight",
                return_value=(True, {"id": "task-1", "status": "completed"}, None),
            ) as mock_submit:
                response = await client.post(
                    "/agents/pulso-diario/insights",
                    json=PAYLOAD,
                    headers={"Authorization": "Bearer secret-token"},
                )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        mock_submit.assert_called_once()
        call_kwargs = mock_submit.call_args.kwargs
        assert call_kwargs["tenant_id"] == "tenant-1"
        assert call_kwargs["result"]["caja_real"] == 500_000

    @pytest.mark.asyncio
    async def test_missing_token_is_rejected(self, pulso_client) -> None:
        async with pulso_client as client:
            with patch(
                "presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"
            ), patch(
                "presentation.pulso_diario_endpoints.submit_completed_insight"
            ) as mock_submit:
                response = await client.post("/agents/pulso-diario/insights", json=PAYLOAD)

        assert response.status_code == 401
        mock_submit.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrong_token_is_rejected(self, pulso_client) -> None:
        async with pulso_client as client:
            with patch(
                "presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"
            ), patch(
                "presentation.pulso_diario_endpoints.submit_completed_insight"
            ) as mock_submit:
                response = await client.post(
                    "/agents/pulso-diario/insights",
                    json=PAYLOAD,
                    headers={"Authorization": "Bearer wrong-token"},
                )

        assert response.status_code == 401
        mock_submit.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_tenant_returns_400(self, pulso_client) -> None:
        async with pulso_client as client:
            with patch(
                "presentation.sell_machine_endpoints.settings.HERMES_BRIDGE_TOKEN", "secret-token"
            ), patch(
                "presentation.pulso_diario_endpoints.submit_completed_insight",
                return_value=(False, None, "tenant unknown-tenant not found"),
            ):
                response = await client.post(
                    "/agents/pulso-diario/insights",
                    json={**PAYLOAD, "tenant_id": "unknown-tenant"},
                    headers={"Authorization": "Bearer secret-token"},
                )

        assert response.status_code == 400
