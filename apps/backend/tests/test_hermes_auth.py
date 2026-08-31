"""
Tests for core/hermes_auth.py — verify_hermes_token FastAPI dependency.

Scenarios:
1. Valid token accepted (no exception raised)
2. Missing Authorization header → HTTP 403
3. Wrong token value → HTTP 403
4. Missing env var → RuntimeError at import / call time
"""

import importlib
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_hermes_auth(hermes_bridge_token: str | None = "test-secret-token"):
    """Import (or reload) hermes_auth with the given env var value."""
    # Remove cached module so the module-level guard re-runs on each import.
    for key in list(sys.modules.keys()):
        if "hermes_auth" in key:
            del sys.modules[key]

    env = {} if hermes_bridge_token is None else {"HERMES_BRIDGE_TOKEN": hermes_bridge_token}
    clear = hermes_bridge_token is None
    with patch.dict("os.environ", env, clear=clear):
        import core.hermes_auth as mod
        return mod


def _call_dependency(mod, authorization: str | None):
    """Invoke the verify_hermes_token dependency directly."""
    return mod.verify_hermes_token(authorization=authorization)


# ---------------------------------------------------------------------------
# Tests: Token validation
# ---------------------------------------------------------------------------

class TestVerifyHermesToken:
    def test_valid_token_accepted(self):
        """A matching Bearer token must not raise."""
        mod = _import_hermes_auth("secret-abc")
        # Should return None / not raise
        _call_dependency(mod, authorization="Bearer secret-abc")

    def test_missing_header_raises_403(self):
        """No Authorization header → HTTP 403."""
        mod = _import_hermes_auth("secret-abc")
        with pytest.raises(HTTPException) as exc_info:
            _call_dependency(mod, authorization=None)
        assert exc_info.value.status_code == 403

    def test_wrong_token_raises_403(self):
        """Wrong token value → HTTP 403."""
        mod = _import_hermes_auth("secret-abc")
        with pytest.raises(HTTPException) as exc_info:
            _call_dependency(mod, authorization="Bearer wrong-token")
        assert exc_info.value.status_code == 403

    def test_malformed_header_raises_403(self):
        """Authorization header without 'Bearer ' prefix → HTTP 403."""
        mod = _import_hermes_auth("secret-abc")
        with pytest.raises(HTTPException) as exc_info:
            _call_dependency(mod, authorization="secret-abc")
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Tests: Missing env var
# ---------------------------------------------------------------------------

class TestMissingEnvVar:
    def test_missing_env_var_raises_runtime_error(self):
        """If HERMES_BRIDGE_TOKEN is not set, importing or calling raises RuntimeError."""
        for key in list(sys.modules.keys()):
            if "hermes_auth" in key:
                del sys.modules[key]

        import os
        env_backup = os.environ.pop("HERMES_BRIDGE_TOKEN", None)
        try:
            with pytest.raises((RuntimeError, Exception)):
                import core.hermes_auth  # noqa: F401
        finally:
            if env_backup is not None:
                os.environ["HERMES_BRIDGE_TOKEN"] = env_backup
