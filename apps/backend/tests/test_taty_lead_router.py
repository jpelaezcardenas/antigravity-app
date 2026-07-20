"""
Unit tests for taty_lead_router.py (taty-whatsapp-sales-router, Change D).

This is a NEW, separate lead-scoped router — NOT an extension of taty_intent_router.py, which is
tenant-scoped and has no notion of a pre-signup crm_leads row (see design.md Decision 1).
CrmService is mocked directly (no Supabase credentials needed), matching the pattern used
throughout the CRM/Sell Machine test suites.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.taty_lead_router import (
    _create_empty_tax_profile,
    _detect_persona_fields,
    _extract_topes_amount,
    classify_lead_intent,
    find_or_create_lead,
    generate_wompi_link,
    route_lead_document,
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
        ), patch(
            "services.taty_lead_router.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
        ) as mock_link:
            result = route_lead_message(
                "lead-1", "Quiero saber si me toca declarar renta este año"
            )

        mock_service.advance_lead.assert_called_once_with("lead-1", "PROSPECTOS")
        assert result["intent"] == "sales_interest"
        mock_link.assert_called_once_with("lead-1")
        assert "checkout.wompi.co" in result["reply"]

    def test_lead_past_nuevos_is_not_advanced_or_regressed(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ), patch(
            "services.taty_lead_router.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
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
        ) as mock_create, patch(
            "services.taty_lead_router.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
        ):
            route_lead_message("lead-1", "Sí, soy asalariado")

        mock_create.assert_called_once_with("lead-1")
        mock_service.update_tax_profile.assert_called_once()
        args, _ = mock_service.update_tax_profile.call_args
        assert args[0] == "lead-1"
        assert args[1] == {"es_asalariado": True}

    def test_payment_confirmation_approved_advances_to_por_aprobar(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ), patch(
            "services.taty_lead_router.verify_wompi_transaction",
            return_value={"status": "APPROVED", "wompi_transaction_id": "wompi-123"},
        ):
            result = route_lead_message("lead-1", "Ya pagué, listo")

        assert result["intent"] == "payment_confirmation"
        mock_service.advance_lead.assert_called_once_with("lead-1", "POR_APROBAR")

    def test_payment_confirmation_pending_does_not_advance(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ), patch(
            "services.taty_lead_router.verify_wompi_transaction",
            return_value={"status": "PENDING", "wompi_transaction_id": None},
        ):
            result = route_lead_message("lead-1", "Ya pagué, listo")

        assert result["intent"] == "payment_confirmation"
        mock_service.advance_lead.assert_not_called()
        assert "no" in result["reply"].lower() or "aún" in result["reply"].lower()

    def test_payment_confirmation_no_transaction_says_so(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="NUEVOS"
        ), patch(
            "services.taty_lead_router.verify_wompi_transaction",
            return_value={"status": None, "wompi_transaction_id": None},
        ):
            result = route_lead_message("lead-1", "Ya pagué, listo")

        assert result["intent"] == "payment_confirmation"
        mock_service.advance_lead.assert_not_called()


class TestDetectPersonaFieldsIndependiente:
    def test_independiente_sets_es_asalariado_false(self):
        mock_service = MagicMock()
        mock_service.get_tax_profile.return_value = {}
        mock_service.update_tax_profile.return_value = {"lead_id": "lead-1"}
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ), patch("services.taty_lead_router._create_empty_tax_profile"), patch(
            "services.taty_lead_router.generate_wompi_link",
            return_value="https://checkout.wompi.co/p/?reference=abc",
        ):
            route_lead_message("lead-1", "Soy independiente, trabajo por mi cuenta")

        args, _ = mock_service.update_tax_profile.call_args
        assert args[1] == {"es_asalariado": False}


class TestExtractTopesAmount:
    def test_plain_number_with_consignaciones_keyword(self):
        result = _extract_topes_amount("el año pasado me consignaron 80000000 en el banco")
        assert result == ("consignaciones", 80000000)

    def test_millones_suffix_with_ingresos_keyword(self):
        result = _extract_topes_amount("mis ingresos fueron de 70 millones el año pasado")
        assert result == ("ingresos", 70000000)

    def test_k_suffix_with_compras_keyword(self):
        result = _extract_topes_amount("hice compras por 70k el año pasado")
        assert result == ("compras", 70000)

    def test_patrimonio_keyword_detected(self):
        result = _extract_topes_amount("mi patrimonio es de 500 millones")
        assert result == ("patrimonio", 500000000)

    def test_no_category_keyword_returns_none(self):
        assert _extract_topes_amount("hola, como estas hoy 80000000") is None

    def test_category_keyword_without_amount_returns_none(self):
        assert _extract_topes_amount("tengo dudas sobre mis ingresos") is None


class TestDetectPersonaFieldsTopes:
    def test_topes_amount_merges_with_existing_topes(self):
        fields = _detect_persona_fields(
            "mis ingresos fueron 20000000", existing_topes={"consignaciones": 50000000}
        )
        assert fields["topes"] == {"consignaciones": 50000000, "ingresos": 20000000}

    def test_obligado_declarar_true_when_above_threshold(self):
        fields = _detect_persona_fields("me consignaron 80000000 el año pasado", existing_topes={})
        assert fields["topes"] == {"consignaciones": 80000000}
        assert fields["obligado_declarar"] is True

    def test_obligado_declarar_false_when_below_threshold(self):
        fields = _detect_persona_fields("mis ingresos fueron 10000000", existing_topes={})
        assert fields["topes"] == {"ingresos": 10000000}
        assert fields["obligado_declarar"] is False

    def test_no_topes_detected_leaves_fields_empty(self):
        fields = _detect_persona_fields("hola, como estas", existing_topes={})
        assert "topes" not in fields
        assert "obligado_declarar" not in fields

    def test_es_asalariado_still_detected_alongside_topes_logic(self):
        fields = _detect_persona_fields("Sí, soy asalariado", existing_topes={})
        assert fields == {"es_asalariado": True}


class TestRouteLeadDocument:
    def _mock_crm_service(self, tax_profile=None):
        mock_service = MagicMock()
        mock_service.get_tax_profile.return_value = tax_profile or {
            "rut_status": "requested",
            "extractos_status": "pending",
        }
        mock_service.update_tax_profile.return_value = {"lead_id": "lead-1"}
        return mock_service

    @pytest.mark.asyncio
    async def test_document_before_listos_contadora_is_not_processed(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="PROSPECTOS"
        ):
            result = await route_lead_document("lead-1", "MEDIA_ID_1", "application/pdf")

        mock_service.update_tax_profile.assert_not_called()
        assert result["processed"] is False

    @pytest.mark.asyncio
    async def test_first_document_is_treated_as_rut_and_requests_extractos(self):
        mock_service = self._mock_crm_service(
            tax_profile={"rut_status": "requested", "extractos_status": "pending"}
        )
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="LISTOS_CONTADORA"
        ), patch(
            "services.taty_lead_router.download_whatsapp_media",
            new=AsyncMock(return_value={"content": b"fake-pdf", "mime_type": "application/pdf"}),
        ), patch(
            "services.taty_lead_router.upload_tax_document", return_value="lead-1/rut.pdf"
        ) as mock_upload, patch(
            "services.taty_lead_router._get_lead_phone", return_value="573001234567"
        ), patch(
            "services.taty_lead_router.send_whatsapp_message", new=AsyncMock(return_value=True)
        ) as mock_send:
            result = await route_lead_document("lead-1", "MEDIA_ID_1", "application/pdf")

        mock_upload.assert_called_once_with(
            lead_id="lead-1", document_type="rut", file_bytes=b"fake-pdf", mime_type="application/pdf"
        )
        args, kwargs = mock_service.update_tax_profile.call_args
        patch_dict = kwargs if kwargs else args[1]
        assert patch_dict["rut_status"] == "collected"
        assert patch_dict["rut_storage_path"] == "lead-1/rut.pdf"
        assert patch_dict["extractos_status"] == "requested"
        mock_send.assert_called_once()
        assert result["processed"] is True

    @pytest.mark.asyncio
    async def test_second_document_is_treated_as_extractos(self):
        mock_service = self._mock_crm_service(
            tax_profile={"rut_status": "collected", "extractos_status": "requested"}
        )
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="LISTOS_CONTADORA"
        ), patch(
            "services.taty_lead_router.download_whatsapp_media",
            new=AsyncMock(return_value={"content": b"fake-pdf", "mime_type": "application/pdf"}),
        ), patch(
            "services.taty_lead_router.upload_tax_document", return_value="lead-1/extractos.pdf"
        ) as mock_upload:
            result = await route_lead_document("lead-1", "MEDIA_ID_2", "application/pdf")

        mock_upload.assert_called_once_with(
            lead_id="lead-1", document_type="extractos", file_bytes=b"fake-pdf",
            mime_type="application/pdf",
        )
        args, kwargs = mock_service.update_tax_profile.call_args
        patch_dict = kwargs if kwargs else args[1]
        assert patch_dict["extractos_status"] == "collected"
        assert result["processed"] is True

    @pytest.mark.asyncio
    async def test_download_failure_does_not_update_any_status(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="LISTOS_CONTADORA"
        ), patch(
            "services.taty_lead_router.download_whatsapp_media",
            new=AsyncMock(return_value=None),
        ):
            result = await route_lead_document("lead-1", "MEDIA_ID_1", "application/pdf")

        mock_service.update_tax_profile.assert_not_called()
        assert result["processed"] is False


class TestCreateEmptyTaxProfile:
    def test_includes_tenant_id_from_the_lead(self):
        """Regression test for a bug found live during Change I's Stage 11 (2026-07-20):
        crm_tax_profiles.tenant_id is NOT NULL but the insert never included it."""
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "tenant_id": "tenant-1"
        }
        with patch("services.taty_lead_router.get_service_supabase", return_value=mock_client):
            _create_empty_tax_profile("lead-1")

        insert_call = mock_client.table.return_value.insert
        insert_call.assert_called_once_with({"lead_id": "lead-1", "tenant_id": "tenant-1"})


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


class TestGenerateWompiLink:
    def test_creates_a_new_transaction_when_none_pending(self):
        mock_service = MagicMock()
        mock_service.checkout_lead_payment.return_value = {
            "public_key": "pub_prod_abc",
            "currency": "COP",
            "amount_in_cents": 8900000,
            "reference": "lead-1-123456",
            "signature": "sig123",
        }
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_latest_transaction", return_value=None
        ):
            url = generate_wompi_link("lead-1")

        mock_service.checkout_lead_payment.assert_called_once_with("lead-1")
        assert url.startswith("https://checkout.wompi.co/p/?")
        assert "public-key=pub_prod_abc" in url
        assert "reference=lead-1-123456" in url
        assert "amount-in-cents=8900000" in url
        assert "signature%3Aintegrity=sig123" in url or "signature:integrity=sig123" in url

    def test_reuses_an_existing_pending_transaction(self):
        mock_service = MagicMock()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_latest_transaction",
            return_value={
                "status": "PENDING",
                "reference": "existing-ref",
                "amount_cents": 8900000,
                "currency": "COP",
            },
        ), patch(
            "services.taty_lead_router.settings"
        ) as mock_settings, patch(
            "services.taty_lead_router.compute_integrity_signature", return_value="recomputed-sig"
        ):
            mock_settings.WOMPI_PUBLIC_KEY = "pub_prod_abc"
            mock_settings.WOMPI_INTEGRITY_SECRET = "secret"
            url = generate_wompi_link("lead-1")

        mock_service.checkout_lead_payment.assert_not_called()
        assert "reference=existing-ref" in url

    def test_creates_new_transaction_when_latest_is_not_pending(self):
        mock_service = MagicMock()
        mock_service.checkout_lead_payment.return_value = {
            "public_key": "pub_prod_abc",
            "currency": "COP",
            "amount_in_cents": 8900000,
            "reference": "lead-1-new",
            "signature": "sig456",
        }
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_latest_transaction",
            return_value={"status": "APPROVED", "reference": "old-ref"},
        ):
            url = generate_wompi_link("lead-1")

        mock_service.checkout_lead_payment.assert_called_once_with("lead-1")
        assert "reference=lead-1-new" in url


class TestVerifyWompiTransaction:
    def test_reports_approved_status(self):
        with patch(
            "services.taty_lead_router._get_latest_transaction",
            return_value={"status": "APPROVED", "wompi_transaction_id": "wompi-123"},
        ):
            result = verify_wompi_transaction("lead-1")

        assert result == {"status": "APPROVED", "wompi_transaction_id": "wompi-123"}

    def test_reports_pending_status(self):
        with patch(
            "services.taty_lead_router._get_latest_transaction",
            return_value={"status": "PENDING", "wompi_transaction_id": None},
        ):
            result = verify_wompi_transaction("lead-1")

        assert result["status"] == "PENDING"

    def test_reports_not_found_when_no_transaction_exists(self):
        with patch("services.taty_lead_router._get_latest_transaction", return_value=None):
            result = verify_wompi_transaction("lead-1")

        assert result["status"] is None
