"""Tests for AuthService.login() signing a real tenant UUID claim (change jwt-real-tenant-uuid-claim)."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from application import auth_service as auth_service_module
from application.auth_service import AuthService
from core.security import verify_token


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


from core.identity_resolver import IdentityResolver

_REAL_USER_UUID = "26216a03-9d4a-4590-bfc3-a4ddf0524d57"
_REAL_TENANT_UUID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"


def run(coro):
    return asyncio.run(coro)


def test_demo_login_signs_real_tenant_uuid(monkeypatch):
    fake = IdentityResolver(
        client=_FakeClient(
            {
                "usuarios": [{"id": _REAL_USER_UUID}],
                "user_tenants": [{"tenant_id": _REAL_TENANT_UUID}],
            }
        )
    )
    monkeypatch.setattr(auth_service_module, "identity_resolver", fake)

    service = AuthService()
    result = run(service.login("cliente@demo.co", "demo"))

    payload = verify_token(result["token"])
    assert payload["tenant_id"] == _REAL_TENANT_UUID
    assert payload["sub"] == "usr_cliente_demo"  # sub stays unchanged (D2)


def test_demo_login_falls_back_when_unresolved(monkeypatch):
    fake = IdentityResolver(client=_FakeClient({"usuarios": []}))
    monkeypatch.setattr(auth_service_module, "identity_resolver", fake)

    service = AuthService()
    result = run(service.login("cliente@demo.co", "demo"))

    payload = verify_token(result["token"])
    assert payload["tenant_id"] == "contexia-org-1"  # unchanged default, login still succeeds
    assert payload["sub"] == "usr_cliente_demo"


def test_demo_login_invalid_password_still_raises_401(monkeypatch):
    fake = IdentityResolver(client=_FakeClient({"usuarios": []}))
    monkeypatch.setattr(auth_service_module, "identity_resolver", fake)

    service = AuthService()
    with pytest.raises(HTTPException) as exc:
        run(service.login("cliente@demo.co", "wrong-password"))
    assert exc.value.status_code == 401
