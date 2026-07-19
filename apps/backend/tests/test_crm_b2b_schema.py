"""
Integration tests for the CRM B2B retainer schema (crm-b2b-retainers-cockpit, Change A).

Gated by RUN_CRM_B2B=1 since they hit the real Supabase project — mirrors the pattern
used by test_shadow_gl_schema.py for RUN_SHADOW_GL.
"""

from __future__ import annotations

import os
import pytest

from core.supabase_client import get_service_supabase

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CRM_B2B") != "1",
    reason="Set RUN_CRM_B2B=1 to run CRM B2B integration tests against Supabase",
)


@pytest.fixture(scope="module")
def supabase():
    # Service-role client: these tests verify migration/seed correctness (data landed right),
    # which must not depend on RLS visibility. RLS enforcement itself (anon/non-admin blocked)
    # is verified separately via direct SQL during migration application — see TestCrmB2bRls below.
    return get_service_supabase()


class TestCrmB2bTablesExist:
    def test_b2b_clients_table_is_queryable(self, supabase) -> None:
        result = supabase.table("b2b_clients").select("id").limit(1).execute()
        assert isinstance(result.data, list)

    def test_b2b_payments_table_is_queryable(self, supabase) -> None:
        result = supabase.table("b2b_payments").select("id").limit(1).execute()
        assert isinstance(result.data, list)


class TestCrmB2bSeedData:
    def test_ten_clients_seeded(self, supabase) -> None:
        result = supabase.table("b2b_clients").select("id, name, status").execute()
        assert len(result.data) == 10

    def test_sixty_payment_rows_seeded(self, supabase) -> None:
        result = supabase.table("b2b_payments").select("id", count="exact").execute()
        assert result.count == 60

    def test_repuestos_don_alvaro_march_typo_is_corrected(self, supabase) -> None:
        client = (
            supabase.table("b2b_clients")
            .select("id")
            .ilike("name", "%don%lvaro%")
            .single()
            .execute()
        )
        payment = (
            supabase.table("b2b_payments")
            .select("amount_cents")
            .eq("client_id", client.data["id"])
            .eq("period", "2026-03-01")
            .single()
            .execute()
        )
        assert payment.data["amount_cents"] == 120_000_000  # 1,200,000 COP in minor units

    def test_grand_total_matches_fixture(self, supabase) -> None:
        result = supabase.table("b2b_payments").select("amount_cents").execute()
        grand_total_cents = sum(row["amount_cents"] for row in result.data)
        # Fixture computed from the corrected source ledger (COP, then *100 for minor units):
        # Don Alvaro 1.2M*5 (jun=0) + Medic 2M*6 + Nia Cano 600k + Lavadero 600k*6
        # + Carniceria 2M*3 + Ferez 890k*4 + Variedades 890k*4 + Surge 400k + Clinic 400k + Maderas 1.2M
        expected_cop = (
            1_200_000 * 5
            + 2_000_000 * 6
            + 600_000
            + 600_000 * 6
            + 2_000_000 * 3
            + 890_000 * 4
            + 890_000 * 4
            + 400_000
            + 400_000
            + 1_200_000
        )
        assert grand_total_cents == expected_cop * 100


class TestCrmB2bRls:
    # RLS enablement + policy correctness are verified via direct SQL introspection during
    # migration application (see design.md "Migration Plan" and Task 2.3), not here — the
    # get_supabase() client used in these fixtures is service-role-capable and bypasses RLS
    # by design, so it cannot itself prove RLS is enforced.
    pass
