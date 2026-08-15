"""
Unit tests for retention_service.py (retention-loop).

Rule evaluation is pure (no I/O) so it's testable without Supabase credentials — same philosophy
as centinela_service.py's CentinelaRule classes. save_alerts()/get_alerts() mock the Supabase
client directly (no real network), same pattern as other service tests in this repo.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from services.retention_service import (
    MissedPaymentRule,
    PaymentDropRule,
    RetentionService,
)


def _client(client_id="c-1", status="activo"):
    return {"id": client_id, "name": "Test Client", "status": status}


def _payment(client_id, period, amount_cents):
    return {"client_id": client_id, "period": period, "amount_cents": amount_cents}


class TestMissedPaymentRule:
    def test_fires_when_no_payment_in_most_recent_complete_month(self):
        rule = MissedPaymentRule()
        client = _client()
        payments = [_payment("c-1", "2026-06-01", 500000)]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 15))
        assert alert is not None
        assert alert["rule_id"] == "missed_payment"
        assert alert["client_id"] == "c-1"

    def test_does_not_fire_when_most_recent_complete_month_is_paid(self):
        rule = MissedPaymentRule()
        client = _client()
        payments = [_payment("c-1", "2026-07-01", 500000)]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 15))
        assert alert is None

    def test_current_in_progress_month_is_not_evaluated(self):
        """Missing August's row on Aug 15 shouldn't trigger — only July (the last
        complete month) is checked."""
        rule = MissedPaymentRule()
        client = _client()
        payments = [_payment("c-1", "2026-07-01", 500000)]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 3))
        assert alert is None

    def test_inactive_client_is_never_evaluated(self):
        rule = MissedPaymentRule()
        client = _client(status="inactivo")
        alert = rule.evaluate(client, [], today=date(2026, 8, 15))
        assert alert is None


class TestPaymentDropRule:
    def test_fires_on_a_material_drop_vs_trailing_average(self):
        rule = PaymentDropRule()
        client = _client()
        payments = [
            _payment("c-1", "2026-04-01", 1000000),
            _payment("c-1", "2026-05-01", 1000000),
            _payment("c-1", "2026-06-01", 1000000),
            _payment("c-1", "2026-07-01", 100000),  # 90% drop
        ]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 15))
        assert alert is not None
        assert alert["rule_id"] == "payment_drop"

    def test_does_not_fire_on_a_stable_or_rising_payment(self):
        rule = PaymentDropRule()
        client = _client()
        payments = [
            _payment("c-1", "2026-04-01", 1000000),
            _payment("c-1", "2026-05-01", 1000000),
            _payment("c-1", "2026-06-01", 1000000),
            _payment("c-1", "2026-07-01", 1100000),
        ]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 15))
        assert alert is None

    def test_fewer_than_3_prior_payments_is_not_evaluated(self):
        rule = PaymentDropRule()
        client = _client()
        payments = [
            _payment("c-1", "2026-06-01", 1000000),
            _payment("c-1", "2026-07-01", 100000),
        ]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 15))
        assert alert is None

    def test_inactive_client_is_never_evaluated(self):
        rule = PaymentDropRule()
        client = _client(status="inactivo")
        payments = [
            _payment("c-1", "2026-04-01", 1000000),
            _payment("c-1", "2026-05-01", 1000000),
            _payment("c-1", "2026-06-01", 1000000),
            _payment("c-1", "2026-07-01", 100000),
        ]
        alert = rule.evaluate(client, payments, today=date(2026, 8, 15))
        assert alert is None


class TestRetentionServiceEvaluateRoster:
    def test_aggregates_alerts_across_multiple_clients(self):
        service = RetentionService()
        clients = [_client("c-1"), _client("c-2")]
        payments = [_payment("c-1", "2026-06-01", 500000)]  # c-1 missed July+Aug; c-2 no payments
        alerts = service.evaluate_roster(clients, payments, today=date(2026, 8, 15))
        client_ids = {a["client_id"] for a in alerts}
        assert "c-1" in client_ids
        assert "c-2" in client_ids

    def test_a_healthy_client_produces_no_alerts(self):
        service = RetentionService()
        clients = [_client("c-1")]
        payments = [
            _payment("c-1", "2026-05-01", 1000000),
            _payment("c-1", "2026-06-01", 1000000),
            _payment("c-1", "2026-07-01", 1000000),
        ]
        alerts = service.evaluate_roster(clients, payments, today=date(2026, 8, 15))
        assert alerts == []


class TestRetentionServicePersistence:
    def test_save_alerts_requires_a_tenant_id(self):
        service = RetentionService()
        with pytest.raises(Exception):
            service.save_alerts([{"rule_id": "missed_payment", "client_id": "c-1"}], tenant_id=None)

    def test_save_alerts_stamps_every_row_with_the_tenant_id(self):
        service = RetentionService()
        fake_supabase = MagicMock()
        fake_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "alert-1"}
        ]
        with patch("services.retention_service.get_service_supabase", return_value=fake_supabase):
            saved_ids = service.save_alerts(
                [{"rule_id": "missed_payment", "client_id": "c-1", "severity": "warning", "message": "m"}],
                tenant_id="tenant-abc",
            )
        assert saved_ids == ["alert-1"]
        inserted_row = fake_supabase.table.return_value.insert.call_args[0][0]
        assert inserted_row["tenant_id"] == "tenant-abc"

    def test_get_alerts_scopes_by_tenant_id(self):
        service = RetentionService()
        fake_supabase = MagicMock()
        query = fake_supabase.table.return_value.select.return_value.eq.return_value
        query.order.return_value.limit.return_value.execute.return_value.data = [{"id": "alert-1"}]
        with patch("services.retention_service.get_service_supabase", return_value=fake_supabase):
            result = service.get_alerts(tenant_id="tenant-abc")
        assert result == [{"id": "alert-1"}]
        fake_supabase.table.return_value.select.return_value.eq.assert_called_with(
            "tenant_id", "tenant-abc"
        )


class TestEvaluateAndPersist:
    def test_does_not_re_persist_an_already_existing_alert(self):
        """A duplicate alert for the same (client, rule, message) already in get_alerts()
        must not be re-inserted — otherwise every tab load would flood the table."""
        service = RetentionService()
        fake_supabase = MagicMock()
        tenants_mock = MagicMock()
        clients_mock = MagicMock()
        payments_mock = MagicMock()
        alerts_mock = MagicMock()

        tenants_mock.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
            "id": "tenant-cc"
        }
        clients_mock.select.return_value.eq.return_value.execute.return_value.data = [
            {"id": "c-1", "name": "Client 1", "status": "activo"}
        ]
        payments_mock.select.return_value.eq.return_value.execute.return_value.data = []
        existing_alert = {
            "id": "existing-1",
            "client_id": "c-1",
            "rule_id": "missed_payment",
            "message": "Sin pago registrado para Client 1 en 2026-07-01.",
        }
        alerts_mock.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            existing_alert
        ]

        def table_side_effect(name):
            return {
                "tenants": tenants_mock,
                "b2b_clients": clients_mock,
                "b2b_payments": payments_mock,
                "retention_alerts": alerts_mock,
            }[name]

        fake_supabase.table.side_effect = table_side_effect

        with patch("services.retention_service.get_service_supabase", return_value=fake_supabase), patch(
            "services.retention_service.date"
        ) as mock_date:
            mock_date.today.return_value = date(2026, 8, 15)
            result = service.evaluate_and_persist()

        alerts_mock.insert.assert_not_called()
        assert result == [existing_alert]
