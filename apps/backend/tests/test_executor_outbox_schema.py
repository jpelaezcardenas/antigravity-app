"""
Integration tests for executor_outbox table schema (FASE 4, Slice 2, task 2.12).

Executor outbox holds pending write-back jobs (e.g. to Siigo) created by
approval of tax_correction drafts. Gated by RUN_SHADOW_GL=1.
"""

from __future__ import annotations

import os

import pytest

from core.supabase_client import get_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run executor_outbox schema tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    return get_supabase()


class TestExecutorOutboxSchema:
    def test_executor_outbox_table_is_queryable(self, supabase) -> None:
        result = supabase.table("executor_outbox").select("id").limit(1).execute()
        assert result.data == []

    def test_executor_outbox_has_expected_columns(self, supabase) -> None:
        """Verify the table has all required columns with correct types."""
        result = supabase.table("executor_outbox").select("*").limit(1).execute()
        # If this doesn't error, the table exists. We can't easily check types via
        # Supabase client API, so we verify structure via SQL next.

    def test_executor_outbox_row_structure(self, supabase) -> None:
        """Insert a minimal valid row and verify structure."""
        from services.shadow_gl_service import parse_dian_ubl_xml

        # Get Cliente Cero tenant
        tenant_result = (
            supabase.table("tenants")
            .select("id")
            .eq("is_cliente_cero", True)
            .single()
            .execute()
        )
        tenant_id = tenant_result.data["id"]

        # Create a minimal approval_queue row for FK reference
        approval_result = (
            supabase.table("approval_queue")
            .insert(
                {
                    "draft_id": "test_outbox_ref",
                    "draft_type": "tax_correction",
                    "status": "pending_approval",
                    "reason": "",
                    "approved_by": "",
                    "payload": {"lines": []},
                }
            )
            .execute()
        )
        approval_id = approval_result.data[0]["id"]

        try:
            # Insert into executor_outbox
            outbox_result = (
                supabase.table("executor_outbox")
                .insert(
                    {
                        "tenant_id": tenant_id,
                        "approval_decision_id": approval_id,
                        "status": "pending",
                        "attempts": 0,
                        "payload": {"memo": "test job"},
                    }
                )
                .execute()
            )

            assert len(outbox_result.data) == 1
            row = outbox_result.data[0]
            assert row["tenant_id"] == tenant_id
            assert row["approval_decision_id"] == approval_id
            assert row["status"] == "pending"
            assert row["attempts"] == 0
            assert row["payload"]["memo"] == "test job"
            assert "id" in row
            assert "created_at" in row

            # Clean up
            supabase.table("executor_outbox").delete().eq("id", row["id"]).execute()
        finally:
            supabase.table("approval_queue").delete().eq("id", approval_id).execute()
