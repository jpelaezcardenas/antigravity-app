"""
Credential-free unit tests for crm_service's pivot/aggregation logic.

These mock the Supabase client entirely (no network, no env credentials required) so the
grid-building logic itself is verified independent of whether SUPABASE_SERVICE_ROLE_KEY is
configured in the local shell. The Supabase-hitting variant lives in test_crm_service.py
(gated by RUN_CRM_B2B=1, run in CI/Railway where credentials exist).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.crm_service import CrmService, _month_periods


def test_month_periods_generates_inclusive_first_of_month_range():
    assert _month_periods("2026-01-01", "2026-06-30") == [
        "2026-01-01",
        "2026-02-01",
        "2026-03-01",
        "2026-04-01",
        "2026-05-01",
        "2026-06-01",
    ]


def test_month_periods_single_month():
    assert _month_periods("2026-03-01", "2026-03-15") == ["2026-03-01"]


def _fake_supabase_client(clients_data, payments_data, tenant_id="tenant-1"):
    """Build a MagicMock mimicking the fluent supabase-py query builder chain used here."""

    def table_side_effect(name):
        table_mock = MagicMock()
        if name == "tenants":
            table_mock.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data={"id": tenant_id})
            )
        elif name == "b2b_clients":
            table_mock.select.return_value.eq.return_value.order.return_value.execute.return_value = (
                MagicMock(data=clients_data)
            )
        elif name == "b2b_payments":
            chain = table_mock.select.return_value.eq.return_value.gte.return_value.lte.return_value
            chain.execute.return_value = MagicMock(data=payments_data)
        return table_mock

    client = MagicMock()
    client.table.side_effect = table_side_effect
    return client


class TestB2bPaymentsGridPivotLogic:
    def test_pivots_payments_into_cells_by_client_and_period(self):
        clients = [{"id": "c1", "name": "Medic", "status": "activo"}]
        payments = [
            {"client_id": "c1", "period": "2026-01-01", "amount_cents": 200_000_00},
            {"client_id": "c1", "period": "2026-02-01", "amount_cents": 200_000_00},
        ]
        fake_client = _fake_supabase_client(clients, payments)

        with patch("services.crm_service.get_service_supabase", return_value=fake_client), patch(
            "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
        ):
            result = CrmService().b2b_payments_grid(from_period="2026-01-01", to_period="2026-02-28")

        assert result["source"] == "supabase"
        assert result["grid"]["cells"]["c1"]["2026-01-01"] == 200_000_00
        assert result["grid"]["cells"]["c1"]["2026-02-01"] == 200_000_00
        assert result["totals"]["by_client"]["c1"] == 400_000_00
        assert result["totals"]["by_period"]["2026-01-01"] == 200_000_00
        assert result["totals"]["grand_total"] == 400_000_00

    def test_period_with_no_payment_rows_totals_zero(self):
        clients = [{"id": "c1", "name": "Medic", "status": "activo"}]
        payments = []
        fake_client = _fake_supabase_client(clients, payments)

        with patch("services.crm_service.get_service_supabase", return_value=fake_client), patch(
            "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
        ):
            result = CrmService().b2b_payments_grid(from_period="2026-01-01", to_period="2026-01-31")

        assert result["totals"]["grand_total"] == 0
        assert result["totals"]["by_period"]["2026-01-01"] == 0

    def test_supabase_unreachable_falls_back_to_demo(self):
        with patch("services.crm_service.get_service_supabase", side_effect=Exception("network down")), patch(
            "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
        ):
            result = CrmService().b2b_payments_grid()

        assert result["source"] == "demo_fallback"
        assert len(result["grid"]["clients"]) > 0


class TestListB2bClientsFallback:
    def test_falls_back_to_demo_when_supabase_env_missing(self):
        with patch("os.getenv", return_value=None):
            result = CrmService().list_b2b_clients()

        assert result["source"] == "demo_fallback"
        assert len(result["items"]) > 0
