"""
Tests for Resolution Agent draft generation (FASE 4, Slice 2, task 2.10).

Takes a shadow_gl_discrepancies row (e.g. amount_mismatch) and generates a
balanced tax_correction draft via LLM cascade (Groq → Cerebras → OpenRouter →
Mistral), then enqueues it to approval_queue. The draft must satisfy Agent
Critic's balance constraint before persisting.

Gated by RUN_SHADOW_GL=1 since it hits Supabase + live LLM inference.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_supabase
from services.resolution_agent_service import generate_draft

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Resolution Agent tests (requires live Supabase + LLM inference)",
)


def _invoice_xml(cufe: str, total: str = "119000.00", tax: str = "19000.00") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:UUID schemeName="CUFE-SHA384">{cufe}</cbc:UUID>
  <cbc:IssueDate>2026-06-15</cbc:IssueDate>
  <cac:AccountingSupplierParty><cac:Party><cac:PartyTaxScheme>
    <cbc:CompanyID>900000000</cbc:CompanyID>
  </cac:PartyTaxScheme></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cac:PartyTaxScheme>
    <cbc:CompanyID>800123456</cbc:CompanyID>
  </cac:PartyTaxScheme></cac:Party></cac:AccountingCustomerParty>
  <cac:TaxTotal><cbc:TaxAmount currencyID="COP">{tax}</cbc:TaxAmount></cac:TaxTotal>
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
def fresh_cufe() -> str:
    return f"test-resolution-cufe-{uuid.uuid4()}"


@pytest.fixture(autouse=True)
def _cleanup(supabase, cliente_cero_tenant_id):
    created_cufes: list[str] = []
    created_decision_ids: list[str] = []
    yield created_cufes, created_decision_ids
    for cufe in created_cufes:
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).eq("cufe", cufe).execute()
    for decision_id in created_decision_ids:
        supabase.table("approval_queue").delete().eq("id", decision_id).execute()
    supabase.rpc("refresh_shadow_gl_discrepancies").execute()


class TestResolutionAgentDraftGeneration:
    @pytest.mark.asyncio
    async def test_generates_balanced_draft_from_amount_mismatch(
        self, supabase, cliente_cero_tenant_id, fresh_cufe, _cleanup
    ) -> None:
        """
        Seed a DIAN XML with total 119000, no ERP entry (missing_in_erp).
        Call ResolutionAgentService.generate_draft, which:
        1. Queries shadow_gl_discrepancies for the fresh_cufe
        2. Calls LLM to generate a balanced journal entry (debit + credit = DIAN total)
        3. Enqueues to approval_queue as draft_type='tax_correction'

        Assert:
        - Draft is created in approval_queue (status='pending_approval')
        - Draft payload has balanced lines (SUM debit = SUM credit)
        - Draft can be queried from approval_queue
        """
        from services.shadow_gl_service import parse_dian_ubl_xml

        created_cufes, created_decision_ids = _cleanup

        # Ingest DIAN XML
        xml = _invoice_xml(fresh_cufe)
        parsed = parse_dian_ubl_xml(xml)
        supabase.table("dian_xml_documents").insert(
            {**parsed, "tenant_id": cliente_cero_tenant_id, "raw_xml": xml}
        ).execute()
        created_cufes.append(fresh_cufe)

        # Refresh view to detect discrepancy
        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # Generate draft via Resolution Agent
        decision_id, decision = await generate_draft(
            tenant_id=cliente_cero_tenant_id, cufe=fresh_cufe
        )
        assert decision_id is not None
        assert decision is not None
        created_decision_ids.append(decision_id)

        # Verify draft is in approval_queue
        row = (
            supabase.table("approval_queue")
            .select("*")
            .eq("id", decision_id)
            .single()
            .execute()
        )
        assert row.data["draft_type"] == "tax_correction"
        assert row.data["status"] == "pending_approval"

        # Verify payload lines are balanced
        payload = row.data["payload"]
        assert "lines" in payload
        lines = payload["lines"]
        assert len(lines) >= 2

        total_debit = sum(line.get("debit", 0) for line in lines)
        total_credit = sum(line.get("credit", 0) for line in lines)
        assert total_debit == total_credit, f"Unbalanced: debit={total_debit}, credit={total_credit}"
