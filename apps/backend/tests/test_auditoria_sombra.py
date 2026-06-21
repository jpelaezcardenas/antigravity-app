"""
Tests for Auditoría Sombra agent (FASE 4, Slice 3, task 3.6–3.7).

Auditoría Sombra generates PDF audit reports summarizing Shadow GL coverage.
- Internal report (no HITL): immediate download URL
- External report (HITL): approval queue entry, URL withheld until approved

Gated by RUN_SHADOW_GL=1 since it reads Shadow GL tables.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

import pytest

from core.supabase_client import get_supabase
from services.shadow_gl_service import ingest_dian_xml

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Auditoría Sombra tests against Supabase",
)


def _invoice_xml(cufe: str, total: str = "119000.00", issue_date: str = None) -> str:
    """Synthetic UBL 2.1 Invoice."""
    if issue_date is None:
        issue_date = datetime.utcnow().strftime("%Y-%m-%d")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:UUID schemeName="CUFE-SHA384">{cufe}</cbc:UUID>
  <cbc:IssueDate>{issue_date}</cbc:IssueDate>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyTaxScheme>
    <cbc:CompanyID>900000000</cbc:CompanyID>
  </cac:PartyTaxScheme></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyTaxScheme>
    <cbc:CompanyID>800123456</cbc:CompanyID>
  </cac:PartyTaxScheme></cac:Party></cac:AccountingCustomerParty>
  <cac:TaxTotal><cbc:TaxAmount currencyID="COP">19000.00</cbc:TaxAmount></cac:TaxTotal>
  <cac:LegalMonetaryTotal><cbc:PayableAmount currencyID="COP">{total}</cbc:PayableAmount></cac:LegalMonetaryTotal>
</Invoice>"""


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


@pytest.fixture
def audit_cufe() -> str:
    return f"audit-test-{uuid.uuid4()}"


@pytest.fixture(autouse=True)
def _cleanup(supabase, cliente_cero_tenant_id):
    created_cufes: list[str] = []
    yield created_cufes
    for cufe in created_cufes:
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).eq("cufe", cufe).execute()
    supabase.rpc("refresh_shadow_gl_discrepancies").execute()


