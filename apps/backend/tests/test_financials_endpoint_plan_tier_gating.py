"""
Tests for plan-tier feature gating on GET /api/v1/financials and
GET /api/v1/financials/liquidity-bridge (plan-tier-feature-gating).

Every real tier includes both `pulso_diario` and `liquidity_bridge` today (migration 0043
defaults every tenant to 'starter'), so these tests monkeypatch `has_feature` to exercise
the not-in-plan branch rather than relying on a real tier that doesn't exist yet — mirrors
the existing monkeypatch style already used in test_financials_endpoint_tenant_scoping.py
for the staging-identity/unresolved-tenant cases.

Uses the same hermetic, throwaway-tenant pattern as test_financials_aggregation.py.
"""

import asyncio
import uuid

import pytest
from datetime import date

from core.supabase_client import get_supabase
from presentation.financials_endpoints import get_financials, get_liquidity_bridge
from tests.test_financials_aggregation import insert_test_entry


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def test_tenant_id():
    supabase = get_supabase()
    nit = f"TEST-PLANTIER-{uuid.uuid4().hex[:10]}"
    inserted = (
        supabase.table("tenants")
        .insert({"nit": nit, "legal_name": "Hermetic Plan-Tier Test Tenant (pytest)", "is_cliente_cero": False})
        .execute()
    )
    tenant_id = inserted.data[0]["id"]

    yield tenant_id

    supabase.table("erp_journal_lines").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("erp_journal_entries").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("tenants").delete().eq("id", tenant_id).execute()


class TestFinancialsPlanTierGating:
    def test_tenant_without_pulso_diario_feature_gets_not_in_plan(self, test_tenant_id, monkeypatch):
        import presentation.financials_endpoints as endpoints_module

        called = {"compute": False}
        monkeypatch.setattr(
            endpoints_module,
            "compute_pulso_daily_snapshot",
            lambda *a, **kw: called.__setitem__("compute", True) or {},
        )
        monkeypatch.setattr(endpoints_module, "has_feature", lambda tier, feature: False)

        user = {"id": "user-gated", "resolved_tenant_id": test_tenant_id}
        snapshot = run(get_financials(user=user))

        assert snapshot["status"] == "not_in_plan"
        assert snapshot["caja_real"] == 0
        assert called["compute"] is False

    def test_tenant_with_pulso_diario_feature_computes_normally(self, test_tenant_id, monkeypatch):
        import presentation.financials_endpoints as endpoints_module

        monkeypatch.setattr(endpoints_module, "has_feature", lambda tier, feature: True)

        user = {"id": "user-allowed", "resolved_tenant_id": test_tenant_id}
        snapshot = run(get_financials(user=user))

        assert snapshot["status"] != "not_in_plan"


class TestLiquidityBridgePlanTierGating:
    def test_tenant_without_liquidity_bridge_feature_gets_not_in_plan(self, test_tenant_id, monkeypatch):
        import presentation.financials_endpoints as endpoints_module

        called = {"compute": False}
        monkeypatch.setattr(
            endpoints_module,
            "compute_liquidity_bridge",
            lambda *a, **kw: called.__setitem__("compute", True) or {},
        )
        monkeypatch.setattr(endpoints_module, "has_feature", lambda tier, feature: False)

        user = {"id": "user-gated", "resolved_tenant_id": test_tenant_id}
        bridge = run(get_liquidity_bridge(user=user))

        assert bridge["status"] == "not_in_plan"
        assert bridge["initial_balance"] == 0
        assert bridge["final_balance"] == 0
        assert called["compute"] is False

    def test_tenant_with_liquidity_bridge_feature_computes_normally(self, test_tenant_id, monkeypatch):
        import presentation.financials_endpoints as endpoints_module

        monkeypatch.setattr(endpoints_module, "has_feature", lambda tier, feature: True)

        user = {"id": "user-allowed", "resolved_tenant_id": test_tenant_id}
        bridge = run(get_liquidity_bridge(user=user))

        assert bridge["status"] != "not_in_plan"
