"""
Tests for pulso_diario_endpoints.py::/summary and
centinela_agents_endpoints.py::/generate-draft (agent-endpoints-real-tenant-filtering,
Stage 2).

Before this change, both stub endpoints read `getattr(request.state, "tenant_id",
"default-tenant")` — the raw JWT claim injected by TenantContextMiddleware, or the literal
string "default-tenant" — and only interpolated it into response strings. Neither endpoint
touches the database, so there is nothing to tenant-scope, but the leaked placeholder string
and the missing auth gate were real gaps.

Verifies both endpoints now:
  1. Require `user: dict = Depends(get_current_user)`.
  2. Resolve tenant via `core/tenant_context.py::resolve_request_tenant_scope` (the
     already-canonical helper used by approval_queue_endpoints.py), not
     `request.state.tenant_id`.
  3. Never emit the literal string "default-tenant" in any response, for any caller.
"""

import asyncio
import inspect

import fastapi
import pytest

from core.deps import get_current_user, _STAGING_USER
from presentation import pulso_diario_endpoints, centinela_agents_endpoints


def run(coro):
    return asyncio.run(coro)


def _user_dependency_default(fn, name="user"):
    params = inspect.signature(fn).parameters
    param = params.get(name)
    return param.default if param is not None else None


class TestStubEndpointsRequireAuth:
    def test_pulso_summary_requires_get_current_user(self):
        default = _user_dependency_default(pulso_diario_endpoints.post_pulso_summary)
        assert isinstance(default, fastapi.params.Depends)
        assert default.dependency is get_current_user

    def test_centinela_draft_requires_get_current_user(self):
        default = _user_dependency_default(centinela_agents_endpoints.generate_centinela_draft)
        assert isinstance(default, fastapi.params.Depends)
        assert default.dependency is get_current_user


class TestPulsoSummaryTenantResolution:
    def test_resolved_tenant_is_echoed(self, monkeypatch):
        import presentation.pulso_diario_endpoints as mod

        monkeypatch.setattr(
            mod, "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="tenant-a-uuid", all_tenants=False),
        )
        user = {"id": "user-a", "resolved_tenant_id": "tenant-a-uuid"}
        payload = mod.PulsoDiarioSummaryRequest(company_id="ctx-001")
        response = run(mod.post_pulso_summary(payload=payload, user=user))
        assert response.tenant_id == "tenant-a-uuid"
        assert "default-tenant" not in response.tenant_id
        assert "default-tenant" not in response.message

    def test_unresolved_caller_never_gets_default_tenant_string(self, monkeypatch):
        import presentation.pulso_diario_endpoints as mod

        monkeypatch.setattr(mod, "resolve_request_tenant_scope", lambda user, client: None)
        user = {"id": "user-unlinked", "resolved_tenant_id": None}
        payload = mod.PulsoDiarioSummaryRequest(company_id="ctx-001")
        response = run(mod.post_pulso_summary(payload=payload, user=user))
        assert "default-tenant" not in response.tenant_id
        assert "default-tenant" not in response.message
        assert response.status == "tenant_unresolved"


class TestCentinelaDraftTenantResolution:
    def test_resolved_tenant_is_echoed(self, monkeypatch):
        import presentation.centinela_agents_endpoints as mod

        monkeypatch.setattr(
            mod, "resolve_request_tenant_scope",
            lambda user, client: mod.TenantScope(tenant_id="tenant-a-uuid", all_tenants=False),
        )
        user = {"id": "user-a", "resolved_tenant_id": "tenant-a-uuid"}
        payload = mod.CentinelaGenerateDraftRequest(company_id="ctx-001")
        response = run(mod.generate_centinela_draft(payload=payload, user=user))
        assert response.tenant_id == "tenant-a-uuid"
        assert "default-tenant" not in response.draft_id
        assert "default-tenant" not in response.message

    def test_unresolved_caller_never_gets_default_tenant_string(self, monkeypatch):
        import presentation.centinela_agents_endpoints as mod

        monkeypatch.setattr(mod, "resolve_request_tenant_scope", lambda user, client: None)
        user = {"id": "user-unlinked", "resolved_tenant_id": None}
        payload = mod.CentinelaGenerateDraftRequest(company_id="ctx-001")
        response = run(mod.generate_centinela_draft(payload=payload, user=user))
        assert "default-tenant" not in response.draft_id
        assert "default-tenant" not in response.message
        assert response.status == "tenant_unresolved"
