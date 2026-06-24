"""
Tests for IdentityResolver (change agent-operations-multitenant-security, Slice 6, design D7).

Resolves the JWT's string identities to the canonical UUIDs the governance tables
use (usuarios.id, tenants.id) before the membership check / cost / audit write.

Two layers:
1. Pure-logic unit tests with an injected fake Supabase client — no DB/env needed.
2. A gated integration test (RUN_AGENT_OPS=1 + SUPABASE_SERVICE_ROLE_KEY) against
   the real Cliente Cero data via the service-role client.
"""

from __future__ import annotations

import os

import pytest

from core.identity_resolver import IdentityResolver, ResolvedIdentity


# --------------------------------------------------------------------------- #
# Fake Supabase client — returns configured rows per table, ignoring filters.
# --------------------------------------------------------------------------- #
class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeQuery:
    def __init__(self, rows, raises: bool = False):
        self._rows = rows
        self._raises = raises

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def execute(self):
        if self._raises:
            raise RuntimeError("simulated supabase failure")
        return _FakeResult(self._rows)


class _FakeClient:
    def __init__(self, table_rows: dict, raises: bool = False):
        self._table_rows = table_rows
        self._raises = raises

    def table(self, name: str):
        return _FakeQuery(self._table_rows.get(name, []), raises=self._raises)


_REAL_USER_UUID = "26216a03-9d4a-4590-bfc3-a4ddf0524d57"
_REAL_TENANT_UUID = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"


class TestUserResolution:
    def test_email_resolves_to_usuarios_id(self):
        r = IdentityResolver(client=_FakeClient({"usuarios": [{"id": _REAL_USER_UUID}]}))
        assert r.resolve_user_uuid("usr_cliente_demo", "cliente@demo.co") == _REAL_USER_UUID

    def test_uuid_sub_passthrough_when_email_missing_in_db(self):
        r = IdentityResolver(client=_FakeClient({"usuarios": []}))
        assert r.resolve_user_uuid(_REAL_USER_UUID, "ghost@nowhere.co") == _REAL_USER_UUID

    def test_non_uuid_sub_with_no_email_match_is_unresolved(self):
        r = IdentityResolver(client=_FakeClient({"usuarios": []}))
        assert r.resolve_user_uuid("usr_cliente_demo", "ghost@nowhere.co") is None

    def test_db_error_fails_closed(self):
        r = IdentityResolver(client=_FakeClient({"usuarios": []}, raises=True))
        assert r.resolve_user_uuid("usr_cliente_demo", "cliente@demo.co") is None


class TestTenantResolution:
    def test_uuid_workspace_passthrough(self):
        r = IdentityResolver(client=_FakeClient({}))
        assert r.resolve_tenant_uuid(_REAL_TENANT_UUID, _REAL_USER_UUID) == _REAL_TENANT_UUID

    def test_company_id_resolves_to_tenant_id(self):
        r = IdentityResolver(client=_FakeClient({"tenants": [{"id": _REAL_TENANT_UUID}]}))
        assert r.resolve_tenant_uuid("ctx-001", _REAL_USER_UUID) == _REAL_TENANT_UUID

    def test_single_membership_fallback(self):
        # workspace is an unusable string; tenant derived from the one active membership
        r = IdentityResolver(
            client=_FakeClient(
                {"tenants": [], "user_tenants": [{"tenant_id": _REAL_TENANT_UUID}]}
            )
        )
        assert r.resolve_tenant_uuid("contexia-org-1", _REAL_USER_UUID) == _REAL_TENANT_UUID

    def test_ambiguous_membership_is_unresolved(self):
        r = IdentityResolver(
            client=_FakeClient(
                {
                    "tenants": [],
                    "user_tenants": [
                        {"tenant_id": _REAL_TENANT_UUID},
                        {"tenant_id": "11111111-1111-1111-1111-111111111111"},
                    ],
                }
            )
        )
        assert r.resolve_tenant_uuid("contexia-org-1", _REAL_USER_UUID) is None

    def test_no_membership_is_unresolved(self):
        r = IdentityResolver(client=_FakeClient({"tenants": [], "user_tenants": []}))
        assert r.resolve_tenant_uuid("contexia-org-1", _REAL_USER_UUID) is None


class TestCombinedResolve:
    def test_demo_identity_fully_resolved(self):
        r = IdentityResolver(
            client=_FakeClient(
                {
                    "usuarios": [{"id": _REAL_USER_UUID}],
                    "tenants": [{"id": _REAL_TENANT_UUID}],
                }
            )
        )
        resolved = r.resolve("usr_cliente_demo", "cliente@demo.co", "ctx-001")
        assert isinstance(resolved, ResolvedIdentity)
        assert resolved.user_uuid == _REAL_USER_UUID
        assert resolved.tenant_uuid == _REAL_TENANT_UUID
        assert resolved.is_complete is True

    def test_unresolvable_user_yields_incomplete(self):
        r = IdentityResolver(client=_FakeClient({"usuarios": [], "tenants": []}))
        resolved = r.resolve("usr_cliente_demo", "ghost@nowhere.co", "contexia-org-1")
        assert resolved.user_uuid is None
        assert resolved.is_complete is False


# --------------------------------------------------------------------------- #
# Live integration (real Cliente Cero data via service-role client)
# --------------------------------------------------------------------------- #
_live = pytest.mark.skipif(
    os.environ.get("RUN_AGENT_OPS") != "1"
    or not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    reason="Set RUN_AGENT_OPS=1 and SUPABASE_SERVICE_ROLE_KEY for live identity tests",
)


@_live
class TestIdentityResolverLive:
    def test_demo_client_resolves_to_real_uuids(self):
        r = IdentityResolver()  # service-role client
        resolved = r.resolve("usr_cliente_demo", "cliente@demo.co", "contexia-org-1")
        assert resolved.user_uuid == _REAL_USER_UUID
        assert resolved.tenant_uuid == _REAL_TENANT_UUID
        assert resolved.is_complete is True
