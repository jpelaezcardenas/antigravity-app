"""Tests for resolve_b2b_tenant_for_whatsapp_phone (hermes-jarvis-contexia, D2).

D2: a WhatsApp message from a Growth/Enterprise B2B client's phone number should proxy to
Hermes instead of the B2C Renta Natural lead flow. There was previously no concept of "the
tenant of a WhatsApp lead" anywhere in taty_lead_router.py -- every lead resolves to Cliente
Cero. This lookup bridges crm_leads.whatsapp_phone (always digits-only, see
_normalize_whatsapp_phone) to b2b_clients.phone (free-text, typed by an operator in the Bunker
alta form -- may contain spaces/+/dashes) by normalizing BOTH sides before comparing, so a
raw .eq() that would silently never match doesn't ship.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.taty_lead_router import resolve_b2b_tenant_for_whatsapp_phone


def _mock_supabase(b2b_rows, tenant_row=None):
    client = MagicMock()

    def table(name):
        tbl = MagicMock()
        if name == "b2b_clients":
            tbl.select.return_value.execute.return_value = SimpleNamespace(data=b2b_rows)
        elif name == "tenants":
            tbl.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                SimpleNamespace(data=tenant_row)
            )
        else:
            raise AssertionError(f"Unexpected table queried: {name}")
        return tbl

    client.table.side_effect = table
    return client


class TestResolveB2bTenantForWhatsappPhone:
    def test_matches_despite_different_phone_formatting(self):
        """Lead phone is digits-only ('573001234567'); the b2b_clients row was typed with
        spaces and a plus sign ('+57 300 123 4567') -- must still match."""
        b2b_rows = [{"phone": "+57 300 123 4567", "client_tenant_id": "tenant-abc"}]
        tenant_row = {"plan_tier": "growth"}
        client = _mock_supabase(b2b_rows, tenant_row)

        with patch("services.taty_lead_router.get_service_supabase", return_value=client):
            result = resolve_b2b_tenant_for_whatsapp_phone("573001234567")

        assert result == ("tenant-abc", "growth")

    def test_no_matching_b2b_client_returns_none(self):
        b2b_rows = [{"phone": "+57 300 999 9999", "client_tenant_id": "tenant-xyz"}]
        client = _mock_supabase(b2b_rows)

        with patch("services.taty_lead_router.get_service_supabase", return_value=client):
            result = resolve_b2b_tenant_for_whatsapp_phone("573001234567")

        assert result is None

    def test_empty_b2b_clients_table_returns_none(self):
        client = _mock_supabase([])

        with patch("services.taty_lead_router.get_service_supabase", return_value=client):
            result = resolve_b2b_tenant_for_whatsapp_phone("573001234567")

        assert result is None

    def test_matched_row_with_no_linked_tenant_returns_none(self):
        """A b2b_clients row can, in principle, have client_tenant_id NULL -- never crash on it."""
        b2b_rows = [{"phone": "573001234567", "client_tenant_id": None}]
        client = _mock_supabase(b2b_rows)

        with patch("services.taty_lead_router.get_service_supabase", return_value=client):
            result = resolve_b2b_tenant_for_whatsapp_phone("573001234567")

        assert result is None

    def test_matched_tenant_missing_plan_tier_returns_none(self):
        b2b_rows = [{"phone": "573001234567", "client_tenant_id": "tenant-abc"}]
        client = _mock_supabase(b2b_rows, tenant_row={})

        with patch("services.taty_lead_router.get_service_supabase", return_value=client):
            result = resolve_b2b_tenant_for_whatsapp_phone("573001234567")

        assert result is None

    def test_lookup_error_returns_none_without_raising(self):
        with patch(
            "services.taty_lead_router.get_service_supabase",
            side_effect=RuntimeError("connection refused"),
        ):
            result = resolve_b2b_tenant_for_whatsapp_phone("573001234567")

        assert result is None

    def test_empty_phone_returns_none_without_querying(self):
        with patch("services.taty_lead_router.get_service_supabase") as mock_get:
            result = resolve_b2b_tenant_for_whatsapp_phone("")

        assert result is None
        mock_get.assert_not_called()
