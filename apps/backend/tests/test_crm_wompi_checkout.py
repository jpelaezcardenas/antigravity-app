"""Tests for the Wompi checkout flow on crm_service (change wompi-payment-integration,
"Change C" for crm-b2c-sell-machine-cockpit's crm_wompi_transactions table).

Mocks the Supabase client entirely, mirroring test_crm_service_b2c_logic.py's approach.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from postgrest.exceptions import APIError

from services.crm_service import CrmService


def _patched_env():
    return patch(
        "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
    )


def _patched_wompi_settings():
    return patch.multiple(
        "config.settings",
        WOMPI_PUBLIC_KEY="pub_test_x",
        WOMPI_INTEGRITY_SECRET="test_integrity_x",
    )


class TestCheckoutLeadPayment:
    def test_valid_lead_creates_pending_transaction_and_returns_checkout_data(self):
        client = MagicMock()
        inserted = {}

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data={"id": "l1", "tenant_id": "tenant-1"}
                )
            elif name == "crm_wompi_transactions":
                def _insert(payload):
                    inserted.update(payload)
                    r = MagicMock()
                    r.execute.return_value = MagicMock(data=[payload])
                    return r
                m.insert.side_effect = _insert
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_wompi_settings():
            result = CrmService().checkout_lead_payment("l1")

        assert inserted["tenant_id"] == "tenant-1"
        assert inserted["lead_id"] == "l1"
        assert inserted["status"] == "PENDING"
        assert inserted["reference"]
        assert result["reference"] == inserted["reference"]
        assert result["public_key"] == "pub_test_x"
        assert result["currency"] == "COP"
        assert result["amount_in_cents"] > 0
        assert result["signature"]  # non-empty, computed from integrity secret

    def test_unknown_lead_raises_without_creating_a_transaction(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                    data=None
                )
            elif name == "crm_wompi_transactions":
                m.insert.side_effect = AssertionError("must not insert for an unknown lead")
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_wompi_settings():
            with pytest.raises(LookupError):
                CrmService().checkout_lead_payment("does-not-exist")

    def test_postgrest_single_row_not_found_error_becomes_lookup_error(self):
        # Real postgrest-py behavior: .single().execute() RAISES APIError when
        # zero rows match, it does not return data=None (unlike our other
        # mocked tests here). This reproduces the bug found in Railway
        # production logs (checkout for an unknown lead returned 500, not
        # 404) — the try/except APIError in checkout_lead_payment must
        # translate this into the same LookupError as the "no data" case.
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_leads":
                m.select.return_value.eq.return_value.single.return_value.execute.side_effect = APIError(
                    {"message": "JSON object requested, multiple (or no) rows returned", "code": "PGRST116"}
                )
            elif name == "crm_wompi_transactions":
                m.insert.side_effect = AssertionError("must not insert for an unknown lead")
            return m

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_wompi_settings():
            with pytest.raises(LookupError):
                CrmService().checkout_lead_payment("does-not-exist")
