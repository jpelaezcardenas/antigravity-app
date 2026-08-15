"""
Tests for CRM B2B retainer endpoints (crm-b2b-retainers-cockpit, Change A).

Mirrors test_social_ops_endpoints.py's flag-check style. The endpoint-shape tests use an
isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) with the service
layer mocked — no network/credentials required.

Note: httpx>=0.28 dropped the `app=` shortcut that starlette 0.27's TestClient relies on,
breaking `fastapi.testclient.TestClient(app)` in this environment (pre-existing repo-wide
dependency mismatch, unrelated to this change). ASGITransport is async-only, so these tests
use httpx.AsyncClient + pytest.mark.asyncio (already used elsewhere in this repo, e.g.
test_mission_endpoints.py) rather than the sync TestClient wrapper.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI


class TestCrmCanonicalFeatureFlag:
    def test_crm_canonical_flag_exists_and_defaults_to_false(self) -> None:
        from config import settings

        assert hasattr(settings, "CRM_CANONICAL")
        assert settings.CRM_CANONICAL is False

    def test_crm_router_conditionally_included_on_flag(self) -> None:
        with open("presentation/router.py", "r", encoding="utf-8") as f:
            router_code = f.read()

        assert "if settings.CRM_CANONICAL:" in router_code
        assert 'prefix="/crm"' in router_code


@pytest.fixture
def crm_client():
    from presentation.crm_endpoints import router as crm_router

    app = FastAPI()
    app.include_router(crm_router, prefix="/crm")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestCrmB2bClientsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_and_expected_shape(self, crm_client) -> None:
        fake_result = {
            "source": "supabase",
            "items": [{"id": "c1", "name": "Medic", "status": "activo", "monthly_fee_cents": None}],
        }
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.list_b2b_clients.return_value = fake_result
                response = await client.get("/crm/b2b/clients")

        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "supabase"
        assert body["items"][0]["name"] == "Medic"


class TestCrmB2bPaymentsEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_and_expected_shape(self, crm_client) -> None:
        fake_result = {
            "source": "supabase",
            "grid": {"clients": [], "periods": ["2026-01-01"], "cells": {}},
            "totals": {"grand_total": 0, "by_period": {}, "by_client": {}},
        }
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.b2b_payments_grid.return_value = fake_result
                response = await client.get(
                    "/crm/b2b/payments", params={"from_period": "2026-01-01", "to_period": "2026-06-30"}
                )

        assert response.status_code == 200
        body = response.json()
        assert "grid" in body
        assert "totals" in body

    @pytest.mark.asyncio
    async def test_defaults_apply_when_no_query_params_given(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.b2b_payments_grid.return_value = {
                    "source": "demo_fallback",
                    "grid": {"clients": [], "periods": [], "cells": {}},
                    "totals": {"grand_total": 0, "by_period": {}, "by_client": {}},
                }
                response = await client.get("/crm/b2b/payments")

        assert response.status_code == 200


class TestCrmB2bRetentionAlertsEndpoint:
    """retention-loop"""

    @pytest.mark.asyncio
    async def test_returns_200_and_expected_shape(self, crm_client) -> None:
        fake_alerts = [
            {
                "id": "a1",
                "client_id": "c1",
                "rule_id": "missed_payment",
                "severity": "warning",
                "message": "Sin pago registrado para Medic en 2026-07-01.",
            }
        ]
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_retention_service") as mock_get_service:
                mock_get_service.return_value.evaluate_and_persist.return_value = fake_alerts
                response = await client.get("/crm/b2b/retention-alerts")

        assert response.status_code == 200
        body = response.json()
        assert body["items"] == fake_alerts

    @pytest.mark.asyncio
    async def test_no_alerts_returns_an_empty_items_list(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_retention_service") as mock_get_service:
                mock_get_service.return_value.evaluate_and_persist.return_value = []
                response = await client.get("/crm/b2b/retention-alerts")

        assert response.status_code == 200
        assert response.json()["items"] == []
