"""Tests for GET / health check (Task 10.3).

Covers specs/chatwoot-hermes-bridge/spec.md's "Health check reflects Hermes
Gateway reachability" requirement / "Health check succeeds" scenario: the
endpoint must return HTTP 200 with a JSON body identifying the service, and
it must actually invoke hermes_client.check_models() (not just claim to in
prose) so a bad Hermes profile is visible in logs.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.fixture
def app_and_client():
    import main as main_module

    transport = httpx.ASGITransport(app=main_module.app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    return main_module, client


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_succeeds_and_invokes_hermes_liveness_check(
        self, app_and_client
    ):
        main_module, client = app_and_client
        fake_models = {"data": [{"id": "some-model"}]}
        with patch.object(
            main_module.hermes_client,
            "check_models",
            new_callable=AsyncMock,
            return_value=fake_models,
        ) as mock_check_models:
            async with client as c:
                response = await c.get("/")

        assert response.status_code == 200
        body = response.json()
        assert body["service"] == "chatwoot-hermes-bridge"
        assert body["status"] == "ok"
        assert body["hermes_models"] == fake_models
        mock_check_models.assert_awaited_once_with()
