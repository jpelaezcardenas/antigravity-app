"""
Integration tests for the Shadow GL substrate (FASE 4, Slice 1).

Gated by RUN_SHADOW_GL=1 since they hit the real Supabase project — mirrors
the pattern used by test_kb_seeding.py for RUN_KB_PGVECTOR.
"""

from __future__ import annotations

import os
import pytest

from core.supabase_client import get_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Shadow GL integration tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    return get_supabase()


class TestTenants:
    def test_cliente_cero_tenant_exists(self, supabase) -> None:
        result = (
            supabase.table("tenants")
            .select("id, legal_name, is_cliente_cero")
            .eq("is_cliente_cero", True)
            .execute()
        )
        assert len(result.data) == 1
        assert "contexia" in result.data[0]["legal_name"].lower()

    def test_only_one_tenant_can_be_cliente_cero(self, supabase) -> None:
        with pytest.raises(Exception):
            supabase.table("tenants").insert(
                {
                    "nit": "999999999",
                    "legal_name": "Segundo Cliente Cero SAS",
                    "is_cliente_cero": True,
                }
            ).execute()


class TestShadowGlTablesExist:
    def test_dian_xml_documents_table_is_queryable(self, supabase) -> None:
        result = supabase.table("dian_xml_documents").select("id").limit(1).execute()
        assert result.data == []

    def test_erp_journal_entries_table_is_queryable(self, supabase) -> None:
        result = supabase.table("erp_journal_entries").select("id").limit(1).execute()
        assert result.data == []

    def test_erp_journal_lines_table_is_queryable(self, supabase) -> None:
        result = supabase.table("erp_journal_lines").select("id").limit(1).execute()
        assert result.data == []


class TestDoubleEntryTrigger:
    def test_unbalanced_journal_lines_are_rejected(self, supabase) -> None:
        tenant = (
            supabase.table("tenants")
            .select("id")
            .eq("is_cliente_cero", True)
            .single()
            .execute()
        )
        tenant_id = tenant.data["id"]

        entry = (
            supabase.table("erp_journal_entries")
            .insert({"tenant_id": tenant_id, "memo": "test unbalanced entry"})
            .execute()
        )
        entry_id = entry.data[0]["id"]

        try:
            with pytest.raises(Exception):
                supabase.table("erp_journal_lines").insert(
                    [
                        {
                            "entry_id": entry_id,
                            "tenant_id": tenant_id,
                            "debit_minor": 100000,
                            "credit_minor": 0,
                            "account_code": "1105",
                        },
                        {
                            "entry_id": entry_id,
                            "tenant_id": tenant_id,
                            "debit_minor": 0,
                            "credit_minor": 90000,
                            "account_code": "4135",
                        },
                    ]
                ).execute()
        finally:
            supabase.table("erp_journal_entries").delete().eq("id", entry_id).execute()


class TestShadowGlDiscrepanciesView:
    def test_view_returns_no_rows_with_no_dian_data(self, supabase) -> None:
        result = supabase.table("shadow_gl_discrepancies").select("cufe").execute()
        assert result.data == []
