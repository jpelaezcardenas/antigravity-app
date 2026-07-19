"""
Unit tests for taty_lead_router.py (taty-whatsapp-sales-router, Change D).

This is a NEW, separate lead-scoped router — NOT an extension of taty_intent_router.py, which is
tenant-scoped and has no notion of a pre-signup crm_leads row (see design.md Decision 1).
CrmService is mocked directly (no Supabase credentials needed), matching the pattern used
throughout the CRM/Sell Machine test suites.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.taty_lead_router import (
    classify_lead_intent,
    find_or_create_lead,
    generate_wompi_link,
    route_lead_message,
    verify_wompi_transaction,
)


class TestClassifyLeadIntent:
    def test_sales_interest_detected(self):
        intent, confidence = classify_lead_intent("Quiero saber si me toca declarar renta este año")
        assert intent == "sales_interest"
        assert confidence > 0

    def test_payment_confirmation_detected(self):
        intent, confidence = classify_lead_intent("Ya pagué, listo")
        assert intent == "payment_confirmation"
        assert confidence > 0

    def test_unknown_falls_back(self):
        intent, confidence = classify_lead_intent("asdkjaslkdj random text")
        assert intent == "unknown"
        assert confidence == 0.0


class TestRouteLeadMessage:
    def _mock_crm_service(self, lead_stage="NUEVOS", tax_profile=None):
        mock_service = MagicMock()
        mock_service.advance_lead.return_value = {"id": "lead-1", "stage": "PROSPECTOS"}
        mock_service.get_tax_profile.return_value = tax_profile or {}
        mock_service.update_tax_profile.return_value = {"lead_id": "lead-1"}
        return mock_service

    def test_sales_intent_advances_nuevos_lead_to_prospectos(self):
        mock_service = self._mock_crm_service(lead_stage="NUEVOS")
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="NUEVOS"
        ):
            result = route_lead_message(
                "lead-1", "Quiero saber si me toca declarar renta este año"
            )

        mock_service.advance_lead.assert_called_once_with("lead-1", "PROSPECTOS")
        assert result["intent"] == "sales_interest"

    def test_lead_past_nuevos_is_not_advanced_or_regressed(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ):
            result = route_lead_message(
                "lead-1", "Quiero saber si me toca declarar renta este año"
            )

        mock_service.advance_lead.assert_not_called()
        assert result["intent"] == "sales_interest"

    def test_persona_state_persisted_creates_missing_tax_profile(self):
        mock_service = self._mock_crm_service(tax_profile={})
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ), patch(
            "services.taty_lead_router._create_empty_tax_profile"
        ) as mock_create:
            route_lead_message("lead-1", "Sí, soy asalariado")

        mock_create.assert_called_once_with("lead-1")
        mock_service.update_tax_profile.assert_called_once()
        args, _ = mock_service.update_tax_profile.call_args
        assert args[0] == "lead-1"
        assert args[1] == {"es_asalariado": True}

    def test_payment_confirmation_returns_graceful_stub_reply(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="POR_APROBAR"
        ):
            result = route_lead_message("lead-1", "Ya pagué, listo")

        assert result["intent"] == "payment_confirmation"
        assert "no" in result["reply"].lower() or "aún" in result["reply"].lower() or "todavía" in result["reply"].lower()
        mock_service.advance_lead.assert_not_called()


class TestFindOrCreateLead:
    def test_returns_existing_lead_id_when_phone_matches(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "existing-lead-1"}
        ]
        with patch("services.taty_lead_router.get_service_supabase", return_value=mock_client):
            lead_id = find_or_create_lead("573001234567")

        assert lead_id == "existing-lead-1"

    def test_creates_a_new_nuevos_lead_when_no_match(self):
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "tenant-1"
        }
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "new-lead-1"}
        ]
        with patch("services.taty_lead_router.get_service_supabase", return_value=mock_client):
            lead_id = find_or_create_lead("573009999999", full_name="Nuevo Lead")

        assert lead_id == "new-lead-1"
        insert_args = mock_client.table.return_value.insert.call_args[0][0]
        assert insert_args["stage"] == "NUEVOS"
        assert insert_args["whatsapp_phone"] == "573009999999"


class TestWompiStubs:
    def test_generate_wompi_link_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            generate_wompi_link("lead-1", amount_cents=100000)

    def test_verify_wompi_transaction_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            verify_wompi_transaction("lead-1")
