"""Tests for env-gated auth dependencies (core/deps.py)."""
import asyncio

import pytest
from fastapi import HTTPException

from config import settings
from core import deps
from core.deps import (
    get_current_user,
    verify_resource_ownership,
    _extract_bearer_token,
)
from core.identity_resolver import IdentityResolver
from core.security import create_access_token


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


def test_extract_bearer_token_variants():
    assert _extract_bearer_token(None) is None
    assert _extract_bearer_token("") is None
    assert _extract_bearer_token("Bearer abc.def") == "abc.def"
    assert _extract_bearer_token("bearer abc.def") == "abc.def"
    # Tolerate a raw token without the scheme prefix.
    assert _extract_bearer_token("rawtoken") == "rawtoken"


def test_valid_token_returns_real_user():
    token = create_access_token({"sub": "user-123", "email": "u@x.co"})
    user = run(get_current_user(f"Bearer {token}"))
    assert user["id"] == "user-123"
    assert user["email"] == "u@x.co"


def test_valid_token_adds_resolved_identity(monkeypatch):
    fake = IdentityResolver(client=_FakeClient({"usuarios": [{"id": _REAL_USER_UUID}]}))
    monkeypatch.setattr(deps, "identity_resolver", fake)
    token = create_access_token({"sub": "usr_cliente_demo", "email": "cliente@demo.co", "tenant_id": _REAL_TENANT_UUID})
    user = run(get_current_user(f"Bearer {token}"))
    assert user["id"] == "usr_cliente_demo"
    assert user["resolved_user_id"] == _REAL_USER_UUID
    assert user["resolved_tenant_id"] == _REAL_TENANT_UUID


def test_valid_token_unresolved_identity_does_not_raise(monkeypatch):
    fake = IdentityResolver(client=_FakeClient({"usuarios": []}))
    monkeypatch.setattr(deps, "identity_resolver", fake)
    token = create_access_token({"sub": "usr_unknown", "email": "ghost@nowhere.co"})
    user = run(get_current_user(f"Bearer {token}"))
    assert user["id"] == "usr_unknown"
    assert user["resolved_user_id"] is None
    assert user["resolved_tenant_id"] is None


def test_not_enforced_falls_back_to_staging(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", False)
    user = run(get_current_user(None))
    assert user["id"] == "test-user-staging"
    assert user["resolved_user_id"] is None
    assert user["resolved_tenant_id"] is None


def test_enforced_requires_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
    with pytest.raises(HTTPException) as exc:
        run(get_current_user(None))
    assert exc.value.status_code == 401


def test_enforced_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
    with pytest.raises(HTTPException) as exc:
        run(get_current_user("Bearer not-a-jwt"))
    assert exc.value.status_code == 401


def test_ownership_not_enforced_allows(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", False)
    assert run(verify_resource_ownership("a", "b")) is True


def test_ownership_enforced_blocks_mismatch(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
    with pytest.raises(HTTPException) as exc:
        run(verify_resource_ownership("a", "b"))
    assert exc.value.status_code == 403


def test_ownership_enforced_allows_match(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
    assert run(verify_resource_ownership("same", "same")) is True
