"""
Tests for DIAN UBL 2.1 ingestion (FASE 4, Slice 2, manual-upload scope).

Parser tests run unconditionally (pure function, no DB). Persistence tests
are gated by RUN_SHADOW_GL=1, same convention as test_shadow_gl_schema.py.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.supabase_client import get_supabase
from services.shadow_gl_service import (
    DianXmlParseError,
    ingest_dian_xml,
    parse_dian_ubl_xml,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_INVOICE_XML = (FIXTURES_DIR / "dian_invoice_sample.xml").read_text(encoding="utf-8")


class TestParseDianUblXml:
    def test_parses_valid_invoice(self) -> None:
        parsed = parse_dian_ubl_xml(SAMPLE_INVOICE_XML)
        assert parsed["cufe"] == "test-cufe-0001-synthetic-fixture"
        assert parsed["document_type"] == "invoice"
        assert parsed["issuer_nit"] == "900000000"
        assert parsed["receiver_nit"] == "800123456"
        assert parsed["issue_date"] == "2026-06-15"
        assert parsed["total_amount_minor"] == 11900000
        assert parsed["tax_amount_minor"] == 1900000
        assert parsed["withholding_amount_minor"] == 0
        assert parsed["currency_code"] == "COP"

    def test_rejects_malformed_xml(self) -> None:
        with pytest.raises(DianXmlParseError):
            parse_dian_ubl_xml("<Invoice><unclosed>")

    def test_rejects_unsupported_root_element(self) -> None:
        with pytest.raises(DianXmlParseError):
            parse_dian_ubl_xml("<NotAnInvoice/>")

    def test_rejects_missing_required_field(self) -> None:
        xml_missing_cufe = SAMPLE_INVOICE_XML.replace(
            "<cbc:UUID schemeName=\"CUFE-SHA384\">test-cufe-0001-synthetic-fixture</cbc:UUID>",
            "",
        )
        with pytest.raises(DianXmlParseError, match="UUID"):
            parse_dian_ubl_xml(xml_missing_cufe)


@pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Shadow GL ingestion persistence tests against Supabase",
)
class TestIngestDianXmlPersistence:
    @pytest.fixture(scope="class")
    def cliente_cero_tenant_id(self) -> str:
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
        supabase = get_supabase()
        yield
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).eq("cufe", "test-cufe-0001-synthetic-fixture").execute()

    @pytest.mark.asyncio
    async def test_ingest_persists_document(self, cliente_cero_tenant_id) -> None:
        success, document, error = await ingest_dian_xml(
            cliente_cero_tenant_id, SAMPLE_INVOICE_XML
        )
        assert success is True
        assert error is None
        assert document["cufe"] == "test-cufe-0001-synthetic-fixture"
        assert document["raw_xml"] == SAMPLE_INVOICE_XML

    @pytest.mark.asyncio
    async def test_duplicate_cufe_is_idempotent(self, cliente_cero_tenant_id) -> None:
        first_success, first_doc, _ = await ingest_dian_xml(
            cliente_cero_tenant_id, SAMPLE_INVOICE_XML
        )
        second_success, second_doc, second_error = await ingest_dian_xml(
            cliente_cero_tenant_id, SAMPLE_INVOICE_XML
        )

        assert first_success is True
        assert second_success is True
        assert second_error is None
        assert first_doc["id"] == second_doc["id"]

        supabase = get_supabase()
        rows = (
            supabase.table("dian_xml_documents")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .eq("cufe", "test-cufe-0001-synthetic-fixture")
            .execute()
        )
        assert len(rows.data) == 1

    @pytest.mark.asyncio
    async def test_malformed_xml_is_not_persisted(self, cliente_cero_tenant_id) -> None:
        success, document, error = await ingest_dian_xml(
            cliente_cero_tenant_id, "<NotAnInvoice/>"
        )
        assert success is False
        assert document is None
        assert error is not None
