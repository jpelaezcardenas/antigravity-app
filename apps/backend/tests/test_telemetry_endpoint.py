"""
Tests for the telemetry report endpoint (sell-machine-telemetry-loop, Change G).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established throughout the Sell Machine test suites. This
route lives in presentation/sell_machine_endpoints.py (extended, not a new module — reuses the
already-live SELL_MACHINE_CANONICAL flag, same as Change F).
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def sm_client():
    from presentation.sell_machine_endpoints import router as sell_machine_router

    app = FastAPI()
    app.include_router(sell_machine_router, prefix="/sell-machine")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestTelemetryReportEndpoint:
    @pytest.mark.asyncio
    async def test_returns_the_report_shape(self, sm_client) -> None:
        fake_report = {
            "hook_performance": {"post_content": {"count": 2, "impressions": 500}},
            "funnel_snapshot": {"NUEVOS": 3, "PROSPECTOS": 1, "POR_APROBAR": 0, "LISTOS_CONTADORA": 0},
            "generated_at": "2026-07-20T00:00:00+00:00",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.get_telemetry_report", return_value=fake_report
            ):
                response = await client.get("/sell-machine/telemetry/report")

        assert response.status_code == 200
        body = response.json()
        assert body["hook_performance"]["post_content"]["count"] == 2
        assert body["funnel_snapshot"]["NUEVOS"] == 3
        assert "generated_at" in body

    @pytest.mark.asyncio
    async def test_returns_200_with_an_empty_report(self, sm_client) -> None:
        empty_report = {
            "hook_performance": {"post_content": {"count": 0}, "run_ads_ab": {"count": 0}},
            "funnel_snapshot": {"NUEVOS": 0, "PROSPECTOS": 0, "POR_APROBAR": 0, "LISTOS_CONTADORA": 0},
            "generated_at": "2026-07-20T00:00:00+00:00",
        }
        async with sm_client as client:
            with patch(
                "presentation.sell_machine_endpoints.get_telemetry_report", return_value=empty_report
            ):
                response = await client.get("/sell-machine/telemetry/report")

        assert response.status_code == 200
        assert response.json()["hook_performance"]["post_content"]["count"] == 0
