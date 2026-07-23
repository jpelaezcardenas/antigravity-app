"""Tests for Taty's per-tenant profile resolution (taty-per-tenant-profiles, task 1).

`_get_tenant_profile(tenant_id)` replaces the old hardcoded `AGENT_PROFILES` dict:
a provisioned tenant is resolved from the `tenants` table + a `DEFAULT_PROFILE`
template; an unknown or non-uuid tenant key resolves to `None` gracefully (never
raises), which feeds `_error_response(..., error_code="tenant_not_found")`.

Follows the hermetic-mock convention used by service-layer tests such as
test_crm_wompi_tenant_scoping.py: `services.taty_service.get_supabase` is patched
with a MagicMock, no live Supabase connection required.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from services.taty_service import TatyAgentService, DEFAULT_PROFILE


def _mock_supabase_for_tenant(tenant_row: dict | None):
    """Build a MagicMock Supabase client whose tenants.select(...).eq(...).execute()
    returns a single row (or an empty result set) mimicking the real client shape."""
    client = MagicMock()

    def table_side_effect(name):
        m = MagicMock()
        if name == "tenants":
            data = [tenant_row] if tenant_row is not None else []
            m.select.return_value.eq.return_value.execute.return_value = MagicMock(data=data)
        return m

    client.table.side_effect = table_side_effect
    return client


class TestGetTenantProfileProvisionedTenant:
    def test_provisioned_tenant_profile_matches_legal_name(self):
        tenant_id = str(uuid.uuid4())
        tenant_row = {
            "id": tenant_id,
            "nit": "900.111.222-3",
            "legal_name": "Hermetic Test Tenant SAS",
            "is_cliente_cero": False,
            "company_id": None,
        }
        client = _mock_supabase_for_tenant(tenant_row)

        with patch("services.taty_service.get_supabase", return_value=client):
            profile = TatyAgentService()._get_tenant_profile(tenant_id)

        assert profile is not None
        assert profile["nombre_empresa"] == tenant_row["legal_name"]
        assert profile["tenant_id"] == tenant_id
        assert profile["nit"] == tenant_row["nit"]

    def test_provisioned_tenant_profile_regimen_is_none_by_default(self):
        tenant_id = str(uuid.uuid4())
        tenant_row = {
            "id": tenant_id,
            "nit": "900.111.222-3",
            "legal_name": "Hermetic Test Tenant SAS",
            "is_cliente_cero": False,
            "company_id": None,
        }
        client = _mock_supabase_for_tenant(tenant_row)

        with patch("services.taty_service.get_supabase", return_value=client):
            profile = TatyAgentService()._get_tenant_profile(tenant_id)

        assert profile["regimen"] is None

    def test_cliente_cero_tenant_gets_contexia_fiscal_source_without_mutating_default(self):
        tenant_id = str(uuid.uuid4())
        tenant_row = {
            "id": tenant_id,
            "nit": "9.867.082-4",
            "legal_name": "Contexia",
            "is_cliente_cero": True,
            "company_id": "ctx-001",
        }
        client = _mock_supabase_for_tenant(tenant_row)

        with patch("services.taty_service.get_supabase", return_value=client):
            profile = TatyAgentService()._get_tenant_profile(tenant_id)

        assert "contexia_fiscal" in profile["fuentes_habilitadas"]
        # The shared module-level DEFAULT_PROFILE list must never be mutated in place.
        assert "contexia_fiscal" not in DEFAULT_PROFILE["fuentes_habilitadas"]


class TestGetTenantProfileUnknownTenant:
    def test_unknown_tenant_uuid_returns_none(self):
        unknown_tenant_id = str(uuid.uuid4())
        client = _mock_supabase_for_tenant(None)

        with patch("services.taty_service.get_supabase", return_value=client):
            profile = TatyAgentService()._get_tenant_profile(unknown_tenant_id)

        assert profile is None


class TestGetTenantProfileLegacyNonUuidKey:
    def test_legacy_non_uuid_key_returns_none_without_exception(self):
        client = _mock_supabase_for_tenant(None)

        with patch("services.taty_service.get_supabase", return_value=client):
            profile = TatyAgentService()._get_tenant_profile("ferez-001")

        assert profile is None


class TestErrorResponseErrorCode:
    def test_error_response_includes_error_code_when_provided(self):
        service = TatyAgentService()
        response = service._error_response(
            "Cliente no configurado", start_time=0.0, error_code="tenant_not_found"
        )

        assert response["error_code"] == "tenant_not_found"

    def test_error_response_omits_error_code_when_not_provided(self):
        service = TatyAgentService()
        response = service._error_response("Some error", start_time=0.0)

        assert "error_code" not in response
