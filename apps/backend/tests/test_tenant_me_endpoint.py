"""
Tests for GET /api/v1/tenant/me (plan-tier-feature-gating).

Uses the canonical `resolve_request_tenant_scope` (unlike financials_endpoints.py's legacy
local resolver — see design.md D5, this is a brand-new endpoint with no prior behavior to
preserve). Mirrors the hermetic, throwaway-tenant pattern used across this test suite.
"""

import asyncio
import uuid

import pytest

from core.supabase_client import get_supabase
from core.deps import _STAGING_USER
from presentation.tenant_endpoints import get_tenant_me


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def test_tenant():
    supabase = get_supabase()
    nit = f"TEST-TENANTME-{uuid.uuid4().hex[:10]}"
    inserted = (
        supabase.table("tenants")
        .insert(
            {
                "nit": nit,
                "legal_name": "Hermetic Tenant/Me Test Tenant (pytest)",
                "is_cliente_cero": False,
                "plan_tier": "growth",
            }
        )
        .execute()
    )
    tenant_id = inserted.data[0]["id"]

    yield tenant_id, "Hermetic Tenant/Me Test Tenant (pytest)", "growth"

    supabase.table("tenants").delete().eq("id", tenant_id).execute()


class TestTenantMeEndpoint:
    def test_resolved_tenant_sees_own_legal_name_and_tier(self, test_tenant):
        tenant_id, legal_name, plan_tier = test_tenant

        user = {"id": "user-a", "resolved_tenant_id": tenant_id}
        response = run(get_tenant_me(user=user))

        assert response.legal_name == legal_name
        assert response.plan_tier == plan_tier

    def test_unresolved_tenant_never_sees_cliente_cero_identity(self, monkeypatch):
        import core.tenant_context as tenant_context_module

        monkeypatch.setattr(
            tenant_context_module, "resolve_cliente_cero_tenant_id",
            lambda client: "unrelated-cliente-cero-id",
        )

        user = {"id": "76680e1f-2943-4235-8501-18b090d59257", "resolved_tenant_id": None}
        response = run(get_tenant_me(user=user))

        assert response.legal_name is None
        assert response.plan_tier is None
        assert response.status == "empty"

    def test_staging_identity_resolves_to_cliente_cero(self):
        response = run(get_tenant_me(user=dict(_STAGING_USER)))

        assert response.status != "empty"
        assert response.legal_name is not None
