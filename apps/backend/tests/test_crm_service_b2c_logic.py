"""
Credential-free unit tests for crm_service's B2C pipeline/lead/tax-profile/approval logic
(crm-b2c-sell-machine-cockpit, Change B).

Mocks the Supabase client entirely (no network, no env credentials required), mirroring
test_crm_service_grid_logic.py's approach for Change A. The Supabase-hitting integration
tests live in test_crm_b2c_schema.py (RUN_CRM_B2B=1).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.crm_service import CrmService


def _patched_env():
    return patch(
        "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
    )


class TestB2cPipeline:
    def test_groups_leads_into_columns_by_stage(self):
        leads_data = [
            {"id": "l1", "full_name": "A", "stage": "NUEVOS", "score": 10},
            {"id": "l2", "full_name": "B", "stage": "POR_APROBAR", "score": 75},
        ]
        client = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = (
            MagicMock(data=leads_data)
        )
        client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            MagicMock(data={"id": "tenant-1"})
        )

        def table_side_effect(name):
            m = MagicMock()
            if name == "tenants":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data={"id": "tenant-1"}
                )
            elif name == "crm_leads":
                m.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock(
                    data=leads_data
                )
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env():
            result = CrmService().b2c_pipeline()

        assert result["source"] == "supabase"
        columns_by_id = {c["id"]: c for c in result["columns"]}
        assert len(columns_by_id["NUEVOS"]["leads"]) == 1
        assert len(columns_by_id["POR_APROBAR"]["leads"]) == 1
        assert len(columns_by_id["PROSPECTOS"]["leads"]) == 0
        assert len(columns_by_id["LISTOS_CONTADORA"]["leads"]) == 0

    def test_supabase_unreachable_falls_back_to_demo(self):
        with patch("services.crm_service.get_service_supabase", side_effect=Exception("down")), _patched_env():
            result = CrmService().b2c_pipeline()

        assert result["source"] == "demo_fallback"
        assert len(result["columns"]) == 4


class TestAdvanceLead:
    def test_advances_to_a_valid_stage(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.update.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"id": "l1", "stage": "PROSPECTOS"}]
                )
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env():
            result = CrmService().advance_lead("l1", "PROSPECTOS")

        assert result["stage"] == "PROSPECTOS"

    def test_rejects_an_invalid_stage(self):
        with _patched_env():
            with pytest.raises(ValueError):
                CrmService().advance_lead("l1", "NOT_A_REAL_STAGE")


class TestTaxProfile:
    def test_get_tax_profile_returns_stored_fields(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_tax_profiles":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data={"lead_id": "l1", "es_asalariado": True, "rut_status": "pending"}
                )
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env():
            result = CrmService().get_tax_profile("l1")

        assert result["es_asalariado"] is True
        assert result["rut_status"] == "pending"

    def test_update_tax_profile_applies_patch(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_tax_profiles":
                m.update.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"lead_id": "l1", "rut_status": "collected"}]
                )
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env():
            result = CrmService().update_tax_profile("l1", {"rut_status": "collected"})

        assert result["rut_status"] == "collected"


class TestApprovePayment:
    def test_approves_a_por_aprobar_lead(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data={"id": "l1", "stage": "POR_APROBAR"}
                )
                m.update.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"id": "l1", "stage": "LISTOS_CONTADORA"}]
                )
            elif name == "crm_wompi_transactions":
                m.update.return_value.eq.return_value.execute.return_value = MagicMock(
                    data=[{"lead_id": "l1", "status": "APPROVED"}]
                )
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env():
            result = CrmService().approve_payment("l1", approved_by="admin@contexia.online")

        assert result["stage"] == "LISTOS_CONTADORA"

    def test_rejects_a_lead_not_in_por_aprobar(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data={"id": "l1", "stage": "NUEVOS"}
                )
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env():
            with pytest.raises(ValueError):
                CrmService().approve_payment("l1", approved_by="admin@contexia.online")
