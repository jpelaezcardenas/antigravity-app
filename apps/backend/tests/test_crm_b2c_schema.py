"""
Integration tests for the CRM B2C sell-machine schema (crm-b2c-sell-machine-cockpit, Change B).

Gated by RUN_CRM_B2B=1 (reuses Change A's gate — same feature area) since they hit the real
Supabase project — mirrors test_crm_b2b_schema.py.
"""

from __future__ import annotations

import os
import pytest

from core.supabase_client import get_service_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CRM_B2B") != "1",
    reason="Set RUN_CRM_B2B=1 to run CRM B2C integration tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    return get_service_supabase()


class TestCrmB2cTablesExist:
    def test_crm_leads_table_is_queryable(self, supabase) -> None:
        result = supabase.table("crm_leads").select("id").limit(1).execute()
        assert isinstance(result.data, list)

    def test_crm_tax_profiles_table_is_queryable(self, supabase) -> None:
        result = supabase.table("crm_tax_profiles").select("id").limit(1).execute()
        assert isinstance(result.data, list)

    def test_crm_wompi_transactions_table_is_queryable(self, supabase) -> None:
        result = supabase.table("crm_wompi_transactions").select("id").limit(1).execute()
        assert isinstance(result.data, list)


class TestCrmB2cSeedData:
    def test_leads_seeded_across_all_four_stages(self, supabase) -> None:
        result = supabase.table("crm_leads").select("id, stage").execute()
        stages_present = {row["stage"] for row in result.data}
        assert stages_present == {"NUEVOS", "PROSPECTOS", "POR_APROBAR", "LISTOS_CONTADORA"}

    def test_every_lead_has_a_tax_profile(self, supabase) -> None:
        leads = supabase.table("crm_leads").select("id").execute()
        profiles = supabase.table("crm_tax_profiles").select("lead_id").execute()
        lead_ids = {row["id"] for row in leads.data}
        profile_lead_ids = {row["lead_id"] for row in profiles.data}
        assert lead_ids == profile_lead_ids

    def test_por_aprobar_leads_have_a_pending_wompi_transaction(self, supabase) -> None:
        por_aprobar = (
            supabase.table("crm_leads").select("id").eq("stage", "POR_APROBAR").execute()
        )
        for lead in por_aprobar.data:
            tx = (
                supabase.table("crm_wompi_transactions")
                .select("id, status, reference")
                .eq("lead_id", lead["id"])
                .execute()
            )
            assert len(tx.data) >= 1
            assert tx.data[0]["status"] == "PENDING"
            assert tx.data[0]["reference"].startswith("SEED-REF-")


class TestCrmB2cRls:
    # RLS enablement + policy correctness verified via direct SQL introspection during migration
    # application (see design.md), not here — mirrors test_crm_b2b_schema.py's TestCrmB2bRls.
    pass
