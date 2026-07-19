"""
Tests for CRM B2C sell-machine endpoints (crm-b2c-sell-machine-cockpit, Change B).

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern as test_crm_endpoints.py (Change A), needed because the sync
fastapi.testclient.TestClient is broken by a pre-existing httpx>=0.28/starlette 0.27 mismatch in
this environment.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI


@pytest.fixture
def crm_client():
    from presentation.crm_endpoints import router as crm_router

    app = FastAPI()
    app.include_router(crm_router, prefix="/crm")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestB2cPipelineEndpoint:
    @pytest.mark.asyncio
    async def test_returns_200_and_expected_shape(self, crm_client) -> None:
        fake_result = {
            "source": "supabase",
            "columns": [{"id": "NUEVOS", "label": "Nuevos", "leads": []}],
            "summary": {"total_leads": 0},
        }
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.b2c_pipeline.return_value = fake_result
                response = await client.get("/crm/b2c/pipeline")

        assert response.status_code == 200
        assert response.json()["columns"][0]["id"] == "NUEVOS"


class TestAdvanceLeadEndpoint:
    @pytest.mark.asyncio
    async def test_advances_a_lead(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.advance_lead.return_value = {
                    "id": "l1",
                    "stage": "PROSPECTOS",
                }
                response = await client.post("/crm/leads/l1/advance", json={"stage": "PROSPECTOS"})

        assert response.status_code == 200
        assert response.json()["stage"] == "PROSPECTOS"

    @pytest.mark.asyncio
    async def test_invalid_stage_returns_4xx(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.advance_lead.side_effect = ValueError("Invalid stage")
                response = await client.post("/crm/leads/l1/advance", json={"stage": "BOGUS"})

        assert 400 <= response.status_code < 500


class TestTaxProfileEndpoints:
    @pytest.mark.asyncio
    async def test_get_tax_profile(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.get_tax_profile.return_value = {
                    "lead_id": "l1",
                    "rut_status": "pending",
                }
                response = await client.get("/crm/leads/l1/tax-profile")

        assert response.status_code == 200
        assert response.json()["rut_status"] == "pending"

    @pytest.mark.asyncio
    async def test_patch_tax_profile(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.update_tax_profile.return_value = {
                    "lead_id": "l1",
                    "rut_status": "collected",
                }
                response = await client.patch(
                    "/crm/leads/l1/tax-profile", json={"rut_status": "collected"}
                )

        assert response.status_code == 200
        assert response.json()["rut_status"] == "collected"


class TestApprovePaymentEndpoint:
    @pytest.mark.asyncio
    async def test_approves_payment(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.approve_payment.return_value = {
                    "id": "l1",
                    "stage": "LISTOS_CONTADORA",
                }
                response = await client.post(
                    "/crm/leads/l1/approve-payment", json={"approved_by": "admin@contexia.online"}
                )

        assert response.status_code == 200
        assert response.json()["stage"] == "LISTOS_CONTADORA"

    @pytest.mark.asyncio
    async def test_rejects_when_not_por_aprobar(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.approve_payment.side_effect = ValueError(
                    "Lead is not in POR_APROBAR stage"
                )
                response = await client.post(
                    "/crm/leads/l1/approve-payment", json={"approved_by": "admin@contexia.online"}
                )

        assert 400 <= response.status_code < 500
