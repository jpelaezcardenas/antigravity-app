"""
E2E tests for cost tracking aggregation
(change agent-operations-multitenant-security, Slice 5.2).

Tests that costs are correctly summed across multiple operations,
and that the cost matrix is accurately reflected in the database.

These tests require:
- RUN_AGENT_OPS=1 (enable integration tests)
- SUPABASE_SERVICE_ROLE_KEY (for service-role reads)
- Live Supabase project with agent_operations table
"""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

from core.supabase_client import get_service_supabase
from services.agent_cost_tracker import AgentCostTracker


class TestCostTrackingE2E:
    """Verify cost aggregation across agent operations."""

    @pytest.fixture
    def run_agent_ops(self) -> bool:
        """Check if integration tests are enabled."""
        return os.getenv("RUN_AGENT_OPS") == "1"

    def test_cost_aggregation_per_tenant(self, run_agent_ops):
        """Multiple operations are correctly summed per tenant."""
        if not run_agent_ops:
            pytest.skip("RUN_AGENT_OPS not set")

        service_role = get_service_supabase()
        tenant_e = "tenant-e-111"
        user_e = "user-e@example.com"

        try:
            # Insert multiple operations with known costs.
            service_role.table("agent_operations").insert([
                {
                    "tenant_id": tenant_e,
                    "agent_name": "pulso",
                    "user_id": user_e,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 500,
                    "cost": 0.005,
                    "input_data": {},
                    "output_data": {},
                },
                {
                    "tenant_id": tenant_e,
                    "agent_name": "centinela",
                    "user_id": user_e,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 800,
                    "cost": 0.01,
                    "input_data": {},
                    "output_data": {},
                },
                {
                    "tenant_id": tenant_e,
                    "agent_name": "radar",
                    "user_id": user_e,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 600,
                    "cost": 0.008,
                    "input_data": {},
                    "output_data": {},
                },
            ]).execute()

            # Aggregate costs for this tenant.
            result = service_role.table("agent_operations").select(
                "cost"
            ).eq("tenant_id", tenant_e).execute()

            total_cost = sum(float(row["cost"]) for row in result.data)
            expected_cost = 0.005 + 0.01 + 0.008  # 0.023

            assert abs(total_cost - expected_cost) < 0.001, (
                f"Expected total cost ~{expected_cost}, got {total_cost}"
            )

        finally:
            # Cleanup.
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_e
            ).execute()

    def test_cost_matrix_matches_database_records(self, run_agent_ops):
        """Recorded costs match the AgentCostTracker matrix."""
        if not run_agent_ops:
            pytest.skip("RUN_AGENT_OPS not set")

        service_role = get_service_supabase()
        cost_tracker = AgentCostTracker()
        tenant_f = "tenant-f-222"
        user_f = "user-f@example.com"

        try:
            # Create operations for known cost matrix entries.
            operations = [
                ("pulso", "invoke", "success", 0.005),
                ("centinela", "invoke", "success", 0.01),
                ("radar", "invoke", "success", 0.008),
                ("audit", "invoke", "success", 0.025),
            ]

            rows_to_insert = [
                {
                    "tenant_id": tenant_f,
                    "agent_name": agent,
                    "user_id": user_f,
                    "operation_type": op_type,
                    "status": status,
                    "duration_ms": 1000,
                    "cost": cost,
                    "input_data": {},
                    "output_data": {},
                }
                for agent, op_type, status, cost in operations
            ]

            service_role.table("agent_operations").insert(rows_to_insert).execute()

            # Verify costs match the tracker.
            for agent, op_type, status, expected_cost in operations:
                # Resolve cost from tracker.
                resolved_cost = cost_tracker.resolve_cost_for_status(
                    agent, op_type, status=status
                )

                # Query database for the recorded cost.
                db_result = service_role.table("agent_operations").select(
                    "cost"
                ).eq("tenant_id", tenant_f).eq("agent_name", agent).execute()

                assert len(db_result.data) >= 1
                recorded_cost = float(db_result.data[0]["cost"])

                assert recorded_cost == float(expected_cost), (
                    f"{agent}:{op_type}: expected {expected_cost}, "
                    f"got {recorded_cost}"
                )
                assert float(resolved_cost) == float(expected_cost), (
                    f"Tracker mismatch for {agent}: {resolved_cost} != {expected_cost}"
                )

        finally:
            # Cleanup.
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_f
            ).execute()

    def test_failed_operations_still_incur_cost(self, run_agent_ops):
        """Operations with status='failed' still have cost recorded (not zero)."""
        if not run_agent_ops:
            pytest.skip("RUN_AGENT_OPS not set")

        service_role = get_service_supabase()
        cost_tracker = AgentCostTracker()
        tenant_g = "tenant-g-333"
        user_g = "user-g@example.com"

        try:
            # Insert a failed operation (should have non-zero cost).
            cost_for_failed = cost_tracker.resolve_cost_for_status(
                "pulso", "invoke", status="failed"
            )

            service_role.table("agent_operations").insert([
                {
                    "tenant_id": tenant_g,
                    "agent_name": "pulso",
                    "user_id": user_g,
                    "operation_type": "invoke",
                    "status": "failed",
                    "duration_ms": 1000,
                    "cost": float(cost_for_failed),
                    "input_data": {},
                    "error_message": "timeout",
                },
            ]).execute()

            # Retrieve and verify the cost.
            result = service_role.table("agent_operations").select(
                "status, cost"
            ).eq("tenant_id", tenant_g).eq("status", "failed").execute()

            assert len(result.data) >= 1
            recorded_cost = float(result.data[0]["cost"])
            assert recorded_cost > 0, "Failed operations should have non-zero cost"

        finally:
            # Cleanup.
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_g
            ).execute()
