"""
Tests for Centinela's Shadow GL discrepancy poller (FASE 4, Slice 2, task 2.9).

Polls shadow_gl_discrepancies and creates one centinela_alerts row per new
discrepancy, deduplicating against discrepancies that already have an
unresolved alert. Gated by RUN_SHADOW_GL=1 since it hits live Supabase.
"""

from __future__ import annotations

import os
import uuid

import pytest

from core.supabase_client import get_supabase
from services.centinela_resolution_service import (
    SHADOW_GL_DISCREPANCY_RULE_ID,
    poll_shadow_gl_discrepancies,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Centinela resolution poller tests against Supabase",
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
    return f"test-poller-cufe-{uuid.uuid4()}"


@pytest.fixture(autouse=True)
def _cleanup(supabase, cliente_cero_tenant_id):
    created_cufes: list[str] = []
    yield created_cufes
    for cufe in created_cufes:
        supabase.table("dian_xml_documents").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).eq("cufe", cufe).execute()
        supabase.table("centinela_alerts").delete().eq(
            "rule_id", SHADOW_GL_DISCREPANCY_RULE_ID
        ).contains("evidence", {"cufe": cufe}).execute()
    supabase.rpc("refresh_shadow_gl_discrepancies").execute()


class TestPollShadowGlDiscrepancies:
    @pytest.mark.asyncio
    async def test_poll_creates_alert_for_missing_in_erp_discrepancy(
        self, supabase, cliente_cero_tenant_id, fresh_cufe, _cleanup
    ) -> None:
        supabase.table("dian_xml_documents").insert(
            {
                **_parse_for_insert(fresh_cufe),
                "tenant_id": cliente_cero_tenant_id,
                "raw_xml": _invoice_xml(fresh_cufe),
            }
        ).execute()
        _cleanup.append(fresh_cufe)
        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        created_ids = await poll_shadow_gl_discrepancies(cliente_cero_tenant_id)
        assert len(created_ids) == 1

        alert = (
            supabase.table("centinela_alerts")
            .select("*")
            .eq("id", created_ids[0])
            .single()
            .execute()
        )
        assert alert.data["rule_id"] == SHADOW_GL_DISCREPANCY_RULE_ID
        assert alert.data["evidence"]["cufe"] == fresh_cufe
        assert alert.data["evidence"]["discrepancy_status"] == "missing_in_erp"

    @pytest.mark.asyncio
    async def test_poll_does_not_duplicate_alert_on_repeat(
        self, supabase, cliente_cero_tenant_id, fresh_cufe, _cleanup
    ) -> None:
        supabase.table("dian_xml_documents").insert(
            {
                **_parse_for_insert(fresh_cufe),
                "tenant_id": cliente_cero_tenant_id,
                "raw_xml": _invoice_xml(fresh_cufe),
            }
        ).execute()
        _cleanup.append(fresh_cufe)
        supabase.rpc("refresh_shadow_gl_discrepancies").execute()

        first_ids = await poll_shadow_gl_discrepancies(cliente_cero_tenant_id)
        second_ids = await poll_shadow_gl_discrepancies(cliente_cero_tenant_id)

        assert len(first_ids) == 1
        assert len(second_ids) == 0

        alerts = (
            supabase.table("centinela_alerts")
            .select("id")
            .eq("rule_id", SHADOW_GL_DISCREPANCY_RULE_ID)
            .contains("evidence", {"cufe": fresh_cufe})
            .execute()
        )
        assert len(alerts.data) == 1


def _parse_for_insert(cufe: str) -> dict:
    from services.shadow_gl_service import parse_dian_ubl_xml

    return parse_dian_ubl_xml(_invoice_xml(cufe))
