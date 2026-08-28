"""
Credential-free unit tests for CrmService's B2B write methods (per-tenant-client-access,
Phase B: the Búnker feeding system). Mocks the Supabase service-role client entirely —
no network, no real auth.users writes — mirroring test_crm_service_grid_logic.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.crm_service import CrmService


def _fake_client(cliente_cero_id="cc-tenant"):
    """A MagicMock whose .table(...) chains return sane defaults; individual tests
    override specific chains as needed via side_effect reassignment."""
    client = MagicMock()

    def table_side_effect(name):
        table_mock = MagicMock()
        if name == "tenants":
            table_mock.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": cliente_cero_id})
            )
            table_mock.insert.return_value.execute.return_value = MagicMock(
                data=[{"id": "new-tenant-id"}]
            )
        return table_mock

    client.table.side_effect = table_side_effect
    return client


class TestCreateB2bClient:
    def test_creates_own_tenant_and_roster_row(self):
        client = _fake_client()
        b2b_clients_table = MagicMock()
        b2b_clients_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-1", "name": "Nuevo Cliente", "status": "activo"}]
        )

        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "b2b_clients":
                return b2b_clients_table
            return original_side_effect(name)

        client.table.side_effect = routed

        service = CrmService()
        service._provision_b2b_client_login = MagicMock()  # isolate from login provisioning

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = service.create_b2b_client(name="Nuevo Cliente", email=None)

        assert result["name"] == "Nuevo Cliente"
        insert_call = b2b_clients_table.insert.call_args[0][0]
        assert insert_call["client_tenant_id"] == "new-tenant-id"
        assert insert_call["tenant_id"] == "cc-tenant"
        assert insert_call["provision_status"] == "pending_email"
        service._provision_b2b_client_login.assert_not_called()

    def test_client_with_email_attempts_login_provisioning(self):
        client = _fake_client()
        b2b_clients_table = MagicMock()
        b2b_clients_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-2", "name": "Con Email", "status": "activo"}]
        )
        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "b2b_clients":
                return b2b_clients_table
            return original_side_effect(name)

        client.table.side_effect = routed

        service = CrmService()
        service._provision_b2b_client_login = MagicMock(
            return_value=("new-user-id", "https://supabase.example/invite?token=abc")
        )

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = service.create_b2b_client(name="Con Email", email="nuevo@cliente.co")

        service._provision_b2b_client_login.assert_called_once()
        assert result["provision_status"] == "provisioned"
        assert result["invite_link"] == "https://supabase.example/invite?token=abc"

    def test_login_provisioning_failure_does_not_fail_the_alta(self):
        """A client is still created even if login provisioning blows up — the roster
        row is the source of truth, not the login."""
        client = _fake_client()
        b2b_clients_table = MagicMock()
        b2b_clients_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-3", "name": "Fallo Login", "status": "activo"}]
        )
        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "b2b_clients":
                return b2b_clients_table
            return original_side_effect(name)

        client.table.side_effect = routed

        service = CrmService()
        service._provision_b2b_client_login = MagicMock(side_effect=RuntimeError("boom"))

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = service.create_b2b_client(name="Fallo Login", email="fallo@cliente.co")

        assert result["id"] == "client-3"  # alta still succeeded

    def test_explicit_plan_tier_is_written_to_tenants_and_b2b_clients(self):
        client = _fake_client()
        tenants_table = client.table("tenants")  # capture the mock created for "tenants"
        b2b_clients_table = MagicMock()
        b2b_clients_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-4", "name": "Con Tier", "status": "activo"}]
        )

        def routed(name):
            if name == "b2b_clients":
                return b2b_clients_table
            if name == "tenants":
                return tenants_table
            return MagicMock()

        client.table.side_effect = routed
        client.table.reset_mock()  # clear the setup call above before the real assertions

        service = CrmService()
        service._provision_b2b_client_login = MagicMock()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            service.create_b2b_client(name="Con Tier", plan_tier="growth")

        tenants_insert_call = tenants_table.insert.call_args[0][0]
        assert tenants_insert_call["plan_tier"] == "growth"

        b2b_insert_call = b2b_clients_table.insert.call_args[0][0]
        assert b2b_insert_call["plan_tier"] == "growth"

    def test_default_plan_tier_is_starter(self):
        client = _fake_client()
        b2b_clients_table = MagicMock()
        b2b_clients_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-5", "name": "Sin Tier", "status": "activo"}]
        )
        original_side_effect = client.table.side_effect

        def routed(name):
            if name == "b2b_clients":
                return b2b_clients_table
            return original_side_effect(name)

        client.table.side_effect = routed

        service = CrmService()
        service._provision_b2b_client_login = MagicMock()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            service.create_b2b_client(name="Sin Tier")

        b2b_insert_call = b2b_clients_table.insert.call_args[0][0]
        assert b2b_insert_call["plan_tier"] == "starter"

    def test_rejects_invalid_plan_tier(self):
        service = CrmService()
        with pytest.raises(ValueError):
            service.create_b2b_client(name="Tier Invalido", plan_tier="platinum")


class TestProvisionB2bClientLogin:
    def test_writes_generate_link_invite_not_a_password(self):
        client = MagicMock()
        client.auth.admin.generate_link.return_value = MagicMock(
            user=MagicMock(id="new-user-id"),
            properties=MagicMock(action_link="https://supabase.example/invite?token=abc"),
        )

        service = CrmService()
        user_id, invite_link = service._provision_b2b_client_login(
            client, "b2b-client-1", "tenant-x", "Cliente Nuevo", "nuevo@cliente.co",
            "SYN-ABC123", plan_tier="enterprise",
        )

        client.auth.admin.generate_link.assert_called_once_with(
            {"type": "invite", "email": "nuevo@cliente.co"}
        )
        client.auth.admin.create_user.assert_not_called()
        assert user_id == "new-user-id"
        assert invite_link == "https://supabase.example/invite?token=abc"

    def test_writes_plan_tier_to_usuarios_plan_not_hardcoded_starter(self):
        client = MagicMock()
        client.auth.admin.generate_link.return_value = MagicMock(
            user=MagicMock(id="new-user-id"),
            properties=MagicMock(action_link="https://supabase.example/invite?token=xyz"),
        )
        usuarios_table = MagicMock()

        def table_side_effect(name):
            if name == "usuarios":
                return usuarios_table
            return MagicMock()

        client.table.side_effect = table_side_effect

        service = CrmService()
        service._provision_b2b_client_login(
            client, "b2b-client-1", "tenant-x", "Cliente Nuevo", "nuevo@cliente.co",
            "SYN-ABC123", plan_tier="enterprise",
        )

        upsert_call = usuarios_table.upsert.call_args[0][0]
        assert upsert_call["plan"] == "enterprise"


class TestSetB2bClientStatus:
    def test_rejects_invalid_status(self):
        with pytest.raises(ValueError):
            CrmService().set_b2b_client_status("client-1", "en-pausa")

    def test_baja_deactivates_user_tenants_membership(self):
        client = MagicMock()
        b2b_clients_table = MagicMock()
        b2b_clients_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-1", "status": "inactivo", "client_tenant_id": "tenant-x"}]
        )
        user_tenants_table = MagicMock()

        def table_side_effect(name):
            if name == "b2b_clients":
                return b2b_clients_table
            if name == "user_tenants":
                return user_tenants_table
            return MagicMock()

        client.table.side_effect = table_side_effect

        from unittest.mock import patch

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().set_b2b_client_status("client-1", "inactivo")

        assert result["status"] == "inactivo"
        user_tenants_table.update.assert_called_once_with({"is_active": False})
        user_tenants_table.update.return_value.eq.assert_called_once_with("tenant_id", "tenant-x")

    def test_reactivar_activates_user_tenants_membership(self):
        client = MagicMock()
        b2b_clients_table = MagicMock()
        b2b_clients_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-1", "status": "activo", "client_tenant_id": "tenant-x"}]
        )
        user_tenants_table = MagicMock()

        def table_side_effect(name):
            if name == "b2b_clients":
                return b2b_clients_table
            if name == "user_tenants":
                return user_tenants_table
            return MagicMock()

        client.table.side_effect = table_side_effect

        from unittest.mock import patch

        with patch("services.crm_service.get_service_supabase", return_value=client):
            CrmService().set_b2b_client_status("client-1", "activo")

        user_tenants_table.update.assert_called_once_with({"is_active": True})


class TestUpsertB2bPayment:
    def test_normalizes_period_to_first_of_month_and_upserts(self):
        client = MagicMock()
        b2b_clients_table = MagicMock()
        b2b_clients_table.select.return_value.eq.return_value.single.return_value.execute.return_value = (
            MagicMock(data={"tenant_id": "tenant-x"})
        )
        b2b_payments_table = MagicMock()
        b2b_payments_table.upsert.return_value.execute.return_value = MagicMock(
            data=[{"client_id": "client-1", "period": "2026-03-01", "amount_cents": 89000000}]
        )

        def table_side_effect(name):
            if name == "b2b_clients":
                return b2b_clients_table
            if name == "b2b_payments":
                return b2b_payments_table
            return MagicMock()

        client.table.side_effect = table_side_effect

        from unittest.mock import patch

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().upsert_b2b_payment("client-1", "2026-03-15", 89000000)

        upsert_payload = b2b_payments_table.upsert.call_args[0][0]
        assert upsert_payload["period"] == "2026-03-01"
        assert upsert_payload["tenant_id"] == "tenant-x"
        assert result["amount_cents"] == 89000000


class TestUpdateB2bClientContact:
    def test_only_patches_provided_fields(self):
        client = MagicMock()
        b2b_clients_table = MagicMock()
        b2b_clients_table.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "client-1", "email": "new@client.co"}]
        )
        client.table.return_value = b2b_clients_table

        from unittest.mock import patch

        with patch("services.crm_service.get_service_supabase", return_value=client):
            CrmService().update_b2b_client_contact("client-1", email="new@client.co")

        patch_payload = b2b_clients_table.update.call_args[0][0]
        assert patch_payload == {"email": "new@client.co"}

    def test_raises_when_no_fields_given(self):
        with pytest.raises(ValueError):
            CrmService().update_b2b_client_contact("client-1")
