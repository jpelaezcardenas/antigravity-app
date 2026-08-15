"""Tests for run_renta_diagnostico's crm_leads capture (fix-whatsapp-phone-normalization-dedup).

Found live 2026-08-15: the original direct .insert() used column names that don't exist on
crm_leads (whatsapp/name/crm_stage/lead_source/notes vs the real whatsapp_phone/full_name/stage)
and a hardcoded, invalid tenant_id string — every call silently failed (caught by a bare
except). Confirmed live: SELECT source, count(*) FROM crm_leads GROUP BY source returned only
'whatsapp', zero rows from this path ever succeeded. Fixed by routing through
CrmService.whatsapp_intake, the same correct, deduped, tenant-scoped path the WhatsApp channel
uses.
"""

from __future__ import annotations

from unittest.mock import patch

from services.wizard_service import run_renta_diagnostico


def _quiz_kwargs(whatsapp="573001234567"):
    return {
        "nombre": "Ana Test",
        "whatsapp": whatsapp,
        "tipo_ingreso": "salario",
        "ingresos_anuales": 10_000_000,
        "patrimonio": 5_000_000,
        "compras": 1_000_000,
        "consumos_tarjeta": 500_000,
        "inversiones": 0,
    }


class TestRentaDiagnosticoLeadCapture:
    def test_new_phone_creates_lead_via_crm_service(self):
        with patch("services.wizard_service.CrmService") as mock_crm_service_cls:
            mock_crm_service_cls.return_value.whatsapp_intake.return_value = {
                "lead_id": "new-lead-id",
                "is_new": True,
                "stage": "NUEVOS",
            }
            run_renta_diagnostico(**_quiz_kwargs())

        mock_crm_service_cls.return_value.whatsapp_intake.assert_called_once_with(
            "573001234567", full_name="Ana Test"
        )

    def test_existing_phone_does_not_duplicate(self):
        """whatsapp_intake itself owns the dedupe-by-phone lookup — this test confirms
        run_renta_diagnostico calls it rather than bypassing it with a direct insert."""
        with patch("services.wizard_service.CrmService") as mock_crm_service_cls:
            mock_crm_service_cls.return_value.whatsapp_intake.return_value = {
                "lead_id": "existing-lead-id",
                "is_new": False,
                "stage": "PROSPECTOS",
            }
            result = run_renta_diagnostico(**_quiz_kwargs(whatsapp="+573001234567"))

        mock_crm_service_cls.return_value.whatsapp_intake.assert_called_once_with(
            "+573001234567", full_name="Ana Test"
        )
        assert "color" in result  # diagnostic result is still returned regardless of CRM outcome

    def test_crm_failure_does_not_break_the_diagnostic_response(self):
        """The quiz result (topes evaluation) must still be returned even if CRM capture fails —
        matches the original try/except intent, now applied around the correct code path."""
        with patch("services.wizard_service.CrmService") as mock_crm_service_cls:
            mock_crm_service_cls.return_value.whatsapp_intake.side_effect = Exception("boom")
            result = run_renta_diagnostico(**_quiz_kwargs())

        assert "color" in result
        assert "mensaje" in result
