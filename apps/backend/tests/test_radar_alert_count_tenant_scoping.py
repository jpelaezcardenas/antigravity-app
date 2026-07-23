"""
Pure-mock test for radar_service._count_centinela_alerts_this_month
(centinela-tenant-scoped-alerts, Stage 6).

Radar's alert-frequency factor already resolved tenant_id -> company_id
correctly but never filtered centinela_alerts by tenant_id — a tenant's
Radar score could be inflated by another tenant's alerts sharing the same
company_id. No Supabase connection required (fully mocked client).
"""

from datetime import datetime
from unittest.mock import MagicMock

from services.radar_service import _count_centinela_alerts_this_month


def _mock_supabase(company_id: str, alert_rows: list) -> MagicMock:
    client = MagicMock()

    tenant_query = MagicMock()
    tenant_query.select.return_value = tenant_query
    tenant_query.eq.return_value = tenant_query
    tenant_query.single.return_value = tenant_query
    tenant_query.execute.return_value.data = {"company_id": company_id}

    alerts_query = MagicMock()
    alerts_query.select.return_value = alerts_query
    alerts_query.eq.return_value = alerts_query
    alerts_query.gte.return_value = alerts_query
    alerts_query.lt.return_value = alerts_query
    alerts_query.execute.return_value.data = alert_rows

    def table(name):
        return {"tenants": tenant_query, "centinela_alerts": alerts_query}[name]

    client.table.side_effect = table
    return client, alerts_query


class TestCountCentinelaAlertsThisMonth:
    def test_query_filters_by_company_id_and_tenant_id(self):
        client, alerts_query = _mock_supabase("ctx-medic", [{"id": "a1"}])
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        count = _count_centinela_alerts_this_month(client, "tenant-medic", month_start, today)

        assert count == 1
        alerts_query.eq.assert_any_call("company_id", "ctx-medic")
        alerts_query.eq.assert_any_call("tenant_id", "tenant-medic")

    def test_returns_zero_when_tenant_has_no_company_id(self):
        client, _ = _mock_supabase(None, [])
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        count = _count_centinela_alerts_this_month(client, "tenant-unmapped", month_start, today)

        assert count == 0
