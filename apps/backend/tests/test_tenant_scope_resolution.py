"""Unit tests for the shared tenant-scope resolution helper (approval-queue-tenant-scoping).

Covers `resolve_request_tenant_scope(user, client)` — the four-way resolution ladder
described in `openspec/changes/approval-queue-tenant-scoping/design.md`:

1. caller's own `resolved_tenant_id` resolves to Cliente Cero -> all_tenants=True (operator)
2. caller's own `resolved_tenant_id` is a normal client -> all_tenants=False, own tenant only
3. staging identity (no auth enforced, no token) -> Cliente Cero, all_tenants=True (back-compat)
4. authenticated but unresolved -> None (never a silent Cliente Cero fallback)

All Supabase access is mocked at the client boundary, matching the pattern established by
`test_tenant_stamping.py`.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from core.deps import _STAGING_USER
from core.tenant_context import TenantScope, resolve_request_tenant_scope

CLIENTE_CERO_ID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"
CLIENT_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _mock_client_with_cliente_cero(tenant_id: str = CLIENTE_CERO_ID):
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "id": tenant_id
    }
    return client


def _mock_client_missing_cliente_cero():
    client = MagicMock()
    client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = None
    return client


def test_client_with_resolved_tenant_gets_own_scope_not_all_tenants():
    client = _mock_client_with_cliente_cero()
    user = {"id": "client-user", "resolved_tenant_id": CLIENT_TENANT_ID}

    scope = resolve_request_tenant_scope(user, client)

    assert scope == TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False)


def test_cliente_cero_member_gets_all_tenants_scope():
    client = _mock_client_with_cliente_cero()
    user = {"id": "operator-user", "resolved_tenant_id": CLIENTE_CERO_ID}

    scope = resolve_request_tenant_scope(user, client)

    assert scope == TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True)


def test_staging_identity_gets_cliente_cero_all_tenants_scope():
    client = _mock_client_with_cliente_cero()
    user = dict(_STAGING_USER)

    scope = resolve_request_tenant_scope(user, client)

    assert scope == TenantScope(tenant_id=CLIENTE_CERO_ID, all_tenants=True)


def test_authenticated_unresolved_returns_none():
    client = _mock_client_with_cliente_cero()
    user = {"id": "some-other-authenticated-user", "resolved_tenant_id": None}

    scope = resolve_request_tenant_scope(user, client)

    assert scope is None


def test_missing_cliente_cero_row_still_resolves_client_tenant():
    client = _mock_client_missing_cliente_cero()
    user = {"id": "client-user", "resolved_tenant_id": CLIENT_TENANT_ID}

    scope = resolve_request_tenant_scope(user, client)

    assert scope == TenantScope(tenant_id=CLIENT_TENANT_ID, all_tenants=False)
