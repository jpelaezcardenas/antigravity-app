"""
Integration tests for the agent_operations table schema
(change: agent-operations-multitenant-security, Slice 1).

agent_operations is the per-invocation audit log for every agent call routed
through the WebSocket invoke_agent() chokepoint: who (user_id), in which tenant
(tenant_id), what (agent_name/operation_type), outcome (status), timing
(duration_ms), cost, and the input/output payloads.

Gated by RUN_AGENT_OPS=1 so it only runs against a real Supabase (branch or prod).
"""

from __future__ import annotations

import os

import pytest

from core.supabase_client import get_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_AGENT_OPS") != "1",
    reason="Set RUN_AGENT_OPS=1 to run agent_operations schema tests against Supabase",
)

EXPECTED_COLUMNS = {
    "id",
    "agent_name",
    "user_id",
    "tenant_id",
    "operation_type",
    "status",
    "duration_ms",
    "cost",
    "input_data",
    "output_data",
    "error_message",
    "created_at",
}


@pytest.fixture(scope="module")
def supabase():
    return get_supabase()


@pytest.fixture(scope="module")
def cliente_cero_tenant_id(supabase) -> str:
    result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    return result.data["id"]


class TestAgentOperationsSchema:
    def test_agent_operations_table_is_queryable(self, supabase) -> None:
        result = supabase.table("agent_operations").select("id").limit(1).execute()
        assert result.data == []

    def test_agent_operations_has_expected_columns(self, supabase) -> None:
        """A successfully inserted row must expose every required column."""
        result = supabase.table("agent_operations").select("*").limit(1).execute()
        # Empty table is fine; structure is asserted by the insert test below.
        assert isinstance(result.data, list)

    def test_agent_operations_row_structure(
        self, supabase, cliente_cero_tenant_id
    ) -> None:
        """Insert a minimal valid row and verify the audit structure."""
        insert_result = (
            supabase.table("agent_operations")
            .insert(
                {
                    "agent_name": "pulso",
                    "user_id": "test-user-0001",
                    "tenant_id": cliente_cero_tenant_id,
                    "operation_type": "summary",
                    "status": "success",
                    "duration_ms": 42,
                    "cost": 0.005,
                    "input_data": {"params": {}},
                    "output_data": {"caja_real": "1000.00"},
                    "error_message": None,
                }
            )
            .execute()
        )

        assert len(insert_result.data) == 1
        row = insert_result.data[0]
        assert EXPECTED_COLUMNS.issubset(set(row.keys()))
        assert row["agent_name"] == "pulso"
        assert row["tenant_id"] == cliente_cero_tenant_id
        assert row["status"] == "success"
        assert row["duration_ms"] == 42

        # Clean up
        supabase.table("agent_operations").delete().eq("id", row["id"]).execute()

    def test_agent_operations_status_check_rejects_unknown(
        self, supabase, cliente_cero_tenant_id
    ) -> None:
        """status must be one of success | failed | blocked (CHECK constraint)."""
        with pytest.raises(Exception):
            supabase.table("agent_operations").insert(
                {
                    "agent_name": "pulso",
                    "user_id": "test-user-0001",
                    "tenant_id": cliente_cero_tenant_id,
                    "operation_type": "summary",
                    "status": "not_a_real_status",
                }
            ).execute()
