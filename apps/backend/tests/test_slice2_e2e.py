"""
End-to-end test for Slice 2 complete workflow (FASE 4, task 2.16 Stage 11).

Manual ingestion → parsing → Shadow GL discrepancy detection → Resolution Agent
draft generation → Approval Queue enqueue → Executor Outbox job creation.

This test demonstrates the full Slice 2 functionality in a single flow.
Gated by RUN_SHADOW_GL=1 and RUN_APPROVAL_QUEUE_DB=1.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_supabase
from services.approval_queue_service import ApprovalQueueService
from services.centinela_resolution_service import poll_shadow_gl_discrepancies
from services.resolution_agent_service import generate_draft_with_retry
from services.shadow_gl_service import ingest_dian_xml, parse_dian_ubl_xml

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1" or os.environ.get("RUN_APPROVAL_QUEUE_DB") != "1",
    reason="Set RUN_SHADOW_GL=1 and RUN_APPROVAL_QUEUE_DB=1 to run Slice 2 E2E test",
)


def _invoice_xml(cufe: str, total: str = "119000.00", tax: str = "19000.00") -> str:
    """Synthetic UBL 2.1 Invoice (missing_in_erp scenario)."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:UUID schemeName="CUFE-SHA384">{cufe}</cbc:UUID>
  <cbc:IssueDate>2026-06-21</cbc:IssueDate>
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
def e2e_cufe() -> str:
    return f"e2e-test-{uuid.uuid4()}"


@pytest.fixture(autouse=True)
def _cleanup(supabase, cliente_cero_tenant_id):
    created_cufes: list[str] = []
    created_decision_ids: list[str] = []
    created_outbox_ids: list[str] = []
    yield created_cufes, created_decision_ids, created_outbox_ids

    # Cleanup
    for cufe in created_cufes:
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).eq("cufe", cufe).execute()
        supabase.table("centinela_alerts").delete().contains("evidence", {"cufe": cufe}).execute()
    for decision_id in created_decision_ids:
        supabase.table("approval_queue").delete().eq("id", decision_id).execute()
    for outbox_id in created_outbox_ids:
        supabase.table("executor_outbox").delete().eq("id", outbox_id).execute()
    supabase.rpc("refresh_shadow_gl_discrepancies").execute()


class TestSlice2EndToEnd:
    @pytest.mark.asyncio
    async def test_complete_slice2_workflow(
        self, supabase, cliente_cero_tenant_id, e2e_cufe, _cleanup
    ) -> None:
        """
        End-to-end flow:
        1. Ingest DIAN XML (missing_in_erp scenario)
        2. Refresh discrepancies view
        3. Poll for new discrepancies → create Centinela alert
        4. Generate Resolution Agent draft
        5. Approve draft → create executor_outbox job
        """
        created_cufes, created_decision_ids, created_outbox_ids = _cleanup

        # 1. Ingest DIAN XML
        xml = _invoice_xml(e2e_cufe)
        success, doc, error = await ingest_dian_xml(cliente_cero_tenant_id, xml)
        assert success is True, f"Ingestion failed: {error}"
        assert doc["cufe"] == e2e_cufe
        created_cufes.append(e2e_cufe)

        # 2. Refresh discrepancies view
        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        # 3. Poll for discrepancies → Centinela alert
        alert_ids = await poll_shadow_gl_discrepancies(cliente_cero_tenant_id)
        assert len(alert_ids) == 1, f"Expected 1 alert, got {len(alert_ids)}"

        # Verify alert was created
        alert = (
            supabase.table("centinela_alerts")
            .select("*")
            .eq("id", alert_ids[0])
            .single()
            .execute()
        )
        assert alert.data["evidence"]["cufe"] == e2e_cufe
        assert alert.data["evidence"]["discrepancy_status"] == "missing_in_erp"

        # 4. Generate Resolution Agent draft
        decision_id, decision = await generate_draft_with_retry(
            tenant_id=cliente_cero_tenant_id, cufe=e2e_cufe, max_retries=2
        )
        assert decision_id is not None, "Draft generation failed"
        created_decision_ids.append(decision_id)

        # Verify draft in approval_queue
        draft_row = (
            supabase.table("approval_queue")
            .select("*")
            .eq("id", decision_id)
            .single()
            .execute()
        )
        assert draft_row.data["draft_type"] == "tax_correction"
        assert draft_row.data["status"] == "pending_approval"

        # 5. Approve draft → executor_outbox job
        success, approved, error = await ApprovalQueueService.approve_draft(
            decision_id=decision_id,
            approval_reason="E2E test approval",
            approved_by="e2e@test.local",
        )
        assert success is True, f"Approval failed: {error}"

        # Verify executor_outbox job was created
        outbox_rows = (
            supabase.table("executor_outbox")
            .select("*")
            .eq("approval_decision_id", decision_id)
            .execute()
        )
        assert len(outbox_rows.data) == 1, "Executor outbox job not created"
        outbox_job = outbox_rows.data[0]
        created_outbox_ids.append(outbox_job["id"])

        # Verify outbox job structure
        assert outbox_job["status"] == "pending"
        assert outbox_job["attempts"] == 0
        assert outbox_job["payload"]["approval_id"] == decision_id

        # Final verification: entire chain is complete
        print(f"[OK] E2E Slice 2 workflow completed for CUFE {e2e_cufe}")
        print(f"  - DIAN XML ingested")
        print(f"  - Discrepancy detected: {alert_ids[0][:8]}...")
        print(f"  - Draft generated: {decision_id[:8]}...")
        print(f"  - Outbox job created: {outbox_job['id'][:8]}...")
