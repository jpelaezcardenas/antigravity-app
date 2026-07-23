"""Tests for env-gated auth dependencies (core/deps.py)."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt as jose_jwt

from config import settings
from core import deps
from core.deps import (
    get_current_user,
    verify_resource_ownership,
    _extract_bearer_token,
)
from core.identity_resolver import IdentityResolver
from core.security import create_access_token


def _make_supabase_jwt(secret: str, **claims) -> str:
    """Builds a token shaped like a real Supabase Auth JWT (aud=authenticated,
    app_metadata.role), signed with the given secret — mirrors middleware.ts's own
    verification target, not the backend's own create_access_token."""
    payload = {
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        **claims,
    }
    return jose_jwt.encode(payload, secret, algorithm="HS256")


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


class TestSupabaseJwtFallback:
    """get_current_user recognizes a Supabase-issued JWT (bunker-pwa-auth-enforcement) — the
    token login.html already stores in localStorage["token"] and sends as Authorization: Bearer,
    verified with SUPABASE_JWT_SECRET (same target middleware.ts already validates), as a
    fallback when the backend's own verify_token doesn't recognize it."""

    def test_valid_supabase_jwt_is_recognized(self, monkeypatch):
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "supabase-test-secret")
        token = _make_supabase_jwt(
            "supabase-test-secret",
            sub="76680e1f-2943-4235-8501-18b090d59257",
            email="growth@contexia.online",
            app_metadata={"role": "cliente", "roles": ["cliente"]},
        )
        user = run(get_current_user(f"Bearer {token}"))
        assert user["id"] == "76680e1f-2943-4235-8501-18b090d59257"
        assert user["email"] == "growth@contexia.online"

    def test_backends_own_jwt_still_works_unchanged(self, monkeypatch):
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "supabase-test-secret")
        token = create_access_token({"sub": "user-123", "email": "u@x.co"})
        user = run(get_current_user(f"Bearer {token}"))
        assert user["id"] == "user-123"
        assert user["email"] == "u@x.co"

    def test_enforced_accepts_a_real_supabase_session(self, monkeypatch):
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "supabase-test-secret")
        monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
        token = _make_supabase_jwt(
            "supabase-test-secret",
            sub="bd0700fb-6274-49ed-a2d0-e2844100e857",
            email="contexia.marketing@gmail.com",
            app_metadata={"role": "admin", "roles": ["admin"]},
        )
        user = run(get_current_user(f"Bearer {token}"))
        assert user["email"] == "contexia.marketing@gmail.com"

    def test_enforced_still_rejects_a_token_signed_with_the_wrong_secret(self, monkeypatch):
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "supabase-test-secret")
        monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
        token = _make_supabase_jwt("some-other-secret", sub="x", email="x@x.co")
        with pytest.raises(HTTPException) as exc:
            run(get_current_user(f"Bearer {token}"))
        assert exc.value.status_code == 401

    def test_no_supabase_secret_configured_does_not_crash(self, monkeypatch):
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
        monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
        token = _make_supabase_jwt("whatever-secret", sub="x", email="x@x.co")
        with pytest.raises(HTTPException) as exc:
            run(get_current_user(f"Bearer {token}"))
        assert exc.value.status_code == 401


class TestSupabaseAsymmetricJwks:
    """get_current_user recognizes Supabase's current default signing scheme: an
    asymmetric key (observed live: ES256 + a `kid`), verified via the project's JWKS
    endpoint — not the legacy shared HS256 secret, which cannot verify these tokens at
    all (found live 2026-07-23: every real client login was silently falling back to
    mock data because _verify_supabase_token only ever tried HS256)."""

    @staticmethod
    def _make_es256_keypair():
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = ec.generate_private_key(ec.SECP256R1())
        return private_key, private_key.public_key()

    @staticmethod
    def _jwk_from_public_key(public_key, kid: str) -> dict:
        import base64

        numbers = public_key.public_numbers()

        def _b64url(n: int) -> str:
            raw = n.to_bytes(32, "big")
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

        return {
            "kty": "EC",
            "crv": "P-256",
            "alg": "ES256",
            "use": "sig",
            "kid": kid,
            "x": _b64url(numbers.x),
            "y": _b64url(numbers.y),
        }

    def _make_es256_token(self, private_key, kid: str, **claims) -> str:
        payload = {
            "aud": "authenticated",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            **claims,
        }
        return jose_jwt.encode(
            payload, private_key, algorithm="ES256", headers={"kid": kid}
        )

    def test_valid_es256_token_verified_via_jwks(self, monkeypatch):
        private_key, public_key = self._make_es256_keypair()
        jwk = self._jwk_from_public_key(public_key, "test-kid-1")
        monkeypatch.setattr(deps, "_fetch_supabase_jwks", lambda force=False: [jwk])

        token = self._make_es256_token(
            private_key, "test-kid-1", sub="user-es256", email="es256@client.co",
            app_metadata={"role": "cliente", "roles": ["cliente"]},
        )
        user = run(get_current_user(f"Bearer {token}"))

        assert user["id"] == "user-es256"
        assert user["email"] == "es256@client.co"

    def test_es256_token_with_wrong_key_is_rejected(self, monkeypatch):
        _private_key, public_key = self._make_es256_keypair()
        other_private_key, _other_public_key = self._make_es256_keypair()
        jwk = self._jwk_from_public_key(public_key, "test-kid-2")
        monkeypatch.setattr(deps, "_fetch_supabase_jwks", lambda force=False: [jwk])

        # Signed with a DIFFERENT private key than the one whose public half is cached.
        token = self._make_es256_token(other_private_key, "test-kid-2", sub="x", email="x@x.co")

        monkeypatch.setattr(settings, "AUTH_ENFORCED", True)
        with pytest.raises(HTTPException) as exc:
            run(get_current_user(f"Bearer {token}"))
        assert exc.value.status_code == 401

    def test_unknown_kid_refetches_once_then_gives_up(self, monkeypatch):
        private_key, public_key = self._make_es256_keypair()
        jwk = self._jwk_from_public_key(public_key, "rotated-kid")
        calls = {"count": 0}

        def fake_fetch(force=False):
            calls["count"] += 1
            # Simulate the cache only knowing the new key once forced (post-rotation).
            return [jwk] if force else []

        monkeypatch.setattr(deps, "_fetch_supabase_jwks", fake_fetch)

        token = self._make_es256_token(private_key, "rotated-kid", sub="u", email="u@x.co")
        user = run(get_current_user(f"Bearer {token}"))

        assert user["id"] == "u"
        assert calls["count"] == 2  # first miss, forced refetch found it

    def test_jwks_fetch_failure_degrades_to_staging_when_not_enforced(self, monkeypatch):
        monkeypatch.setattr(deps, "_fetch_supabase_jwks", lambda force=False: [])
        monkeypatch.setattr(settings, "AUTH_ENFORCED", False)

        private_key, _public_key = self._make_es256_keypair()
        token = self._make_es256_token(private_key, "missing-kid", sub="u", email="u@x.co")
        user = run(get_current_user(f"Bearer {token}"))

        assert user["id"] == "test-user-staging"

    def test_legacy_hs256_token_still_works_alongside_es256_support(self, monkeypatch):
        """Backward compatibility: a token with no `kid` (or alg=HS256) still verifies
        via the legacy shared-secret path, unaffected by the new JWKS branch."""
        monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "supabase-test-secret")
        token = _make_supabase_jwt(
            "supabase-test-secret", sub="legacy-user", email="legacy@x.co"
        )
        user = run(get_current_user(f"Bearer {token}"))
        assert user["id"] == "legacy-user"
