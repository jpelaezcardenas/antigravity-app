"""
Credential-free unit tests for recording the agreed professional fee and its service band
(pricing-quote-engine, Stage 5).

Mirrors test_crm_service_b2b_writes.py's fully-mocked Supabase pattern. What is asserted
here is the *validation and payload shaping* the service owns — the Postgres CHECK is a
backstop, not the error surface the Búnker should ever see.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.crm_service import CrmService
from services.pricing_service import SERVICE_BANDS


def _fake_client(cliente_cero_id="cc-tenant"):
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


def _route(client, name, table_mock):
    original = client.table.side_effect

    def routed(requested):
        if requested == name:
            return table_mock
        return original(requested)

    client.table.side_effect = routed
    return table_mock


class TestServiceBandConstant:
    def test_bands_match_the_engine_and_the_database_check(self):
        """One source of truth: the engine suggests these, the column constrains these."""
        assert set(SERVICE_BANDS) == {"micro", "estandar", "complejo"}


class TestCreateB2bClientWithBand:
    def test_persists_the_band_alongside_the_fee(self):
        client = _fake_client()
        b2b = _route(client, "b2b_clients", MagicMock())
        b2b.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "c-1", "name": "Con Banda", "status": "activo"}]
        )

        service = CrmService()
        service._provision_b2b_client_login = MagicMock()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            service.create_b2b_client(
                name="Con Banda",
                email=None,
                monthly_fee_cents=1_490_000_00,
                service_band="estandar",
            )

        inserted = b2b.insert.call_args[0][0]
        assert inserted["monthly_fee_cents"] == 1_490_000_00
        assert inserted["service_band"] == "estandar"

    def test_omitting_the_band_writes_null_not_a_default(self):
        """Inferring a band from the fee amount is exactly the guess this change removes."""
        client = _fake_client()
        b2b = _route(client, "b2b_clients", MagicMock())
        b2b.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "c-2", "name": "Sin Banda", "status": "activo"}]
        )

        service = CrmService()
        service._provision_b2b_client_login = MagicMock()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            service.create_b2b_client(name="Sin Banda", email=None, monthly_fee_cents=890_000_00)

        assert b2b.insert.call_args[0][0]["service_band"] is None

    def test_invalid_band_raises_before_touching_the_database(self):
        client = _fake_client()
        service = CrmService()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            with pytest.raises(ValueError) as exc:
                service.create_b2b_client(name="Malo", email=None, service_band="premium")

        assert "premium" in str(exc.value)
        client.table.assert_not_called()


class TestUpdateB2bClientCommercials:
    def test_updates_fee_and_band_together(self):
        client = MagicMock()
        b2b = MagicMock()
        client.table.return_value = b2b
        b2b.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c-1", "monthly_fee_cents": 2_400_000_00, "service_band": "complejo"}]
        )

        service = CrmService()
        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = service.update_b2b_client_commercials(
                "c-1", monthly_fee_cents=2_400_000_00, service_band="complejo"
            )

        assert b2b.update.call_args[0][0] == {
            "monthly_fee_cents": 2_400_000_00,
            "service_band": "complejo",
        }
        assert result["service_band"] == "complejo"

    def test_updates_only_the_field_supplied(self):
        client = MagicMock()
        b2b = MagicMock()
        client.table.return_value = b2b
        b2b.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c-1", "service_band": "micro"}]
        )

        service = CrmService()
        with patch("services.crm_service.get_service_supabase", return_value=client):
            service.update_b2b_client_commercials("c-1", service_band="micro")

        assert b2b.update.call_args[0][0] == {"service_band": "micro"}

    def test_clearing_the_band_is_possible_and_distinct_from_omitting_it(self):
        """A band recorded by mistake must be removable. Empty string clears to NULL;
        omission leaves the stored value alone."""
        client = MagicMock()
        b2b = MagicMock()
        client.table.return_value = b2b
        b2b.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "c-1", "service_band": None}]
        )

        service = CrmService()
        with patch("services.crm_service.get_service_supabase", return_value=client):
            service.update_b2b_client_commercials("c-1", service_band="")

        assert b2b.update.call_args[0][0] == {"service_band": None}

    def test_invalid_band_raises_rather_than_hitting_the_check_constraint(self):
        client = MagicMock()
        service = CrmService()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            with pytest.raises(ValueError) as exc:
                service.update_b2b_client_commercials("c-1", service_band="gigante")

        assert "gigante" in str(exc.value)
        client.table.assert_not_called()

    def test_negative_fee_is_rejected(self):
        client = MagicMock()
        service = CrmService()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            with pytest.raises(ValueError):
                service.update_b2b_client_commercials("c-1", monthly_fee_cents=-1)

        client.table.assert_not_called()

    def test_an_empty_patch_is_rejected(self):
        client = MagicMock()
        service = CrmService()

        with patch("services.crm_service.get_service_supabase", return_value=client):
            with pytest.raises(ValueError):
                service.update_b2b_client_commercials("c-1")

        client.table.assert_not_called()


class TestRosterProjection:
    def test_listing_returns_the_service_band(self, monkeypatch):
        """Without this, the Búnker could write a band it can never read back."""
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")

        client = _fake_client()
        b2b = _route(client, "b2b_clients", MagicMock())
        b2b.select.return_value.eq.return_value.order.return_value.execute.return_value = (
            MagicMock(data=[{"id": "c-1", "name": "X", "service_band": "estandar"}])
        )

        service = CrmService()
        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = service.list_b2b_clients()

        projection = b2b.select.call_args[0][0]
        assert "service_band" in projection
        assert result["items"][0]["service_band"] == "estandar"
