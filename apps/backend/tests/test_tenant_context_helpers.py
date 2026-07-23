"""
Tests for the shared tenant-resolution helpers (centinela-tenant-scoped-alerts).

require_tenant_id() is the fail-loud, reusable contract that replaces every implicit
Cliente Cero fallback: Cliente Cero must always be explicit, never a silent default. See
core/tenant_context.py and ARCHITECTURE.md Decision #13.

The caller-tenant resolution ladder itself (`resolve_caller_tenant`) was removed by
agent-endpoints-real-tenant-filtering, Stage 4 — its 3-branch behavior is a strict subset
of `resolve_request_tenant_scope`, already covered by `test_tenant_scope_resolution.py`.
"""

import pytest

from core.tenant_context import TenantResolutionError, require_tenant_id


class TestRequireTenantId:
    def test_require_tenant_id_returns_value(self):
        assert require_tenant_id("tenant-medic", context="test") == "tenant-medic"

    def test_require_tenant_id_raises_on_none(self):
        with pytest.raises(TenantResolutionError, match="centinela.save_alerts"):
            require_tenant_id(None, context="centinela.save_alerts")

    def test_require_tenant_id_raises_on_empty_string(self):
        with pytest.raises(TenantResolutionError, match="centinela.save_alerts"):
            require_tenant_id("", context="centinela.save_alerts")


