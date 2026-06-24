"""Tests for TenantContextMiddleware's resolved_* identity fields (core/tenant_middleware.py)."""
from __future__ import annotations

import asyncio

from core import tenant_middleware as tm
from core.identity_resolver import IdentityResolver
from core.security import create_access_token


class _FakeRequest:
    def __init__(self, headers: dict):
        self.headers = headers
        self.state = type("State", (), {})()
        self.method = "GET"
        self.url = type("URL", (), {"path": "/fake"})()


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        class _Result:
            def __init__(self, data):
                self.data = data
        return _Result(self._rows)


class _FakeClient:
    def __init__(self, table_rows: dict):
        self._table_rows = table_rows

    def table(self, name):
        return _FakeQuery(self._table_rows.get(name, []))


_REAL_USER_UUID = "26216a03-9d4a-4590-bfc3-a4ddf0524d57"
_REAL_TENANT_UUID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"


def run(coro):
    return asyncio.run(coro)


async def _noop_call_next(request):
    return "response"


def test_valid_token_sets_resolved_fields(monkeypatch):
    fake = IdentityResolver(client=_FakeClient({"usuarios": [{"id": _REAL_USER_UUID}]}))
    monkeypatch.setattr(tm, "identity_resolver", fake)

    token = create_access_token(
        {"sub": "usr_cliente_demo", "email": "cliente@demo.co", "tenant_id": _REAL_TENANT_UUID}
    )
    request = _FakeRequest({"Authorization": f"Bearer {token}"})
    middleware = tm.TenantContextMiddleware(app=None)

    run(middleware.dispatch(request, _noop_call_next))

    assert request.state.tenant_id == _REAL_TENANT_UUID
    assert request.state.user_id == "usr_cliente_demo"
    assert request.state.resolved_user_id == _REAL_USER_UUID
    assert request.state.resolved_tenant_id == _REAL_TENANT_UUID


def test_unresolved_identity_leaves_resolved_fields_none(monkeypatch):
    fake = IdentityResolver(client=_FakeClient({"usuarios": []}))
    monkeypatch.setattr(tm, "identity_resolver", fake)

    token = create_access_token({"sub": "usr_unknown", "email": "ghost@nowhere.co"})
    request = _FakeRequest({"Authorization": f"Bearer {token}"})
    middleware = tm.TenantContextMiddleware(app=None)

    run(middleware.dispatch(request, _noop_call_next))

    assert request.state.resolved_user_id is None
    assert request.state.resolved_tenant_id is None


def test_no_token_does_not_call_resolver_and_request_proceeds(monkeypatch):
    calls = []

    class _ExplodingResolver:
        def resolve(self, *a, **k):
            calls.append((a, k))
            raise AssertionError("resolver should not be called without a JWT")

    monkeypatch.setattr(tm, "identity_resolver", _ExplodingResolver())

    request = _FakeRequest({})
    middleware = tm.TenantContextMiddleware(app=None)

    result = run(middleware.dispatch(request, _noop_call_next))

    assert result == "response"
    assert request.state.tenant_id == "default-tenant"
    assert request.state.resolved_user_id is None
    assert request.state.resolved_tenant_id is None
    assert calls == []
