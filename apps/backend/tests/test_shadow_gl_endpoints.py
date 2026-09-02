"""
Tests for shadow_gl_endpoints auth pattern.

Verifies that all POST endpoints require JWT auth via get_current_user and
resolve the tenant via resolve_request_tenant_scope (not a hardcoded Cliente Cero).
"""

import inspect

import pytest


class TestEndpointAuthSignatures:
    """Verify Depends(get_current_user) is wired on every POST endpoint."""

    def _get_endpoint_dependencies(self, fn) -> list[str]:
        """Return the names of FastAPI dependencies declared on an endpoint function."""
        sig = inspect.signature(fn)
        dep_names = []
        for param in sig.parameters.values():
            default = param.default
            # FastAPI Depends wraps the callable in a FieldInfo-like object;
            # the actual dependency callable is stored in .dependency.
            if hasattr(default, "dependency"):
                dep_names.append(default.dependency.__name__)
        return dep_names

    def test_dian_xml_ingest_requires_auth(self):
        """ingest_dian_xml_endpoint must declare get_current_user dependency."""
        from presentation.shadow_gl_endpoints import ingest_dian_xml_endpoint

        deps = self._get_endpoint_dependencies(ingest_dian_xml_endpoint)
        assert "get_current_user" in deps

    def test_siigo_csv_ingest_requires_auth(self):
        """ingest_siigo_csv_endpoint must declare get_current_user dependency."""
        from presentation.shadow_gl_endpoints import ingest_siigo_csv_endpoint

        deps = self._get_endpoint_dependencies(ingest_siigo_csv_endpoint)
        assert "get_current_user" in deps

    def test_siigo_csv_upload_requires_auth(self):
        """upload_siigo_csv_endpoint must declare get_current_user dependency."""
        from presentation.shadow_gl_endpoints import upload_siigo_csv_endpoint

        deps = self._get_endpoint_dependencies(upload_siigo_csv_endpoint)
        assert "get_current_user" in deps

    def test_upload_any_format_requires_auth(self):
        """upload_any_format_endpoint must declare get_current_user dependency."""
        from presentation.shadow_gl_endpoints import upload_any_format_endpoint

        deps = self._get_endpoint_dependencies(upload_any_format_endpoint)
        assert "get_current_user" in deps


class TestTenantResolver:
    """Verify _resolve_tenant_from_scope uses resolve_request_tenant_scope, not hardcoded logic."""

    def test_resolver_raises_403_when_scope_is_none(self):
        """_resolve_tenant_from_scope must raise HTTP 403 when scope resolves to None."""
        from unittest.mock import MagicMock, patch
        from fastapi import HTTPException
        from presentation.shadow_gl_endpoints import _resolve_tenant_from_scope

        staging_user = {"id": "00000000-0000-0000-0000-000000000000", "email": "staging@example.com"}

        with patch("presentation.shadow_gl_endpoints.get_supabase"), \
             patch("presentation.shadow_gl_endpoints.resolve_request_tenant_scope", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                _resolve_tenant_from_scope(staging_user)

        assert exc_info.value.status_code == 403

    def test_resolver_returns_scope_tenant_id(self):
        """_resolve_tenant_from_scope must return scope.tenant_id when scope is resolved."""
        from unittest.mock import MagicMock, patch
        from presentation.shadow_gl_endpoints import _resolve_tenant_from_scope

        expected_tenant_id = "aabbccdd-0000-0000-0000-aabbccddee00"
        mock_scope = MagicMock()
        mock_scope.tenant_id = expected_tenant_id

        staging_user = {"id": "00000000-0000-0000-0000-000000000000", "email": "staging@example.com"}

        with patch("presentation.shadow_gl_endpoints.get_supabase"), \
             patch("presentation.shadow_gl_endpoints.resolve_request_tenant_scope", return_value=mock_scope):
            result = _resolve_tenant_from_scope(staging_user)

        assert result == expected_tenant_id

    def test_resolver_does_not_hardcode_cliente_cero(self):
        """_resolve_tenant_from_scope source must not contain is_cliente_cero hardcode."""
        import inspect as _inspect
        from presentation.shadow_gl_endpoints import _resolve_tenant_from_scope

        source = _inspect.getsource(_resolve_tenant_from_scope)
        assert "is_cliente_cero" not in source


class TestRoutePresence:
    """Verify all expected routes are registered on the router."""

    def test_upload_any_format_route_exists(self):
        """POST /upload route must be registered for multi-format PWA upload."""
        from presentation.shadow_gl_endpoints import router

        paths = [r.path for r in router.routes]
        assert any("/upload" == p or p.endswith("/upload") for p in paths)

    def test_all_four_post_routes_exist(self):
        """All four ingest/upload routes must be present."""
        from presentation.shadow_gl_endpoints import router

        paths = " ".join(r.path for r in router.routes)
        assert "/dian-xml/ingest" in paths
        assert "/siigo-csv/ingest" in paths
        assert "/siigo-csv/upload" in paths
        assert "/upload" in paths
