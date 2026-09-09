"""
Tests for the operator pre-quote route and the band price range in the response
(pricing-catalog-and-operator-quote, Stages 3-4).

The route exists because the engine shipped unusable for its actual purpose: it resolves the
CALLER's tenant, so in the Búnker — where the caller is a Contexia operator resolving to Cliente
Cero — it returned Contexia's own numbers instead of the prospect's.

Scoping of what is faked: the tenant resolver and the Supabase client are stubbed (collaborators
behind the endpoint). `compute_pre_quote` is NOT faked in the tests that assert pricing or tenant
targeting — that is the boundary those tests claim to verify.
"""

from __future__ import annotations

import asyncio
import inspect

import pytest
from fastapi import HTTPException

from core.deps import get_current_user
from core.pricing_catalog import SERVICE_BAND_PRICING
from presentation import pricing_endpoints as mod

UVT_2025 = {"year": 2025, "value_cop": 49_799, "resolution": "Resolución DIAN 000193 de 2024"}


class _Query:
    def __init__(self, rows, recorder=None, table=None):
        self._rows = rows
        self._recorder = recorder
        self._table = table

    def select(self, *_a, **_k):
        return self

    def eq(self, col, val):
        if self._recorder is not None:
            self._recorder.append((self._table, col, val))
        return self

    def gte(self, *_a, **_k):
        return self

    def lte(self, *_a, **_k):
        return self

    def in_(self, *_a, **_k):
        return self

    def maybe_single(self):
        return self

    def single(self):
        return self

    def execute(self):
        return type("R", (), {"data": self._rows})()


class _Stub:
    """Twelve months of journal history for whichever tenant is queried, plus a roster row."""

    def __init__(self, roster_row=None, uvt=UVT_2025):
        self.roster_row = roster_row
        self.uvt = uvt
        self.filters: list = []

    def table(self, name):
        if name == "uvt_values":
            return _Query(self.uvt)
        if name == "b2b_clients":
            return _Query(self.roster_row, self.filters, "b2b_clients")
        if name == "erp_journal_entries":
            from datetime import date

            today = date.today()
            rows = [
                {
                    "id": f"e-{m}",
                    "entry_date": date(
                        today.year if today.month - m > 0 else today.year - 1,
                        (today.month - m - 1) % 12 + 1,
                        15,
                    ).isoformat(),
                }
                for m in range(12)
            ]
            return _Query(rows, self.filters, "erp_journal_entries")
        if name == "erp_journal_lines":
            # ~2.000 UVT annualised -> lands in the estandar band.
            return _Query(
                [{"account_code": "4100", "debit_minor": 0, "credit_minor": 99_598_000_00}],
                self.filters,
                "erp_journal_lines",
            )
        raise AssertionError(f"unexpected table {name!r}")


def _operator(monkeypatch, stub):
    monkeypatch.setattr(mod, "get_supabase", lambda: stub)
    monkeypatch.setattr(
        mod,
        "resolve_request_tenant_scope",
        lambda user, client: mod.TenantScope(tenant_id="cliente-cero", all_tenants=True),
    )


def _single_tenant_client(monkeypatch, stub):
    monkeypatch.setattr(mod, "get_supabase", lambda: stub)
    monkeypatch.setattr(
        mod,
        "resolve_request_tenant_scope",
        lambda user, client: mod.TenantScope(tenant_id="tenant-b", all_tenants=False),
    )


ROSTER = {"id": "client-1", "name": "Cliente Uno", "client_tenant_id": "tenant-cliente-uno"}


