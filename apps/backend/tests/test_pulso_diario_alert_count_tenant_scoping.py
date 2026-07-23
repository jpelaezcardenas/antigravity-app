"""
Pure-mock test for pulso_diario_service._count_alerts_generated
(centinela-tenant-scoped-alerts, Stage 6).

Before this fix, the query filtered `.eq("company_id", tenant_id)` — passing
a tenant UUID into the text company_id column, which always matched nothing,
so `alerts_generated` was silently always 0. No Supabase connection required.
"""

from unittest.mock import MagicMock

from services.pulso_diario_service import _count_alerts_generated


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


class TestCountAlertsGenerated:
    def test_resolves_company_id_and_filters_by_both_columns(self):
        client, alerts_query = _mock_supabase("ctx-medic", [{"id": "a1"}, {"id": "a2"}])

        count = _count_alerts_generated(client, "tenant-medic", "2026-07-23")

        assert count == 2
        alerts_query.eq.assert_any_call("company_id", "ctx-medic")
        alerts_query.eq.assert_any_call("tenant_id", "tenant-medic")
        # The old bug filtered company_id with the tenant UUID directly —
        # guard against regressing to that.
        assert ("company_id", "tenant-medic") not in [
            call.args for call in alerts_query.eq.call_args_list
        ]

    def test_returns_zero_when_tenant_has_no_company_id(self):
        client, _ = _mock_supabase(None, [])

        count = _count_alerts_generated(client, "tenant-unmapped", "2026-07-23")

        assert count == 0
