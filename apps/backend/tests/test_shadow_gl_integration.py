"""
Integration tests for Shadow GL: XML DIAN + CSV Siigo in same day (Phase 5).

Run with: pytest test_shadow_gl_integration.py -v
Or with DB: RUN_SHADOW_GL=1 pytest test_shadow_gl_integration.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_XML = (FIXTURES_DIR / "dian_invoice_sample.xml").read_text(encoding="utf-8")
SAMPLE_CSV = (
    FIXTURES_DIR / "contexia_siigo_journal_2026-06-18-to-2026-06-24.csv"
).read_text(encoding="utf-8")


class TestShadowGLIntegration:
    """Verify XML and CSV both work (no DB dependency for parser tests)."""

    def test_dian_xml_parses(self) -> None:
        """XML DIAN parser works."""
        from services.shadow_gl_service import parse_dian_ubl_xml

        parsed = parse_dian_ubl_xml(SAMPLE_XML)
        assert parsed["cufe"] == "test-cufe-0001-synthetic-fixture"
        assert parsed["total_amount_minor"] == 11900000

    def test_siigo_csv_parses(self) -> None:
        """Siigo CSV parser works."""
        from services.shadow_gl_service import parse_siigo_csv

        parsed = parse_siigo_csv(SAMPLE_CSV)
        assert len(parsed) > 0
        assert all("external_reference_id" in entry for entry in parsed)

    def test_xml_and_csv_both_valid(self) -> None:
        """Both formats parse without errors (can be loaded same day)."""
        from services.shadow_gl_service import parse_dian_ubl_xml, parse_siigo_csv

        xml_parsed = parse_dian_ubl_xml(SAMPLE_XML)
        csv_parsed = parse_siigo_csv(SAMPLE_CSV)

        assert xml_parsed is not None
        assert csv_parsed is not None
        # Both can coexist in Shadow GL
        assert len(csv_parsed) >= 1  # At least one CSV entry


@pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Shadow GL integration tests with Supabase",
)
class TestShadowGLIntegrationWithDB:
    """End-to-end: both ingestion paths work together."""

    @pytest.fixture(scope="class")
    def cliente_cero_tenant_id(self) -> str:
        from core.supabase_client import get_supabase

        supabase = get_supabase()
        result = (
            supabase.table("tenants")
            .select("id")
            .eq("is_cliente_cero", True)
            .single()
            .execute()
        )
        return result.data["id"]

    @pytest.fixture(autouse=True)
    def _cleanup(self, cliente_cero_tenant_id):
        """Clean up test data after each test."""
        from core.supabase_client import get_supabase

        supabase = get_supabase()
        yield
        # Delete DIAN and ERP data created during test
        supabase.table("erp_journal_lines").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).execute()
        supabase.table("erp_journal_entries").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).execute()
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).execute()

    @pytest.mark.asyncio
    async def test_ingest_xml_and_csv_same_day(self, cliente_cero_tenant_id) -> None:
        """Upload XML DIAN + CSV Siigo same day → both land in Shadow GL."""
        from services.shadow_gl_service import ingest_dian_xml, ingest_siigo_csv

        # Ingest XML
        xml_success, xml_doc, xml_error = await ingest_dian_xml(
            cliente_cero_tenant_id, SAMPLE_XML
        )
        assert xml_success is True
        assert xml_error is None

        # Ingest CSV
        csv_success, csv_summary, csv_error = await ingest_siigo_csv(
            cliente_cero_tenant_id, SAMPLE_CSV
        )
        assert csv_success is True
        assert csv_error is None

        # Verify both tables populated
        from core.supabase_client import get_supabase

        supabase = get_supabase()

        dian_rows = (
            supabase.table("dian_xml_documents")
            .select("*")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
        )
        assert len(dian_rows.data) >= 1

        erp_entries = (
            supabase.table("erp_journal_entries")
            .select("*")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
        )
        assert len(erp_entries.data) >= 1

    @pytest.mark.asyncio
    async def test_csv_idempotency_no_duplicates(self, cliente_cero_tenant_id) -> None:
        """Re-upload same CSV → no duplicates."""
        from services.shadow_gl_service import ingest_siigo_csv

        # First upload
        success1, summary1, error1 = await ingest_siigo_csv(
            cliente_cero_tenant_id, SAMPLE_CSV
        )
        assert success1 is True
        count1 = summary1["row_count"]

        # Second upload (same data)
        success2, summary2, error2 = await ingest_siigo_csv(
            cliente_cero_tenant_id, SAMPLE_CSV
        )
        assert success2 is True
        # Should not create new rows
        assert summary2["row_count"] == count1