class TestOperatorAccess:
    def test_route_requires_authentication(self):
        params = inspect.signature(mod.get_client_pre_quote).parameters
        default = params["user"].default
        assert default.dependency is get_current_user

    def test_operator_gets_a_pre_quote_for_the_named_client(self, monkeypatch):
        stub = _Stub(roster_row=ROSTER)
        _operator(monkeypatch, stub)

        response = asyncio.run(
            mod.get_client_pre_quote(b2b_client_id="client-1", user={"id": "op"})
        )

        assert response.estado == "ok"
        # The decisive assertion: scoped to the CLIENT's tenant, not the operator's own.
        assert response.client_tenant_id == "tenant-cliente-uno"
        assert response.client_tenant_id != "cliente-cero"

    def test_shadow_gl_is_queried_for_the_clients_tenant(self, monkeypatch):
        stub = _Stub(roster_row=ROSTER)
        _operator(monkeypatch, stub)

        asyncio.run(mod.get_client_pre_quote(b2b_client_id="client-1", user={"id": "op"}))

        gl_filters = [f for f in stub.filters if f[0] == "erp_journal_entries"]
        assert ("erp_journal_entries", "tenant_id", "tenant-cliente-uno") in gl_filters

    def test_single_tenant_client_gets_404_not_403(self, monkeypatch):
        """Anti-enumeration (Decisión #17): a B2B client must not learn the route exists."""
        stub = _Stub(roster_row=ROSTER)
        _single_tenant_client(monkeypatch, stub)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(mod.get_client_pre_quote(b2b_client_id="client-1", user={"id": "u"}))

        assert exc.value.status_code == 404

    def test_unresolved_scope_gets_404(self, monkeypatch):
        stub = _Stub(roster_row=ROSTER)
        monkeypatch.setattr(mod, "get_supabase", lambda: stub)
        monkeypatch.setattr(mod, "resolve_request_tenant_scope", lambda user, client: None)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(mod.get_client_pre_quote(b2b_client_id="client-1", user={"id": "u"}))

        assert exc.value.status_code == 404

    def test_unknown_client_id_gets_404(self, monkeypatch):
        stub = _Stub(roster_row=None)
        _operator(monkeypatch, stub)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(mod.get_client_pre_quote(b2b_client_id="nope", user={"id": "op"}))

        assert exc.value.status_code == 404


class TestRosterClientWithoutTenant:
    def test_null_client_tenant_reports_an_explicit_state_not_a_500(self, monkeypatch):
        """A roster row created before provisioning has no tenant. That must read as
        'not provisioned', never as an empty pre-quote that looks like 'no activity'."""
        stub = _Stub(roster_row={"id": "c9", "name": "Sin Tenant", "client_tenant_id": None})
        _operator(monkeypatch, stub)

        response = asyncio.run(
            mod.get_client_pre_quote(b2b_client_id="c9", user={"id": "op"})
        )

        assert response.estado == "cliente_sin_tenant"
        assert response.banda_sugerida is None
        assert response.ingresos_anualizados_cop is None


class TestBandPriceInResponse:
    def test_suggested_band_carries_its_price_range(self, monkeypatch):
        stub = _Stub(roster_row=ROSTER)
        _operator(monkeypatch, stub)

        response = asyncio.run(
            mod.get_client_pre_quote(b2b_client_id="client-1", user={"id": "op"})
        )

        assert response.banda_sugerida == "estandar"
        expected = SERVICE_BAND_PRICING["estandar"]
        assert response.banda_precio_min_cents == expected.min_cents
        assert response.banda_precio_max_cents == expected.max_cents

    def test_no_band_means_no_price_rather_than_zero(self, monkeypatch):
        """A zeroed price would read as 'free'. Absent must stay absent."""
        stub = _Stub(roster_row={"id": "c9", "name": "X", "client_tenant_id": None})
        _operator(monkeypatch, stub)

        response = asyncio.run(mod.get_client_pre_quote(b2b_client_id="c9", user={"id": "op"}))

        assert response.banda_precio_min_cents is None
        assert response.banda_precio_max_cents is None


class TestSelfRouteContractUnchanged:
    def test_self_route_still_takes_no_tenant_or_client_parameter(self):
        """Decisión #17 is untouched: selecting a target is legitimate only on the
        operator route, for a scope already entitled to every tenant."""
        params = inspect.signature(mod.get_pre_quote).parameters
        for name in params:
            assert "tenant" not in name.lower()
            assert "client" not in name.lower()


class TestRouteMounting:
    def test_operator_route_is_mounted(self):
        from presentation.router import api_router

        paths = {r.path for r in api_router.routes}
        assert "/pricing/pre-cotizacion/cliente/{b2b_client_id}" in paths
