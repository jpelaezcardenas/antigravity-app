"""
Unit tests for the shared tenant resolver (pwa-tenant-aware-screens Stage 1, design.md D1).

`core.tenant_context.resolve_caller_tenant_id` is the single source of truth for "which
tenant does this caller see" — extracted out of `financials_endpoints.get_financials`'s
previously-inlined policy so Stage 2 (centinela alerts) and Stage 3 (liquidity bridge) can
reuse it instead of re-copying the three branches.

These tests exercise the helper directly, with an injected `cliente_cero_resolver` so they
never touch the network. `tests/test_financials_endpoint_tenant_scoping.py` remains the
regression guard for the endpoint-level, unmodified behavior.
"""

import asyncio

import pytest

from core.deps import _STAGING_USER
from core.tenant_context import resolve_caller_tenant_id


def run(coro):
    return asyncio.run(coro)


class TestResolveCallerTenantId:
    def test_authenticated_caller_with_resolved_tenant_returns_that_tenant(self):
        user = {"id": "user-a", "resolved_tenant_id": "tenant-a"}

        result = run(resolve_caller_tenant_id(user))

        assert result == "tenant-a"

    def test_staging_identity_uses_injected_cliente_cero_resolver(self):
        called = {"count": 0}

        async def fake_resolver():
            called["count"] += 1
            return "cliente-cero-tenant"

        result = run(
            resolve_caller_tenant_id(dict(_STAGING_USER), cliente_cero_resolver=fake_resolver)
        )

        assert result == "cliente-cero-tenant"
        assert called["count"] == 1

    def test_authenticated_unresolved_caller_returns_none_without_invoking_resolver(self):
        async def must_not_be_called():
            raise AssertionError(
                "Cliente Cero resolver must never be invoked for an authenticated, "
                "unresolved caller — that would leak Contexia's own data."
            )

        user = {"id": "some-real-user-id", "resolved_tenant_id": None}

        result = run(
            resolve_caller_tenant_id(user, cliente_cero_resolver=must_not_be_called)
        )

        assert result is None

    def test_resolved_tenant_id_takes_priority_even_for_the_staging_user_id(self):
        """Defensive: branch 1 must win even if a caller somehow shares the staging id."""
        user = dict(_STAGING_USER, resolved_tenant_id="explicit-tenant")

        async def must_not_be_called():
            raise AssertionError("Cliente Cero resolver must not run when resolved_tenant_id is set")

        result = run(resolve_caller_tenant_id(user, cliente_cero_resolver=must_not_be_called))

        assert result == "explicit-tenant"
