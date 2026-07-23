"""
Tests for POST /api/v1/centinela/evaluate and GET /api/v1/centinela/alerts/{company_id}
tenant resolution (centinela-tenant-scoped-alerts).

Mirrors the pattern established by test_financials_endpoint_tenant_scoping.py:
monkeypatched service calls + fake user dicts, calling the endpoint functions
directly (no HTTP client), so these run without a real Supabase connection.
"""

import asyncio

import pytest

from core.deps import _STAGING_USER
from presentation.centinela_endpoints import (
    CentinelaEvaluateRequest,
    evaluate_centinela,
    get_company_alerts,
)


def run(coro):
    return asyncio.run(coro)


class TestEvaluateEndpointTenantScoping:
    def test_post_evaluate_saves_with_resolved_tenant(self, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        captured = {}

        def fake_save_alerts(self, alerts, tenant_id):
            captured["tenant_id"] = tenant_id
            return ["alert-1"]

        monkeypatch.setattr(
            endpoints_module.CentinelaService, "save_alerts", fake_save_alerts
        )

        user = {"id": "user-a", "resolved_tenant_id": "tenant-medic"}
        request = CentinelaEvaluateRequest(
            company_id="ctx-001",
            financial_data={"regime": "Régimen Simple", "annual_revenue": 999999999999},
            save_alerts=True,
        )
        response = run(evaluate_centinela(request, user=user))

        assert captured["tenant_id"] == "tenant-medic"
        assert response.saved_alert_ids == ["alert-1"]
        assert response.save_skipped_reason is None

    def test_post_evaluate_staging_saves_with_explicit_cliente_cero(self, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        captured = {}

        def fake_save_alerts(self, alerts, tenant_id):
            captured["tenant_id"] = tenant_id
            return ["alert-1"]

        monkeypatch.setattr(
            endpoints_module.CentinelaService, "save_alerts", fake_save_alerts
        )
        import core.tenant_context as tenant_context_module
        monkeypatch.setattr(
            tenant_context_module,
            "resolve_cliente_cero_tenant_id",
            lambda client: "cliente-cero-tenant-id",
        )

        request = CentinelaEvaluateRequest(
            company_id="ctx-001",
            financial_data={"regime": "Régimen Simple", "annual_revenue": 999999999999},
            save_alerts=True,
        )
        response = run(evaluate_centinela(request, user=dict(_STAGING_USER)))

        assert captured["tenant_id"] == "cliente-cero-tenant-id"
        assert response.saved_alert_ids == ["alert-1"]

    def test_post_evaluate_authenticated_unresolved_skips_save(self, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        def must_not_be_called(self, alerts, tenant_id):
            raise AssertionError("save_alerts must not be called for an unresolved tenant")

        def must_not_resolve_cliente_cero(client):
            raise AssertionError("Cliente Cero fallback must not be used for an authenticated, unresolved caller")

        monkeypatch.setattr(
            endpoints_module.CentinelaService, "save_alerts", must_not_be_called
        )
        import core.tenant_context as tenant_context_module
        monkeypatch.setattr(
            tenant_context_module, "resolve_cliente_cero_tenant_id", must_not_resolve_cliente_cero
        )

        user = {
            "id": "76680e1f-2943-4235-8501-18b090d59257",
            "email": "growth@contexia.online",
            "resolved_user_id": None,
            "resolved_tenant_id": None,
        }
        request = CentinelaEvaluateRequest(
            company_id="ctx-001",
            financial_data={"regime": "Régimen Simple", "annual_revenue": 999999999999},
            save_alerts=True,
        )
        response = run(evaluate_centinela(request, user=user))

        assert response.saved_alert_ids == []
        assert response.save_skipped_reason == "tenant_unresolved"
        assert response.alert_count > 0  # evaluation itself is unaffected

    def test_post_evaluate_respects_save_alerts_false(self, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        def must_not_be_called(self, alerts, tenant_id):
            raise AssertionError("save_alerts must not be called when save_alerts=False")

        monkeypatch.setattr(
            endpoints_module.CentinelaService, "save_alerts", must_not_be_called
        )

        user = {"id": "user-a", "resolved_tenant_id": "tenant-medic"}
        request = CentinelaEvaluateRequest(
            company_id="ctx-001",
            financial_data={"regime": "Régimen Simple", "annual_revenue": 999999999999},
            save_alerts=False,
        )
        response = run(evaluate_centinela(request, user=user))

        assert response.saved_alert_ids == []
        assert response.save_skipped_reason is None


class TestGetAlertsEndpointTenantScoping:
    def test_get_alerts_filters_by_caller_tenant(self, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        captured = {}

        def fake_get_alerts(self, company_id, tenant_id, limit=20, severity=None):
            captured["company_id"] = company_id
            captured["tenant_id"] = tenant_id
            return []

        monkeypatch.setattr(
            endpoints_module.CentinelaService, "get_alerts_for_company", fake_get_alerts
        )

        user = {"id": "user-a", "resolved_tenant_id": "tenant-medic"}
        run(get_company_alerts("ctx-001", user=user))

        assert captured["company_id"] == "ctx-001"
        assert captured["tenant_id"] == "tenant-medic"

    def test_get_alerts_authenticated_unresolved_returns_empty_never_cliente_cero(
        self, monkeypatch
    ):
        import presentation.centinela_endpoints as endpoints_module

        def must_not_be_called(self, company_id, tenant_id, limit=20, severity=None):
            raise AssertionError("get_alerts_for_company must not be called for an unresolved tenant")

        def must_not_resolve_cliente_cero(client):
            raise AssertionError("Cliente Cero fallback must not be used for an authenticated, unresolved caller")

        monkeypatch.setattr(
            endpoints_module.CentinelaService, "get_alerts_for_company", must_not_be_called
        )
        import core.tenant_context as tenant_context_module
        monkeypatch.setattr(
            tenant_context_module, "resolve_cliente_cero_tenant_id", must_not_resolve_cliente_cero
        )

        user = {
            "id": "76680e1f-2943-4235-8501-18b090d59257",
            "email": "growth@contexia.online",
            "resolved_user_id": None,
            "resolved_tenant_id": None,
        }
        response = run(get_company_alerts("ctx-001", user=user))

        assert response.alert_count == 0
        assert response.source == "none"
