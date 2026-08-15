"""
Tests for the WhatsApp lead intake endpoint/service (chatwoot-hermes-taty-bridge,
Task Group 1): POST /api/v1/crm/leads/whatsapp-intake finds-or-creates a crm_leads
row by WhatsApp phone number.

Service-layer tests mock the Supabase service-role client entirely (no network),
mirroring test_crm_service_b2b_writes.py. Endpoint tests use the isolated
FastAPI app + httpx.ASGITransport pattern from test_crm_b2c_endpoints.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI

from config import settings
from services.crm_service import CrmService, _normalize_whatsapp_phone


def _fake_client(cliente_cero_id="cc-tenant"):
    """A MagicMock whose .table("tenants") chain resolves the Cliente Cero tenant id,
    mirroring the _fake_client helper in test_crm_service_b2b_writes.py."""
    client = MagicMock()

    def table_side_effect(name):
        table_mock = MagicMock()
        if name == "tenants":
            table_mock.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": cliente_cero_id})
            )
        return table_mock

    client.table.side_effect = table_side_effect
    return client


class TestNormalizeWhatsappPhone:
    def test_plus_and_no_plus_forms_normalize_to_the_same_value(self):
        """Regression test for the live bug found 2026-08-15 (fix-whatsapp-phone-normalization-
        dedup): the normalizer used to preserve whichever +-prefix state the caller passed,
        so "+573504187902" and "573504187902" never matched — two real crm_leads rows were
        created for the same WhatsApp customer as a result."""
        assert _normalize_whatsapp_phone("+573001234567") == _normalize_whatsapp_phone(
            "573001234567"
        )

    def test_normalized_form_has_no_plus(self):
        assert _normalize_whatsapp_phone("+573001234567") == "573001234567"

    def test_strips_spaces_and_punctuation(self):
        assert _normalize_whatsapp_phone("+57 300 123 4567") == "573001234567"


class TestWhatsappIntakeService:
    def test_existing_lead_found_regardless_of_plus_prefix_format(self):
        """The lookup must use the SAME normalized value the original insert used, so a lead
        created from one phone format is found when contacted via the other format."""
        client = _fake_client()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data={"id": "existing-lead-id", "stage": "PROSPECTOS"})
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "crm_leads":
                return leads_table
            return original_side_effect(name)

        client.table.side_effect = routed

        with patch("services.crm_service.get_service_supabase", return_value=client):
            # Original lead was created from "+573001234567"; this call uses no "+".
            result = CrmService().whatsapp_intake("573001234567")

        assert result == {"lead_id": "existing-lead-id", "is_new": False, "stage": "PROSPECTOS"}
        lookup_call = leads_table.select.return_value.eq.return_value.eq
        assert lookup_call.call_args[0] == ("whatsapp_phone", "573001234567")
        leads_table.insert.assert_not_called()


    def test_new_phone_creates_lead_in_nuevos_stage(self):
        client = _fake_client()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data=None)
        )
        leads_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-lead-id", "stage": "NUEVOS"}]
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "crm_leads":
                return leads_table
            return original_side_effect(name)

        client.table.side_effect = routed

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().whatsapp_intake("+57 300 123 4567")

        assert result == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}
        insert_payload = leads_table.insert.call_args[0][0]
        assert insert_payload["stage"] == "NUEVOS"
        assert insert_payload["tenant_id"] == "cc-tenant"
        assert insert_payload["whatsapp_phone"] == "573001234567"

    def test_new_phone_with_full_name_creates_lead_with_that_name(self):
        client = _fake_client()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data=None)
        )
        leads_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-lead-id", "stage": "NUEVOS"}]
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "crm_leads":
                return leads_table
            return original_side_effect(name)

        client.table.side_effect = routed

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().whatsapp_intake("+573001234567", full_name="Some Name")

        assert result == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}
        insert_payload = leads_table.insert.call_args[0][0]
        assert insert_payload["full_name"] == "Some Name"

    def test_new_phone_without_full_name_falls_back_to_phone(self):
        client = _fake_client()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data=None)
        )
        leads_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-lead-id", "stage": "NUEVOS"}]
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "crm_leads":
                return leads_table
            return original_side_effect(name)

        client.table.side_effect = routed

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().whatsapp_intake("+573001234567")

        assert result == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}
        insert_payload = leads_table.insert.call_args[0][0]
        assert insert_payload["full_name"] == "+573001234567"

    def test_known_phone_lookup_ignores_full_name_argument(self):
        client = _fake_client()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data={"id": "existing-lead-id", "stage": "PROSPECTOS"})
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "crm_leads":
                return leads_table
            return original_side_effect(name)

        client.table.side_effect = routed

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().whatsapp_intake("+573001234567", full_name="Ignored Name")

        assert result == {"lead_id": "existing-lead-id", "is_new": False, "stage": "PROSPECTOS"}
        leads_table.insert.assert_not_called()

    def test_known_phone_is_found_not_duplicated(self):
        client = _fake_client()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data={"id": "existing-lead-id", "stage": "PROSPECTOS"})
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "crm_leads":
                return leads_table
            return original_side_effect(name)

        client.table.side_effect = routed

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().whatsapp_intake("+573001234567")

        assert result == {"lead_id": "existing-lead-id", "is_new": False, "stage": "PROSPECTOS"}
        leads_table.insert.assert_not_called()


@pytest.fixture
def crm_client():
    from presentation.crm_endpoints import router as crm_router

    app = FastAPI()
    app.include_router(crm_router, prefix="/crm")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestWhatsappIntakeEndpoint:
    @pytest.mark.asyncio
    async def test_new_phone_returns_is_new_true(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.return_value = {
                    "lead_id": "new-lead-id",
                    "is_new": True,
                    "stage": "NUEVOS",
                }
                response = await client.post(
                    "/crm/leads/whatsapp-intake", json={"whatsapp_phone": "+573001234567"}
                )

        assert response.status_code == 200
        assert response.json() == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}

    @pytest.mark.asyncio
    async def test_known_phone_returns_is_new_false(self, crm_client) -> None:
        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.return_value = {
                    "lead_id": "existing-lead-id",
                    "is_new": False,
                    "stage": "PROSPECTOS",
                }
                response = await client.post(
                    "/crm/leads/whatsapp-intake", json={"whatsapp_phone": "+573001234567"}
                )

        assert response.status_code == 200
        assert response.json()["is_new"] is False

    @pytest.mark.asyncio
    async def test_unauthenticated_call_is_rejected(self, crm_client, monkeypatch) -> None:
        """With AUTH_ENFORCED=True and no Authorization header, get_current_user
        (applied as a router-level dependency) must reject the request with a 4xx
        before the service layer is ever touched."""
        monkeypatch.setattr(settings, "AUTH_ENFORCED", True)

        async with crm_client as client:
            with patch("presentation.crm_endpoints.get_crm_service") as mock_get_service:
                response = await client.post(
                    "/crm/leads/whatsapp-intake", json={"whatsapp_phone": "+573001234567"}
                )

        assert 400 <= response.status_code < 500
        mock_get_service.return_value.whatsapp_intake.assert_not_called()
