"""
Integration tests for the operator_tasks schema (hermes-manus-execution-bridge, Change F).

Gated by RUN_OPERATOR_TASKS=1 since they hit the real Supabase project — mirrors the pattern
used by test_crm_b2b_schema.py for RUN_CRM_B2B.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_service_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_OPERATOR_TASKS") != "1",
    reason="Set RUN_OPERATOR_TASKS=1 to run operator_tasks integration tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    return get_service_supabase()


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


class TestOperatorTasksTableExists:
    def test_operator_tasks_table_is_queryable(self, supabase) -> None:
        result = supabase.table("operator_tasks").select("id").limit(1).execute()
        assert isinstance(result.data, list)


class TestOperatorTasksConstraints:
    def test_task_type_check_constraint_rejects_invalid_value(
        self, supabase, cliente_cero_tenant_id
    ) -> None:
        with pytest.raises(Exception):
            supabase.table("operator_tasks").insert(
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": cliente_cero_tenant_id,
                    "task_type": "not_a_real_type",
                    "payload": {},
                }
            ).execute()

    def test_status_check_constraint_rejects_invalid_value(
        self, supabase, cliente_cero_tenant_id
    ) -> None:
        with pytest.raises(Exception):
            supabase.table("operator_tasks").insert(
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": cliente_cero_tenant_id,
                    "task_type": "research",
                    "status": "not_a_real_status",
                    "payload": {},
                }
            ).execute()

    def test_valid_row_inserts_with_default_pending_status(
        self, supabase, cliente_cero_tenant_id
    ) -> None:
        row_id = str(uuid.uuid4())
        supabase.table("operator_tasks").insert(
            {
                "id": row_id,
                "tenant_id": cliente_cero_tenant_id,
                "task_type": "research",
                "payload": {"note": "schema test row"},
            }
        ).execute()
        result = (
            supabase.table("operator_tasks").select("status").eq("id", row_id).single().execute()
        )
        assert result.data["status"] == "pending"
        supabase.table("operator_tasks").delete().eq("id", row_id).execute()


class TestOperatorTasksRls:
    # RLS enablement + policy correctness are verified via direct SQL introspection during
    # migration application (see design.md "Migration Plan" and Task 2.3), not here — the
    # get_service_supabase() client used in these fixtures is service-role-capable and bypasses
    # RLS by design, so it cannot itself prove RLS is enforced.
    pass
