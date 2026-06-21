"""Tests for env-gated auth dependencies (core/deps.py)."""
import asyncio

import pytest
from fastapi import HTTPException

from config import settings
from core.deps import (
    get_current_user,
    verify_resource_ownership,
    _extract_bearer_token,
)
from core.security import create_access_token


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


def test_not_enforced_falls_back_to_staging(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_ENFORCED", False)
    user = run(get_current_user(None))
    assert user["id"] == "test-user-staging"


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
