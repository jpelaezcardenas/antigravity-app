"""
Tests for plan-tier feature gating on GET /api/v1/centinela/alerts (plan-tier-feature-gating).

Every real tier includes `centinela_alerts` today (migration 0043 defaults every tenant to
'starter'), so these tests monkeypatch `has_feature` to exercise the not-in-plan branch —
mirrors the existing monkeypatch style in test_centinela_alerts_tenant_scoping.py.
"""

import asyncio
import uuid

import pytest

from core.supabase_client import get_supabase
from presentation.centinela_endpoints import get_my_alerts


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def test_tenant_id():
    supabase = get_supabase()
    nit = f"TEST-CENT-PLANTIER-{uuid.uuid4().hex[:10]}"
    inserted = (
        supabase.table("tenants")
        .insert({"nit": nit, "legal_name": "Hermetic Centinela Plan-Tier Test Tenant (pytest)", "is_cliente_cero": False})
        .execute()
    )
    tenant_id = inserted.data[0]["id"]

    yield tenant_id

    supabase.table("centinela_alerts").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("tenants").delete().eq("id", tenant_id).execute()


class TestCentinelaAlertsPlanTierGating:
    def test_tenant_without_centinela_alerts_feature_gets_not_in_plan(self, test_tenant_id, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        monkeypatch.setattr(endpoints_module, "has_feature", lambda tier, feature: False)

        user = {"id": "user-gated", "resolved_tenant_id": test_tenant_id}
        response = run(get_my_alerts(user=user))

        assert response.status == "not_in_plan"
        assert response.alerts == []
        assert response.alert_count == 0
        assert response.source == "supabase"

    def test_tenant_with_centinela_alerts_feature_queries_normally(self, test_tenant_id, monkeypatch):
        import presentation.centinela_endpoints as endpoints_module

        monkeypatch.setattr(endpoints_module, "has_feature", lambda tier, feature: True)

        user = {"id": "user-allowed", "resolved_tenant_id": test_tenant_id}
        response = run(get_my_alerts(user=user))

        assert response.status is None
        assert response.alerts == []
        assert response.alert_count == 0
