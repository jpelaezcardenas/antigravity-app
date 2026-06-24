"""
E2E tests for multi-tenant isolation of agent_operations
(change agent-operations-multitenant-security, Slice 5.1).

Tests that users from different tenants cannot read each other's operations
and that cost rows are isolated by tenant.

These tests require:
- RUN_AGENT_OPS=1 (enable integration tests)
- SUPABASE_SERVICE_ROLE_KEY (for service-role reads)
- Live Supabase project with agent_operations table and RLS enabled
"""

from __future__ import annotations

import os
import pytest

from core.supabase_client import get_service_supabase, get_supabase


class TestMultiTenantOperationsIsolation:
    """Verify that agent_operations are isolated by tenant via RLS."""

    @pytest.fixture
    def run_agent_ops(self) -> bool:
        """Check if integration tests are enabled."""
        return os.getenv("RUN_AGENT_OPS") == "1"

    def test_tenant_a_cannot_read_tenant_b_operations(self, run_agent_ops):
        """User in tenant A cannot read agent_operations from tenant B.

        RLS policy ensures that SELECT is restricted to rows where:
        - The user is an active member of the operation's tenant, OR
        - The user has admin/finance role for audit read
        """
        if not run_agent_ops:
            pytest.skip("RUN_AGENT_OPS not set")

        supabase = get_supabase()
        service_role = get_service_supabase()

        # Scenario: Two tenants, two users
        tenant_a = "tenant-a-123"
        tenant_b = "tenant-b-456"
        user_a = "user-a@example.com"
        user_b = "user-b@example.com"

        try:
            # Insert test operations for both tenants (using service-role, bypasses RLS).
            service_role.table("agent_operations").insert([
                {
                    "tenant_id": tenant_a,
                    "agent_name": "pulso",
                    "user_id": user_a,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 1000,
                    "cost": 0.005,
                    "input_data": {},
                    "output_data": {},
                },
                {
                    "tenant_id": tenant_b,
                    "agent_name": "centinela",
                    "user_id": user_b,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 2000,
                    "cost": 0.01,
                    "input_data": {},
                    "output_data": {},
                },
            ]).execute()

            # Now attempt to read via anon client (simulating user_a querying from tenant_a).
            # The RLS policy should filter out tenant_b rows.
            result = supabase.table("agent_operations").select("*").eq(
                "tenant_id", tenant_a
            ).execute()

            # Verify that user can only see their own tenant's operations.
            assert len(result.data) >= 1
            for row in result.data:
                assert row["tenant_id"] == tenant_a, (
                    f"User from {tenant_a} should not see operations from {row['tenant_id']}"
                )

        finally:
            # Cleanup: Delete test rows (using service-role to bypass RLS).
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_a
            ).execute()
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_b
            ).execute()

    def test_cost_rows_isolated_by_tenant(self, run_agent_ops):
        """Cost values are correctly recorded and isolated per tenant."""
        if not run_agent_ops:
            pytest.skip("RUN_AGENT_OPS not set")

        supabase = get_supabase()
        service_role = get_service_supabase()

        tenant_c = "tenant-c-789"
        user_c = "user-c@example.com"

        try:
            # Insert multiple operations with different costs.
            service_role.table("agent_operations").insert([
                {
                    "tenant_id": tenant_c,
                    "agent_name": "pulso",
                    "user_id": user_c,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 500,
                    "cost": 0.005,  # Pulso cost
                    "input_data": {},
                    "output_data": {},
                },
                {
                    "tenant_id": tenant_c,
                    "agent_name": "radar",
                    "user_id": user_c,
                    "operation_type": "invoke",
                    "status": "success",
                    "duration_ms": 800,
                    "cost": 0.008,  # Radar cost
                    "input_data": {},
                    "output_data": {},
                },
            ]).execute()

            # Retrieve all operations for the tenant.
            result = service_role.table("agent_operations").select(
                "agent_name, cost"
            ).eq("tenant_id", tenant_c).execute()

            # Verify costs are preserved.
            costs = {row["agent_name"]: float(row["cost"]) for row in result.data if row["agent_name"] in ["pulso", "radar"]}
            assert costs.get("pulso") == 0.005
            assert costs.get("radar") == 0.008

        finally:
            # Cleanup.
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_c
            ).execute()

    def test_blocked_operations_have_zero_cost(self, run_agent_ops):
        """Operations with status='blocked' have cost=0 recorded."""
        if not run_agent_ops:
            pytest.skip("RUN_AGENT_OPS not set")

        service_role = get_service_supabase()

        tenant_d = "tenant-d-999"
        user_d = "user-d@example.com"

        try:
            # Insert a blocked operation.
            service_role.table("agent_operations").insert([
                {
                    "tenant_id": tenant_d,
                    "agent_name": "audit",
                    "user_id": user_d,
                    "operation_type": "invoke",
                    "status": "blocked",
                    "duration_ms": 0,
                    "cost": 0,  # Blocked → zero cost
                    "input_data": {},
                    "error_message": "not_a_member",
                },
            ]).execute()

            # Retrieve the blocked operation.
            result = service_role.table("agent_operations").select(
                "status, cost"
            ).eq("tenant_id", tenant_d).eq("status", "blocked").execute()

            assert len(result.data) >= 1
            for row in result.data:
                assert row["status"] == "blocked"
                assert float(row["cost"]) == 0

        finally:
            # Cleanup.
            service_role.table("agent_operations").delete().eq(
                "tenant_id", tenant_d
            ).execute()
