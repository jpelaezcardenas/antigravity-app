"""
Tests for CRM B2B retainer endpoints (crm-b2b-retainers-cockpit, Change A).

Mirrors test_social_ops_endpoints.py's flag-check style plus an isolated-FastAPI-app
TestClient pattern (per test_radar.py) mocking the service layer — no network/credentials
required.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


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
    return TestClient(app)


class TestCrmB2bClientsEndpoint:
    def test_returns_200_and_expected_shape(self, crm_client) -> None:
        fake_result = {
            "source": "supabase",
            "items": [{"id": "c1", "name": "Medic", "status": "activo", "monthly_fee_cents": None}],
        }
        with patch(
            "presentation.crm_endpoints.get_crm_service"
        ) as mock_get_service:
            mock_get_service.return_value.list_b2b_clients.return_value = fake_result
            response = crm_client.get("/crm/b2b/clients")

        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "supabase"
        assert body["items"][0]["name"] == "Medic"


class TestCrmB2bPaymentsEndpoint:
    def test_returns_200_and_expected_shape(self, crm_client) -> None:
        fake_result = {
            "source": "supabase",
            "grid": {"clients": [], "periods": ["2026-01-01"], "cells": {}},
            "totals": {"grand_total": 0, "by_period": {}, "by_client": {}},
        }
        with patch(
            "presentation.crm_endpoints.get_crm_service"
        ) as mock_get_service:
            mock_get_service.return_value.b2b_payments_grid.return_value = fake_result
            response = crm_client.get(
                "/crm/b2b/payments", params={"from_period": "2026-01-01", "to_period": "2026-06-30"}
            )

        assert response.status_code == 200
        body = response.json()
        assert "grid" in body
        assert "totals" in body

    def test_defaults_apply_when_no_query_params_given(self, crm_client) -> None:
        with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
            mock_get_service.return_value.b2b_payments_grid.return_value = {
                "source": "demo_fallback",
                "grid": {"clients": [], "periods": [], "cells": {}},
                "totals": {"grand_total": 0, "by_period": {}, "by_client": {}},
            }
            response = crm_client.get("/crm/b2b/payments")

        assert response.status_code == 200