class TestAuditoriaSombra:
    def test_generate_internal_report_returns_pdf(
        self, supabase, cliente_cero_tenant_id, audit_cufe, _cleanup
    ) -> None:
        """
        Generate internal audit report returns PDF bytes.
        Expected: PDF content is not None, starts with PDF magic bytes.
        """
        import asyncio
        from services.auditoria_sombra_service import generate_audit_report

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(audit_cufe, total="119000.00", issue_date=today)

        success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(audit_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Generate internal report
        date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_end = datetime.utcnow().strftime("%Y-%m-%d")

        pdf_bytes = asyncio.run(
            generate_audit_report(cliente_cero_tenant_id, date_start, date_end, audience="internal")
        )

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        # PDF files start with %PDF magic bytes
        assert pdf_bytes.startswith(b"%PDF")

    def test_internal_report_includes_statistics(
        self, supabase, cliente_cero_tenant_id, audit_cufe, _cleanup
    ) -> None:
        """
        Internal report PDF includes: transactions reviewed, discrepancies found/resolved/open.
        Expected: PDF contains statistics (approximated by checking for numeric content).
        """
        import asyncio
        from services.auditoria_sombra_service import generate_audit_report

        # Ingest multiple invoices
        for i in range(3):
            cufe = f"{audit_cufe}-{i}"
            xml = _invoice_xml(cufe, total="119000.00")
            success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
            assert success is True
            _cleanup.append(cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_end = datetime.utcnow().strftime("%Y-%m-%d")

        pdf_bytes = asyncio.run(
            generate_audit_report(cliente_cero_tenant_id, date_start, date_end, audience="internal")
        )

        assert pdf_bytes is not None
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")
        # PDF should contain real content (at least 500 bytes with stats)
        assert len(pdf_bytes) > 500
        # Verify PDF contains key statistics text
        assert b"Total Transactions" in pdf_bytes
        assert b"Discrepancies Found" in pdf_bytes

    def test_report_generation_is_readonly(
        self, supabase, cliente_cero_tenant_id, audit_cufe, _cleanup
    ) -> None:
        """
        Report generation does not modify Shadow GL tables.
        Expected: DIAN and discrepancies counts unchanged after report gen.
        """
        import asyncio
        from services.auditoria_sombra_service import generate_audit_report

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(audit_cufe, total="119000.00", issue_date=today)

        success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(audit_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Count before
        dian_before = (
            supabase.table("dian_xml_documents")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
        )
        count_before = len(dian_before.data)

        # Generate report
        date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_end = datetime.utcnow().strftime("%Y-%m-%d")

        asyncio.run(
            generate_audit_report(cliente_cero_tenant_id, date_start, date_end, audience="internal")
        )

        # Count after
        dian_after = (
            supabase.table("dian_xml_documents")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
        )
        count_after = len(dian_after.data)

        # Should be unchanged
        assert count_before == count_after

    def test_internal_report_returns_download_url_immediately(
        self, supabase, cliente_cero_tenant_id, audit_cufe, _cleanup
    ) -> None:
        """
        Internal report request returns download URL immediately, no approval queue.
        Expected: download_url is non-None, no approval_queue entry.
        """
        import asyncio
        from services.auditoria_sombra_service import request_audit_report

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(audit_cufe, total="119000.00", issue_date=today)

        success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(audit_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_end = datetime.utcnow().strftime("%Y-%m-%d")

        result = asyncio.run(
            request_audit_report(cliente_cero_tenant_id, date_start, date_end, audience="internal")
        )

        assert result is not None
        assert result["download_url"] is not None
        assert result["signoff_required"] is False
        assert result["approval_queue_id"] is None
        assert result["status"] == "available"

    def test_external_report_requires_signoff(
        self, supabase, cliente_cero_tenant_id, audit_cufe, _cleanup
    ) -> None:
        """
        External report request creates audit_report_signoff approval_queue entry.
        Expected: download_url is None until approved, approval_queue_id is set.
        """
        import asyncio
        from services.auditoria_sombra_service import request_audit_report

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(audit_cufe, total="119000.00", issue_date=today)

        success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(audit_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_end = datetime.utcnow().strftime("%Y-%m-%d")

        result = asyncio.run(
            request_audit_report(cliente_cero_tenant_id, date_start, date_end, audience="external")
        )

        assert result is not None
        assert result["download_url"] is None
        assert result["signoff_required"] is True
        assert result["approval_queue_id"] is not None
        assert result["status"] == "pending_signoff"

        # Verify approval_queue entry exists with draft_type='audit_report_signoff'
        queue_entry = (
            supabase.table("approval_queue")
            .select("*")
            .eq("id", result["approval_queue_id"])
            .single()
            .execute()
        )
        assert queue_entry.data["draft_type"] == "audit_report_signoff"
        assert queue_entry.data["status"] == "pending"
        assert "tenant_id" in queue_entry.data["payload"]
        assert "date_start" in queue_entry.data["payload"]
        assert "date_end" in queue_entry.data["payload"]

        # Cleanup
        supabase.table("approval_queue").delete().eq("id", result["approval_queue_id"]).execute()

    def test_rejected_external_report_remains_inaccessible(
        self, supabase, cliente_cero_tenant_id, audit_cufe, _cleanup
    ) -> None:
        """
        When external report signoff is rejected, download URL remains None.
        Expected: report status becomes 'rejected', download_url stays None.
        """
        import asyncio
        from services.auditoria_sombra_service import request_audit_report, get_audit_report_status

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(audit_cufe, total="119000.00", issue_date=today)

        success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(audit_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        date_end = datetime.utcnow().strftime("%Y-%m-%d")

        # Request external report
        result = asyncio.run(
            request_audit_report(cliente_cero_tenant_id, date_start, date_end, audience="external")
        )
        approval_id = result["approval_queue_id"]

        # Reject via approval_queue update
        supabase.table("approval_queue").update(
            {"status": "rejected", "reason": "External audit not approved"}
        ).eq("id", approval_id).execute()

        # Check status
        status_result = asyncio.run(get_audit_report_status(approval_id))
        assert status_result is not None
        assert status_result["status"] == "rejected"
        assert status_result["download_url"] is None

        # Cleanup
        supabase.table("approval_queue").delete().eq("id", approval_id).execute()
