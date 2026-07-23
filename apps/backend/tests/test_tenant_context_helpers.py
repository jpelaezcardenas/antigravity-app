"""
Tests for the shared tenant-resolution helpers (centinela-tenant-scoped-alerts).

require_tenant_id() and resolve_caller_tenant() are the fail-loud, reusable
contract that replaces every implicit Cliente Cero fallback: Cliente Cero must
always be explicit, never a silent default. See core/tenant_context.py and
ARCHITECTURE.md Decision #13.
"""

import pytest

from core.deps import _STAGING_USER
from core.tenant_context import (
    TenantResolutionError,
    require_tenant_id,
    resolve_caller_tenant,
)


class TestRequireTenantId:
    def test_require_tenant_id_returns_value(self):
        assert require_tenant_id("tenant-medic", context="test") == "tenant-medic"

    def test_require_tenant_id_raises_on_none(self):
        with pytest.raises(TenantResolutionError, match="centinela.save_alerts"):
            require_tenant_id(None, context="centinela.save_alerts")

    def test_require_tenant_id_raises_on_empty_string(self):
        with pytest.raises(TenantResolutionError, match="centinela.save_alerts"):
            require_tenant_id("", context="centinela.save_alerts")


class _RaisingClient:
    """A fake Supabase client that fails the test if it's ever touched."""

    def table(self, *args, **kwargs):
        raise AssertionError("Cliente Cero resolver must not be called for this branch")


class _ClienteCeroClient:
    """A fake Supabase client returning a fixed Cliente Cero tenant id."""

    def __init__(self, tenant_id: str):
        self._tenant_id = tenant_id

    def table(self, name):
        assert name == "tenants"
        return self

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def single(self):
        return self

    def execute(self):
        tenant_id = self._tenant_id

        class _Result:
            data = {"id": tenant_id}
        return _Result()


class TestResolveCallerTenant:
    def test_resolve_caller_tenant_uses_resolved_tenant(self):
        user = {"id": "user-a", "resolved_tenant_id": "tenant-medic"}
        assert resolve_caller_tenant(user, _RaisingClient()) == "tenant-medic"

    def test_resolve_caller_tenant_staging_resolves_cliente_cero(self):
        user = dict(_STAGING_USER)
        client = _ClienteCeroClient("cliente-cero-tenant-id")
        assert resolve_caller_tenant(user, client) == "cliente-cero-tenant-id"

    def test_resolve_caller_tenant_unresolved_returns_none_never_cliente_cero(self):
        user = {
            "id": "76680e1f-2943-4235-8501-18b090d59257",
            "email": "growth@contexia.online",
            "resolved_user_id": None,
            "resolved_tenant_id": None,
        }
        assert resolve_caller_tenant(user, _RaisingClient()) is None
