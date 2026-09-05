"""
Tests for the 13-week cash projection module (radar-cash-projection-13w).

Task 1.1: pure-mock unit tests for the shared weekly net-flux helper
`_weekly_net_flux`, extracted from the query shape already used by
`calculate_cashflow_forecast` (see design.md Decision #1). No live Supabase
connection required — fully mocked client, mirroring the pattern in
test_radar_alert_count_tenant_scoping.py.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import inspect

import fastapi
from unittest.mock import AsyncMock, MagicMock, patch

from core.deps import get_current_user
from services.radar_service import (
    _weekly_net_flux,
    calculate_cash_projection_13w,
    generate_alerta_narrativa,
)


def _mock_supabase(dian_rows: list, erp_entry_rows: list, erp_line_rows: list) -> MagicMock:
    client = MagicMock()

    dian_query = MagicMock()
    dian_query.select.return_value = dian_query
    dian_query.eq.return_value = dian_query
    dian_query.gte.return_value = dian_query
    dian_query.lte.return_value = dian_query
    dian_query.execute.return_value.data = dian_rows

    erp_entries_query = MagicMock()
    erp_entries_query.select.return_value = erp_entries_query
    erp_entries_query.eq.return_value = erp_entries_query
    erp_entries_query.gte.return_value = erp_entries_query
    erp_entries_query.lte.return_value = erp_entries_query
    erp_entries_query.execute.return_value.data = erp_entry_rows

    erp_lines_query = MagicMock()
    erp_lines_query.select.return_value = erp_lines_query
    erp_lines_query.eq.return_value = erp_lines_query
    erp_lines_query.in_.return_value = erp_lines_query
    erp_lines_query.execute.return_value.data = erp_line_rows

    def table(name):
        return {
            "dian_xml_documents": dian_query,
            "erp_journal_entries": erp_entries_query,
            "erp_journal_lines": erp_lines_query,
        }[name]

    client.table.side_effect = table
    return client


class TestWeeklyNetFlux:
    def test_computes_net_flux_for_a_single_week(self):
        client = _mock_supabase(
            dian_rows=[{"total_amount_minor": 11_900_000}],
            erp_entry_rows=[{"id": "entry-1"}],
            erp_line_rows=[{"debit_minor": 2_000_000}],
        )

        week_start = datetime(2026, 8, 24)
        week_end = datetime(2026, 8, 31)

        net_flux = asyncio.run(
            _weekly_net_flux("tenant-abc", week_start, week_end, supabase_client=client)
        )

        assert net_flux == 11_900_000 - 2_000_000

    def test_returns_zero_for_tenant_with_no_rows_in_window(self):
        client = _mock_supabase(dian_rows=[], erp_entry_rows=[], erp_line_rows=[])

        week_start = datetime(2026, 8, 24)
        week_end = datetime(2026, 8, 31)

        net_flux = asyncio.run(
            _weekly_net_flux("tenant-empty", week_start, week_end, supabase_client=client)
        )

        assert net_flux == 0

    def test_scopes_dian_and_erp_queries_to_tenant_and_window(self):
        client = _mock_supabase(dian_rows=[], erp_entry_rows=[], erp_line_rows=[])
        dian_query = client.table("dian_xml_documents")
        erp_entries_query = client.table("erp_journal_entries")

        week_start = datetime(2026, 8, 24)
        week_end = datetime(2026, 8, 31)

        asyncio.run(
            _weekly_net_flux("tenant-scoped", week_start, week_end, supabase_client=client)
        )

        dian_query.eq.assert_any_call("tenant_id", "tenant-scoped")
        erp_entries_query.eq.assert_any_call("tenant_id", "tenant-scoped")


def _mock_entries_client(entry_dates: list) -> MagicMock:
    """Mock a Supabase client whose erp_journal_entries table returns the
    given entry_date rows, used to drive the history-weeks-count gate.
    """
    client = MagicMock()

    entries_query = MagicMock()
    entries_query.select.return_value = entries_query
    entries_query.eq.return_value = entries_query
    entries_query.gte.return_value = entries_query
    entries_query.lte.return_value = entries_query
    entries_query.execute.return_value.data = [{"entry_date": d} for d in entry_dates]

    client.table.return_value = entries_query
    return client


class TestCalculateCashProjection13w:
    """
    Task 2.1-2.4: tests for calculate_cash_projection_13w, patching the two
    Shadow GL primitives it composes (_weekly_net_flux and the existing
    _compute_caja_real_balance from financials_service) so these tests focus
    purely on the projection/confidence/methodology logic, not on re-testing
    Shadow GL query shapes already covered above and in financials_service's
    own tests.
    """

    def _entry_dates_for_n_weeks(self, n: int) -> list:
        today = datetime.utcnow()
        return [(today - timedelta(weeks=i)).date().isoformat() for i in range(n)]

    @patch("services.radar_service._compute_caja_real_balance", return_value=5_000_000)
    @patch("services.radar_service._weekly_net_flux", new_callable=AsyncMock, return_value=700_000)
    def test_returns_exactly_13_weekly_entries_with_required_fields(
        self, mock_weekly_flux, mock_balance
    ):
        client = _mock_entries_client(self._entry_dates_for_n_weeks(12))

        result = asyncio.run(
            calculate_cash_projection_13w("tenant-abc", supabase_client=client)
        )

        assert result["estado"] == "ok"
        assert len(result["semanas"]) == 13
        for week in result["semanas"]:
            assert set(week.keys()) == {"semana", "fecha_inicio", "caja_proyectada", "confianza"}

    @patch("services.radar_service._compute_caja_real_balance", return_value=5_000_000)
    @patch("services.radar_service._weekly_net_flux", new_callable=AsyncMock, return_value=700_000)
    def test_confidence_bands_media_then_baja_never_alta(self, mock_weekly_flux, mock_balance):
        client = _mock_entries_client(self._entry_dates_for_n_weeks(12))

        result = asyncio.run(
            calculate_cash_projection_13w("tenant-abc", supabase_client=client)
        )

        semanas = result["semanas"]
        for week in semanas[:4]:
            assert week["confianza"] == "media"
        for week in semanas[4:]:
            assert week["confianza"] == "baja"
        assert all(week["confianza"] != "alta" for week in semanas)

    @patch("services.radar_service._compute_caja_real_balance", return_value=5_000_000)
    @patch("services.radar_service._weekly_net_flux", new_callable=AsyncMock, return_value=700_000)
    def test_insufficient_history_returns_honest_empty_state(self, mock_weekly_flux, mock_balance):
        client = _mock_entries_client(self._entry_dates_for_n_weeks(2))

        result = asyncio.run(
            calculate_cash_projection_13w("tenant-new", supabase_client=client)
        )

        assert result["estado"] == "sin_historico_suficiente"
        assert result["semanas"] is None
        mock_weekly_flux.assert_not_called()

    @patch("services.radar_service._compute_caja_real_balance", return_value=5_000_000)
    @patch("services.radar_service._weekly_net_flux", new_callable=AsyncMock, return_value=700_000)
    def test_methodology_and_tax_field_are_always_honest(self, mock_weekly_flux, mock_balance):
        client = _mock_entries_client(self._entry_dates_for_n_weeks(12))

        result = asyncio.run(
            calculate_cash_projection_13w("tenant-abc", supabase_client=client)
        )

        assert result["metodologia"] == "solo_historico"
        assert result["impuesto_futuro_estimado"] is None


def _mock_two_tenant_client(tenant_data: dict) -> MagicMock:
    """
    Mock a Supabase client whose erp_journal_entries/erp_journal_lines/
    dian_xml_documents tables return rows scoped strictly to whichever
    tenant_id was passed to .eq("tenant_id", ...) — used to prove
    calculate_cash_projection_13w never mixes one tenant's Shadow GL rows
    into another tenant's projection (mirrors
    test_radar_alert_count_tenant_scoping.py's per-tenant mock pattern).

    `tenant_data` maps tenant_id -> {"entries": [...], "dian": [...], "erp_lines": [...]}
    """
    client = MagicMock()

    def make_query(rows_for_tenant_fn):
        query = MagicMock()
        state = {"tenant_id": None}

        def eq(field, value):
            if field == "tenant_id":
                state["tenant_id"] = value
            return query

        query.select.return_value = query
        query.eq.side_effect = eq
        query.gte.return_value = query
        query.lte.return_value = query
        query.in_.return_value = query

        def execute():
            result = MagicMock()
            result.data = rows_for_tenant_fn(state["tenant_id"])
            return result

        query.execute.side_effect = execute
        return query

    entries_query = make_query(
        lambda tid: tenant_data.get(tid, {}).get("entries", [])
    )
    dian_query = make_query(lambda tid: tenant_data.get(tid, {}).get("dian", []))
    erp_lines_query = make_query(
        lambda tid: tenant_data.get(tid, {}).get("erp_lines", [])
    )

    def table(name):
        return {
            "erp_journal_entries": entries_query,
            "dian_xml_documents": dian_query,
            "erp_journal_lines": erp_lines_query,
        }[name]

    client.table.side_effect = table
    return client


class TestTenantIsolation:
    """Task 3.1-3.2: Tenant A's projection must never reflect Tenant B's rows."""

    @patch("services.radar_service._compute_caja_real_balance")
    def test_tenant_a_projection_never_reflects_tenant_b_rows(self, mock_balance):
        today = datetime.utcnow()

        def entry_dates(n: int) -> list:
            return [
                {"id": f"entry-{i}", "entry_date": (today - timedelta(weeks=i)).date().isoformat()}
                for i in range(n)
            ]

        tenant_data = {
            "tenant-a": {
                "entries": entry_dates(12),
                "dian": [{"total_amount_minor": 1_000_000}],
                "erp_lines": [],
            },
            "tenant-b": {
                "entries": entry_dates(12),
                "dian": [{"total_amount_minor": 99_000_000}],  # deliberately huge
                "erp_lines": [],
            },
        }
        client = _mock_two_tenant_client(tenant_data)

        def balance_for_tenant(supabase, tenant_id, as_of_date):
            return {"tenant-a": 5_000_000, "tenant-b": 500_000_000}[tenant_id]

        mock_balance.side_effect = balance_for_tenant

        result_a = asyncio.run(
            calculate_cash_projection_13w("tenant-a", supabase_client=client)
        )
        result_b = asyncio.run(
            calculate_cash_projection_13w("tenant-b", supabase_client=client)
        )

        assert result_a["client_tenant_id"] == "tenant-a"
        assert result_b["client_tenant_id"] == "tenant-b"
        # Tenant A's week-1 projection must be grounded in tenant A's own
        # (small) balance/flux, never tenant B's (much larger) figures.
        assert result_a["semanas"][0]["caja_proyectada"] < result_b["semanas"][0]["caja_proyectada"]
        assert result_a["semanas"][0]["caja_proyectada"] < 100_000_000


def _user_dependency_default(fn, name="user"):
    params = inspect.signature(fn).parameters
    param = params.get(name)
    return param.default if param is not None else None


class TestCashProjectionEndpoint:
    """
    Task 4.1-4.3: GET /api/v1/radar/proyeccion-caja, called as a plain async
    function (mirrors test_agent_stub_endpoints_tenant.py's pattern) rather
    than via TestClient — `resolve_request_tenant_scope` is monkeypatched in
    the endpoint module so these tests exercise the endpoint's own auth/
    tenant-resolution wiring without a live Supabase connection.
    """

    def test_endpoint_requires_get_current_user(self):
        from presentation import radar_endpoints as mod

        default = _user_dependency_default(mod.get_cash_projection)
        assert isinstance(default, fastapi.params.Depends)
        assert default.dependency is get_current_user

    def test_unresolved_tenant_gets_graceful_empty_response_not_404(self, monkeypatch):
        from presentation import radar_endpoints as mod

        monkeypatch.setattr(mod, "resolve_request_tenant_scope", lambda user, client: None)
        user = {"id": "user-unlinked", "resolved_tenant_id": None}

        response = asyncio.run(mod.get_cash_projection(user=user))

        assert response.estado == "tenant_no_resuelto"
        assert response.semanas is None

    def test_resolved_tenant_gets_full_response_shape(self, monkeypatch):
        from presentation import radar_endpoints as mod

        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="tenant-cliente-cero", all_tenants=True),
        )

        async def fake_projection(tenant_id, supabase_client=None):
            return {
                "client_tenant_id": tenant_id,
                "generado_en": "2026-09-03T08:00:00Z",
                "metodologia": "solo_historico",
                "impuesto_futuro_estimado": None,
                "estado": "ok",
                "semanas": [
                    {"semana": i, "fecha_inicio": "2026-09-07", "caja_proyectada": 1_000_000, "confianza": "media" if i <= 4 else "baja"}
                    for i in range(1, 14)
                ],
            }

        monkeypatch.setattr(mod, "calculate_cash_projection_13w", fake_projection)
        user = {"id": "user-a", "resolved_tenant_id": "tenant-cliente-cero"}

        response = asyncio.run(mod.get_cash_projection(user=user))

        assert response.client_tenant_id == "tenant-cliente-cero"
        assert response.metodologia == "solo_historico"
        assert response.estado == "ok"
        assert len(response.semanas) == 13
        assert response.alerta_narrativa is not None
        assert response.impuesto_futuro_estimado is None


class TestRouteRegistration:
    """
    The endpoint must be reachable at the path the spec and the PWA client
    agree on. Calling the handler function directly (as the tests above do)
    passes even when the router is mounted somewhere else entirely — which is
    exactly what happened on the first deploy: radar_endpoints was only mounted
    at /agents/radar-predictivo, so production answered 404 for the documented
    path. This test pins the real mounted path.
    """

    def test_proyeccion_caja_is_mounted_at_api_v1_radar(self):
        from presentation.router import api_router

        paths = {route.path for route in api_router.routes}
        assert "/radar/proyeccion-caja" in paths

    def test_legacy_risk_score_path_is_unchanged(self):
        from presentation.router import api_router

        paths = {route.path for route in api_router.routes}
        assert "/agents/radar-predictivo/risk-score" in paths


class TestGenerateAlertaNarrativa:
    """Task 5.1: dedicated coverage for the two phrasing branches + the empty case."""

    def test_declining_cash_gets_bajando_phrasing(self):
        semanas = [
            {"semana": 1, "caja_proyectada": 8_200_000_00},
            {"semana": 13, "caja_proyectada": 3_100_000_00},
        ]
        narrativa = generate_alerta_narrativa(semanas)
        assert "bajar" in narrativa
        assert "COP" in narrativa

    def test_stable_cash_gets_estable_phrasing(self):
        semanas = [
            {"semana": 1, "caja_proyectada": 5_000_000_00},
            {"semana": 13, "caja_proyectada": 5_200_000_00},
        ]
        narrativa = generate_alerta_narrativa(semanas)
        assert "estable" in narrativa
        assert "COP" in narrativa

    def test_no_weeks_gets_honest_no_history_message(self):
        narrativa = generate_alerta_narrativa(None)
        assert "historial" in narrativa
