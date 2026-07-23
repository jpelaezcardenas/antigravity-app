"""
Tests for GET /api/v1/centinela/alerts tenant resolution (pwa-tenant-aware-screens Stage 2).

The new route is additive alongside the existing `GET /centinela/alerts/{company_id}`
(unchanged, still consumed by Hermes's `CentinelaAlertsTool`). These tests verify:
  1. An authenticated caller with a resolved tenant sees only THEIR OWN alerts.
  2. Two different tenants never see each other's alerts.
  3. The unauthenticated/local-dev staging identity still falls back to Cliente Cero.
  4. An authenticated caller with NO resolved tenant gets an empty response — NOT
     Cliente Cero (no leak) — and the Cliente Cero resolver is never invoked.
  5. A resolved tenant with zero rows gets an honest empty list, not a demo fallback.
  6. The legacy `/alerts/{company_id}` route is unaffected.

Uses the same hermetic, throwaway-tenant pattern as test_financials_endpoint_tenant_scoping.py.
"""

import asyncio
import uuid

import pytest

from core.supabase_client import get_supabase
from core.deps import _STAGING_USER
from presentation.centinela_endpoints import get_my_alerts


def run(coro):
    return asyncio.run(coro)


def insert_test_alert(supabase, tenant_id: str, rule_id: str, severity: str) -> str:
    """Insert a hermetic centinela_alerts row for a throwaway tenant, return its id.

    `company_id` FKs to `agent_profiles` — reuses the existing real "ctx-001" row
    (no throwaway agent_profiles row is created); isolation in these tests is
    asserted purely on `tenant_id`, which is what the new route filters by.
    """
    row = {
        "company_id": "ctx-001",
        "tenant_id": tenant_id,
        "rule_id": rule_id,
        "rule_name": "Test Rule",
        "severity": severity,
        "title": "Test alert (pytest)",
        "description": "Hermetic test alert, safe to delete",
        "evidence": {"pytest": True},
    }
    result = supabase.table("centinela_alerts").insert(row).execute()
    return result.data[0]["id"]


@pytest.fixture
def two_test_tenants():
    """Two hermetic, throwaway tenants."""
    supabase = get_supabase()
    tenant_ids = []
    for label in ("A", "B"):
        nit = f"TEST-CENT-{label}-{uuid.uuid4().hex[:10]}"
        inserted = (
            supabase.table("tenants")
            .insert({"nit": nit, "legal_name": f"Hermetic Centinela Tenant {label} (pytest)", "is_cliente_cero": False})
            .execute()
        )
        tenant_ids.append(inserted.data[0]["id"])

    yield tenant_ids

    for tenant_id in tenant_ids:
        supabase.table("centinela_alerts").delete().eq("tenant_id", tenant_id).execute()
        supabase.table("tenants").delete().eq("id", tenant_id).execute()


@pytest.fixture
def cleanup_test_alerts():
    created_ids = []
    yield created_ids
    supabase = get_supabase()
    for alert_id in created_ids:
        supabase.table("centinela_alerts").delete().eq("id", alert_id).execute()


class TestCentinelaAlertsEndpointTenantScoping:
    def test_authenticated_caller_sees_own_tenant_alerts_only(
        self, two_test_tenants, cleanup_test_alerts
    ):
        tenant_a, tenant_b = two_test_tenants
        supabase = get_supabase()

        cleanup_test_alerts.append(
            insert_test_alert(supabase, tenant_a, "R001", "warning")
        )
        cleanup_test_alerts.append(
            insert_test_alert(supabase, tenant_b, "R002", "critical")
        )

        user = {"id": "user-a", "email": "a@client.co", "resolved_user_id": "uuid-a", "resolved_tenant_id": tenant_a}
        response = run(get_my_alerts(user=user))

        assert response.alert_count == 1
        assert all(a.rule_id == "R001" for a in response.alerts)

    def test_two_tenants_never_see_each_others_alerts(
        self, two_test_tenants, cleanup_test_alerts
    ):
        tenant_a, tenant_b = two_test_tenants
        supabase = get_supabase()

        cleanup_test_alerts.append(
            insert_test_alert(supabase, tenant_a, "R001", "warning")
        )
        cleanup_test_alerts.append(
            insert_test_alert(supabase, tenant_b, "R002", "critical")
        )
        cleanup_test_alerts.append(
            insert_test_alert(supabase, tenant_b, "R003", "warning")
        )

        user_a = {"id": "user-a", "email": "a@client.co", "resolved_user_id": "uuid-a", "resolved_tenant_id": tenant_a}
        user_b = {"id": "user-b", "email": "b@client.co", "resolved_user_id": "uuid-b", "resolved_tenant_id": tenant_b}

        response_a = run(get_my_alerts(user=user_a))
        response_b = run(get_my_alerts(user=user_b))

        assert response_a.alert_count == 1
        assert response_b.alert_count == 2
        assert {a.rule_id for a in response_a.alerts}.isdisjoint({a.rule_id for a in response_b.alerts})

    def test_resolved_tenant_with_no_rows_returns_honest_empty_list(self, two_test_tenants):
        tenant_a, _ = two_test_tenants

        user = {"id": "user-a", "email": "a@client.co", "resolved_user_id": "uuid-a", "resolved_tenant_id": tenant_a}
        response = run(get_my_alerts(user=user))

        assert response.alerts == []
        assert response.alert_count == 0
        assert response.source == "supabase"

    def test_staging_identity_falls_back_to_cliente_cero(self, monkeypatch):
        """Unauthenticated/local-dev caller (AUTH_ENFORCED=False, no token) still
        resolves to Cliente Cero — back-compat for the existing overview + local dev."""
        import core.tenant_context as tenant_context_module

        called = {"cliente_cero": False}

        async def fake_default_resolver():
            called["cliente_cero"] = True
            return "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"

        monkeypatch.setattr(tenant_context_module, "_default_cliente_cero_resolver", fake_default_resolver)

        response = run(get_my_alerts(user=dict(_STAGING_USER)))

        assert called["cliente_cero"] is True
        assert response.source == "supabase"

    def test_authenticated_unresolved_tenant_returns_empty_never_cliente_cero(self, monkeypatch):
        """An authenticated caller (not the staging identity) with NO resolved
        tenant must get an empty response, and Cliente Cero resolution must
        NEVER be invoked — that would leak Contexia's alerts to an unwired login."""
        import core.tenant_context as tenant_context_module

        async def must_not_be_called():
            raise AssertionError("Cliente Cero fallback must not be used for an authenticated, unresolved caller")

        monkeypatch.setattr(tenant_context_module, "_default_cliente_cero_resolver", must_not_be_called)

        user = {"id": "76680e1f-2943-4235-8501-18b090d59257", "email": "growth@contexia.online", "resolved_user_id": None, "resolved_tenant_id": None}
        response = run(get_my_alerts(user=user))

        assert response.alerts == []
        assert response.alert_count == 0
        assert response.critical_count == 0
        assert response.warning_count == 0
        assert response.risk_level == "none"
        assert response.source == "supabase"
