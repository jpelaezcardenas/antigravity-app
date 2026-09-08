"""
Tests for GET /api/v1/pricing/pre-cotizacion (pricing-quote-engine, Stage 4).

Called as a plain async function rather than through TestClient, mirroring
test_radar_cash_projection.py's endpoint suite: `resolve_request_tenant_scope` is
monkeypatched in the endpoint module so the endpoint's own auth/tenant wiring is
exercised without a live Supabase connection.

Deliberate scoping of what is faked: the tenant resolver and the Supabase client are
stubbed (they are the collaborators *behind* the endpoint). `compute_pre_quote` is NOT
faked in the tests that assert tax-year/UVT behaviour — that is the boundary those tests
claim to verify, and mocking it would be the exact failure real-data-ingestion-mvp shipped
to production twice (ARCHITECTURE.md Decisión #22).
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import date

import fastapi
import pytest
from fastapi import HTTPException

from core.deps import get_current_user
from presentation import pricing_endpoints as mod


def _param_default(fn, name):
    params = inspect.signature(fn).parameters
    param = params.get(name)
    return param.default if param is not None else None


UVT_2025 = {"year": 2025, "value_cop": 49_799, "resolution": "Resolución DIAN 000193 de 2024"}


class _Query:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *_a, **_k):
        return self

    def eq(self, *_a, **_k):
        return self

    def gte(self, *_a, **_k):
        return self

    def lte(self, *_a, **_k):
        return self

    def in_(self, *_a, **_k):
        return self

    def maybe_single(self):
        return self

    def execute(self):
        return type("Result", (), {"data": self._rows})()


class _StubSupabase:
    """Twelve months of journal history plus a configurable uvt_values row."""

    def __init__(self, uvt_rows_by_year=None):
        self.uvt_rows_by_year = (
            uvt_rows_by_year if uvt_rows_by_year is not None else {2025: UVT_2025}
        )
        self.requested_uvt_years: list[int] = []

    def table(self, name):
        if name == "uvt_values":
            return _UvtQuery(self)
        if name == "erp_journal_entries":
            today = date.today()
            return _Query(
                [
                    {"id": f"e-{m}", "entry_date": date(
                        today.year if today.month - m > 0 else today.year - 1,
                        (today.month - m - 1) % 12 + 1,
                        15,
                    ).isoformat()}
                    for m in range(12)
                ]
            )
        if name == "erp_journal_lines":
            return _Query(
                [{"account_code": "4100", "debit_minor": 0, "credit_minor": 200_000_000_00}]
            )
        raise AssertionError(f"unexpected table {name!r}")


class _UvtQuery(_Query):
    def __init__(self, parent):
        super().__init__(None)
        self._parent = parent
        self._year = None

    def eq(self, _column, value):
        self._year = value
        self._parent.requested_uvt_years.append(value)
        return self

    def execute(self):
        return type("Result", (), {"data": self._parent.uvt_rows_by_year.get(self._year)})()


def _patch_supabase(monkeypatch, stub):
    monkeypatch.setattr(mod, "get_supabase", lambda: stub)


class TestAuthAndTenantScoping:
    def test_endpoint_requires_get_current_user(self):
        default = _param_default(mod.get_pre_quote, "user")
        assert isinstance(default, fastapi.params.Depends)
        assert default.dependency is get_current_user

    def test_endpoint_has_no_tenant_id_query_parameter(self):
        """ARCHITECTURE.md Decisión #17: the tenant comes from the caller's token only.
        The legacy /radar/risk-score tenant_id query param is not a pattern to copy."""
        params = inspect.signature(mod.get_pre_quote).parameters
        for name in params:
            assert "tenant" not in name.lower(), f"{name!r} would let a caller pick a tenant"

    def test_unresolved_tenant_gets_404_and_never_cliente_cero(self, monkeypatch):
        _patch_supabase(monkeypatch, _StubSupabase())
        monkeypatch.setattr(mod, "resolve_request_tenant_scope", lambda user, client: None)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(mod.get_pre_quote(user={"id": "u-unlinked", "resolved_tenant_id": None}))

        assert exc.value.status_code == 404

    def test_resolved_tenant_gets_a_pre_quote_for_its_own_tenant(self, monkeypatch):
        _patch_supabase(monkeypatch, _StubSupabase())
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="tenant-abc", all_tenants=False),
        )

        response = asyncio.run(mod.get_pre_quote(user={"id": "u-a", "resolved_tenant_id": "tenant-abc"}))

        assert response.client_tenant_id == "tenant-abc"
        assert response.estado == "ok"


class TestTaxYearSelection:
    def test_anio_gravable_defaults_to_the_previous_calendar_year(self, monkeypatch):
        """Today's filing season assesses last year's thresholds, which are expressed in
        THAT year's UVT — the verified rule that año gravable 2025 uses UVT 2025."""
        stub = _StubSupabase()
        _patch_supabase(monkeypatch, stub)
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        response = asyncio.run(mod.get_pre_quote(user={"id": "u", "resolved_tenant_id": "t"}))

        expected_year = date.today().year - 1
        assert response.anio_gravable == expected_year
        assert stub.requested_uvt_years == [expected_year]

    def test_explicit_year_selects_that_years_uvt(self, monkeypatch):
        uvt_2026 = {"year": 2026, "value_cop": 52_374, "resolution": "Res. 000238 de 2025"}
        stub = _StubSupabase(uvt_rows_by_year={2025: UVT_2025, 2026: uvt_2026})
        _patch_supabase(monkeypatch, stub)
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        response = asyncio.run(
            mod.get_pre_quote(anio_gravable=2026, user={"id": "u", "resolved_tenant_id": "t"})
        )

        assert response.anio_gravable == 2026
        assert response.uvt_cop == 52_374

    def test_unseeded_year_returns_an_explicit_state_not_a_wrong_number(self, monkeypatch):
        _patch_supabase(monkeypatch, _StubSupabase())
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        response = asyncio.run(
            mod.get_pre_quote(anio_gravable=2099, user={"id": "u", "resolved_tenant_id": "t"})
        )

        assert response.estado == "uvt_no_disponible"
        assert response.anio_gravable == 2099
        assert response.uvt_cop is None
        assert response.banda_sugerida is None


