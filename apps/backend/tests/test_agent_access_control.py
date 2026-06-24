"""
Tests for AgentAccessControl (change agent-operations-multitenant-security, Slice 2).

Two layers:
1. Pure-logic unit tests with an injected fake Supabase client — no DB/env needed.
2. A gated integration test (RUN_AGENT_OPS=1 + SUPABASE_SERVICE_ROLE_KEY) against
   the real Cliente Cero memberships via the service-role client.
"""

from __future__ import annotations

import os

import pytest

from core.agent_access_control import AgentAccessControl, AccessDecision


# --------------------------------------------------------------------------- #
# Fake Supabase client (mimics the .table().select().eq()...execute() chain)
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
    """Returns configured rows per table, ignoring filters (logic-level fake)."""

    def __init__(self, table_rows: dict, raises: bool = False):
        self._table_rows = table_rows
        self._raises = raises

    def table(self, name: str):
        return _FakeQuery(self._table_rows.get(name, []), raises=self._raises)


MEMBER_ROWS = {
    "user_tenants": [{"id": "ut-1"}],
    "user_roles": [{"role": "admin"}],
}
NON_MEMBER_ROWS = {"user_tenants": [], "user_roles": []}


class TestAccessControlLogic:
    def test_member_is_allowed(self):
        ac = AgentAccessControl(client=_FakeClient(MEMBER_ROWS))
        decision = ac.check_access("u1", "t1", "pulso")
        assert isinstance(decision, AccessDecision)
        assert decision.allowed is True
        assert decision.status == "allowed"
        assert decision.role == "admin"

    def test_non_member_is_blocked(self):
        ac = AgentAccessControl(client=_FakeClient(NON_MEMBER_ROWS))
        decision = ac.check_access("u1", "t-other", "pulso")
        assert decision.allowed is False
        assert decision.status == "blocked"
        assert decision.reason == "not_a_member"

    def test_missing_tenant_is_blocked(self):
        ac = AgentAccessControl(client=_FakeClient(MEMBER_ROWS))
        decision = ac.check_access("u1", "", "pulso")
        assert decision.allowed is False
        assert decision.reason == "missing_tenant"

    def test_missing_user_is_blocked(self):
        ac = AgentAccessControl(client=_FakeClient(MEMBER_ROWS))
        decision = ac.check_access("", "t1", "pulso")
        assert decision.allowed is False
        assert decision.reason == "missing_user"

    def test_db_error_fails_closed(self):
        ac = AgentAccessControl(client=_FakeClient(MEMBER_ROWS, raises=True))
        decision = ac.check_access("u1", "t1", "pulso")
        assert decision.allowed is False
        assert decision.reason == "access_check_error"

    def test_can_read_full_audit_only_for_privileged_roles(self):
        admin = AgentAccessControl(client=_FakeClient({"user_roles": [{"role": "admin"}]}))
        viewer = AgentAccessControl(client=_FakeClient({"user_roles": [{"role": "viewer"}]}))
        assert admin.can_read_full_audit("u1", "t1") is True
        assert viewer.can_read_full_audit("u1", "t1") is False


# --------------------------------------------------------------------------- #
# Live integration (real Cliente Cero data via service-role client)
# --------------------------------------------------------------------------- #
_CLIENTE_CERO_TENANT = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"
_ADMIN_USER = "abf2af3a-f5bb-4628-850f-d2edd037c972"

_live = pytest.mark.skipif(
    os.environ.get("RUN_AGENT_OPS") != "1"
    or not os.environ.get("SUPABASE_SERVICE_ROLE_KEY"),
    reason="Set RUN_AGENT_OPS=1 and SUPABASE_SERVICE_ROLE_KEY for live access-control tests",
)


@_live
class TestAccessControlLive:
    def test_real_member_allowed(self):
        ac = AgentAccessControl()  # service-role client
        decision = ac.check_access(_ADMIN_USER, _CLIENTE_CERO_TENANT, "pulso")
        assert decision.allowed is True
        assert decision.role == "admin"

    def test_real_user_blocked_in_foreign_tenant(self):
        ac = AgentAccessControl()
        decision = ac.check_access(
            _ADMIN_USER, "00000000-0000-0000-0000-000000000000", "pulso"
        )
        assert decision.allowed is False
        assert decision.reason == "not_a_member"
