"""
Tests for Sell Machine endpoints (sell-machine-creative-swarm, Change E).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established in test_crm_endpoints.py / test_crm_b2c_endpoints.py
(the sync fastapi.testclient.TestClient is broken by a pre-existing httpx>=0.28/starlette 0.27
mismatch in this environment).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI


class TestSellMachineCanonicalFeatureFlag:
    def test_flag_exists_and_defaults_to_false(self) -> None:
        from config import settings

        assert hasattr(settings, "SELL_MACHINE_CANONICAL")
        assert settings.SELL_MACHINE_CANONICAL is False

    def test_router_conditionally_included_on_flag(self) -> None:
        with open("presentation/router.py", "r", encoding="utf-8") as f:
            router_code = f.read()

        assert "if settings.SELL_MACHINE_CANONICAL:" in router_code
        assert 'prefix="/sell-machine"' in router_code


@pytest.fixture
def sm_client():
    from presentation.sell_machine_endpoints import router as sell_machine_router

    app = FastAPI()
    app.include_router(sell_machine_router, prefix="/sell-machine")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestGenerateHooksEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_and_expected_shape(self, sm_client) -> None:
        fake_hooks = [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]
        async with sm_client as client:
            with patch("presentation.sell_machine_endpoints.generate_hooks", return_value=fake_hooks):
                response = await client.post("/sell-machine/hooks/generate", json={"count": 1})

        assert response.status_code == 200
        assert response.json()["hooks"][0]["headline"] == "H"


class TestEvaluateHooksEndpoint:
    @pytest.mark.asyncio
    async def test_returns_survivors(self, sm_client) -> None:
        survivors = [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]
        async with sm_client as client:
            with patch("presentation.sell_machine_endpoints.evaluate_hooks", return_value=survivors):
                response = await client.post(
                    "/sell-machine/hooks/evaluate",
                    json={"hooks": [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]},
                )

        assert response.status_code == 200
        assert len(response.json()["survivors"]) == 1


class TestCreativeLoopRunEndpoint:
    @pytest.mark.asyncio
    async def test_returns_survivors_from_the_telemetry_aware_loop(self, sm_client) -> None:
        survivors = [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.run_creative_loop", return_value=survivors
            ) as mock_loop:
                response = await client.post(
                    "/sell-machine/creative-loop/run", json={"count": 3}
                )

        assert response.status_code == 200
        assert response.json()["survivors"] == survivors
        mock_loop.assert_called_once_with(count=3, target_segment=None, use_telemetry=True)

    @pytest.mark.asyncio
    async def test_passes_through_target_segment(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.run_creative_loop", return_value=[]
            ) as mock_loop:
                await client.post(
                    "/sell-machine/creative-loop/run",
                    json={"count": 2, "target_segment": "asalariados_renta_natural"},
                )

        mock_loop.assert_called_once_with(
            count=2, target_segment="asalariados_renta_natural", use_telemetry=True
        )

    @pytest.mark.asyncio
    async def test_defaults_count_when_omitted(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.run_creative_loop", return_value=[]
            ) as mock_loop:
                await client.post("/sell-machine/creative-loop/run", json={})

        mock_loop.assert_called_once_with(count=5, target_segment=None, use_telemetry=True)


class TestCreateCampaignEndpoint:
    @pytest.mark.asyncio
    async def test_creates_a_campaign_package(self, sm_client) -> None:
        fake_decision = {"id": "decision-1", "status": "pending_approval"}
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.create_campaign_package",
                return_value=fake_decision,
            ):
                response = await client.post(
                    "/sell-machine/campaigns",
                    json={
                        "hooks": [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}],
                        "brief": "brief",
                        "target_segment": "asalariados",
                        "budget": 500000,
                    },
                )

        assert response.status_code == 200
        assert response.json()["id"] == "decision-1"


class TestListCampaignsEndpoint:
    @pytest.mark.asyncio
    async def test_lists_campaigns(self, sm_client) -> None:
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.list_campaigns",
                return_value=[{"id": "decision-1"}],
            ):
                response = await client.get("/sell-machine/campaigns")

        assert response.status_code == 200
        assert response.json()[0]["id"] == "decision-1"
