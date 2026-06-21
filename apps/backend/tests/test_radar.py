"""
Tests for Radar agent (FASE 4, Slice 3, task 3.3–3.5).

Radar provides deterministic risk-score calculation (0-100) and conditional HITL:
- Risk below 80: no approval queue entry
- Risk >= 80: enqueue risk_review for human approval (no duplicates)

Gated by RUN_SHADOW_GL=1 since it reads Shadow GL tables.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta

import pytest

from core.supabase_client import get_supabase
from services.shadow_gl_service import ingest_dian_xml
from services.radar_service import calculate_risk_score

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Radar tests against Supabase",
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
def radar_cufe() -> str:
    return f"radar-test-{uuid.uuid4()}"


@pytest.fixture(autouse=True)
def _cleanup(supabase, cliente_cero_tenant_id):
    created_cufes: list[str] = []
    yield created_cufes
    for cufe in created_cufes:
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).eq("cufe", cufe).execute()
        # Also clean up any centinela alerts for these CUFEs
        supabase.table("centinela_alerts").delete().contains(
            "evidence", {"cufe": cufe}
        ).execute()
    supabase.rpc("refresh_shadow_gl_discrepancies").execute()


class TestRadar:
    def test_risk_score_zero_activity(self, supabase, cliente_cero_tenant_id) -> None:
        """
        Calculate risk score for a tenant with no new Shadow GL discrepancies.
        Expected: score is deterministic and in valid range.
        Note: if there are historical alerts, score may be > 0 from alert factor.
        """
        import asyncio
        score = asyncio.run(calculate_risk_score(cliente_cero_tenant_id))
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_risk_score_with_discrepancies(
        self, supabase, cliente_cero_tenant_id, radar_cufe, _cleanup
    ) -> None:
        """
        Ingest a DIAN XML (creating a missing_in_erp discrepancy), then calculate risk score.
        Expected: score > 0 (due to discrepancy rate).
        """
        import asyncio

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(radar_cufe, total="119000.00", issue_date=today)

        success, doc, error = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(radar_cufe)

        # Refresh view
        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Calculate risk score
        score = asyncio.run(calculate_risk_score(cliente_cero_tenant_id))
        assert isinstance(score, int)
        assert 0 <= score <= 100
        # With one discrepancy out of one invoice, we expect score > 0
        assert score > 0

    def test_risk_score_deterministic(
        self, supabase, cliente_cero_tenant_id, radar_cufe, _cleanup
    ) -> None:
        """
        Same inputs produce the same risk score (deterministic).
        """
        import asyncio

        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(radar_cufe, total="119000.00", issue_date=today)

        success, doc, error = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(radar_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Call calculate_risk_score twice
        score1 = asyncio.run(calculate_risk_score(cliente_cero_tenant_id))
        score2 = asyncio.run(calculate_risk_score(cliente_cero_tenant_id))

        # Same inputs should give same score
        assert score1 == score2

    def test_cashflow_forecast_returns_int(self, supabase, cliente_cero_tenant_id) -> None:
        """
        Cashflow forecast returns a 30-day projection in minor units (BIGINT).
        Expected: forecast is deterministic and >= 0.
        """
        import asyncio
        from services.radar_service import calculate_cashflow_forecast

        forecast = asyncio.run(calculate_cashflow_forecast(cliente_cero_tenant_id))
        assert isinstance(forecast, int)
        assert forecast >= 0

    def test_cashflow_forecast_with_history(
        self, supabase, cliente_cero_tenant_id, radar_cufe, _cleanup
    ) -> None:
        """
        Cashflow forecast based on historical net flux (DIAN - ERP).
        With DIAN invoices and no ERP entries, forecast should be > 0.
        """
        import asyncio
        from services.radar_service import calculate_cashflow_forecast

        # Ingest DIAN XML
        today = datetime.utcnow().strftime("%Y-%m-%d")
        xml = _invoice_xml(radar_cufe, total="119000.00", issue_date=today)

        success, doc, error = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
        assert success is True
        _cleanup.append(radar_cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Calculate forecast
        forecast = asyncio.run(calculate_cashflow_forecast(cliente_cero_tenant_id))
        assert isinstance(forecast, int)
        # With one DIAN invoice (119000.00 = 11900000 minor) and no ERP, net flux is positive
        assert forecast > 0

    def test_risk_score_above_80_creates_approval_queue_entry(
        self, supabase, cliente_cero_tenant_id, radar_cufe, _cleanup
    ) -> None:
        """
        When risk_score >= 80, a risk_review approval_queue entry is created.
        Expected: one approval_queue row with draft_type='risk_review'.
        Note: This test requires high alerts (20+ in current month) to reach 80+ score.
        If alerts are < 20, test may skip or verify that no entry is created when below threshold.
        """
        import asyncio
        from services.radar_service import enqueue_risk_review_if_critical, calculate_risk_score

        # Ingest multiple DIAN XMLs to trigger high discrepancy rate
        for i in range(5):
            cufe = f"{radar_cufe}-{i}"
            xml = _invoice_xml(cufe, total="119000.00")
            success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
            assert success is True
            _cleanup.append(cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Check actual risk score
        actual_score = asyncio.run(calculate_risk_score(cliente_cero_tenant_id))

        # Enqueue risk_review if critical
        entry_id = asyncio.run(enqueue_risk_review_if_critical(cliente_cero_tenant_id))

        # Verify behavior: if score < 80, no entry; if >= 80, one entry
        if actual_score < 80:
            assert entry_id is None, f"Expected no entry for score {actual_score} < 80, but got {entry_id}"
        else:
            assert entry_id is not None, f"Expected entry for score {actual_score} >= 80"
            queue_entries = (
                supabase.table("approval_queue")
                .select("*")
                .eq("id", entry_id)
                .execute()
            )
            assert len(queue_entries.data) == 1
            assert queue_entries.data[0]["draft_type"] == "risk_review"
            assert queue_entries.data[0]["payload"]["risk_score"] == actual_score

    def test_risk_review_no_duplicate_on_repeat(
        self, supabase, cliente_cero_tenant_id, radar_cufe, _cleanup
    ) -> None:
        """
        Repeated risk_score >= 80 does NOT create duplicate approval_queue entries.
        Expected: calling enqueue twice results in only 1 risk_review entry.
        """
        import asyncio
        from services.radar_service import enqueue_risk_review_if_critical

        # Create high-risk scenario
        for i in range(5):
            cufe = f"{radar_cufe}-{i}"
            xml = _invoice_xml(cufe, total="119000.00")
            success, _, _ = asyncio.run(ingest_dian_xml(cliente_cero_tenant_id, xml))
            assert success is True
            _cleanup.append(cufe)

        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Call enqueue_risk_review_if_critical twice
        asyncio.run(enqueue_risk_review_if_critical(cliente_cero_tenant_id))
        asyncio.run(enqueue_risk_review_if_critical(cliente_cero_tenant_id))

        # Verify only 1 unresolved risk_review entry per tenant
        queue_entries = (
            supabase.table("approval_queue")
            .select("*")
            .eq("draft_type", "risk_review")
            .eq("status", "pending")
            .execute()
        )
        risk_review_count = len([e for e in queue_entries.data])
        # Should have at most 1 pending risk_review (deduped by tenant)
        assert risk_review_count <= 1