class TestResponseHonesty:
    def test_response_always_declares_its_missing_drivers(self, monkeypatch):
        _patch_supabase(monkeypatch, _StubSupabase())
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        response = asyncio.run(mod.get_pre_quote(user={"id": "u", "resolved_tenant_id": "t"}))

        assert "carga_laboral_nomina" in response.drivers_faltantes
        assert "patrimonio_bruto" in response.criterios_no_evaluables
        assert response.criterio_evaluado == "ingresos_brutos"

    def test_uvt_unavailable_state_still_declares_missing_drivers(self, monkeypatch):
        _patch_supabase(monkeypatch, _StubSupabase())
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        response = asyncio.run(
            mod.get_pre_quote(anio_gravable=2099, user={"id": "u", "resolved_tenant_id": "t"})
        )

        assert "carga_laboral_nomina" in response.drivers_faltantes

    def test_confidence_is_never_alta(self, monkeypatch):
        _patch_supabase(monkeypatch, _StubSupabase())
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        response = asyncio.run(mod.get_pre_quote(user={"id": "u", "resolved_tenant_id": "t"}))

        assert response.confianza != "alta"


class TestReadOnly:
    def test_endpoint_performs_no_writes(self, monkeypatch):
        """No approval_queue entry, no telemetry row — unlike /radar/proyeccion-caja,
        which takes an explicitly-justified adoption-tracking exception."""

        class _WriteTrap(_StubSupabase):
            def table(self, name):
                query = super().table(name)
                for forbidden in ("insert", "update", "upsert", "delete"):
                    setattr(query, forbidden, lambda *a, **k: pytest.fail("endpoint must not write"))
                return query

        _patch_supabase(monkeypatch, _WriteTrap())
        monkeypatch.setattr(
            mod,
            "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="t", all_tenants=False),
        )

        asyncio.run(mod.get_pre_quote(user={"id": "u", "resolved_tenant_id": "t"}))


class TestRouterMounting:
    def test_route_is_mounted_at_the_expected_path(self):
        from presentation.router import api_router

        paths = {route.path for route in api_router.routes}
        assert "/pricing/pre-cotizacion" in paths
