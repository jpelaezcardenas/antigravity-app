"""
Unit/integration tests for crm_service.py (crm-b2b-retainers-cockpit, Change A).

Gated by RUN_CRM_B2B=1 since they hit the real Supabase project — same convention
as test_crm_b2b_schema.py and test_shadow_gl_schema.py.
"""

from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CRM_B2B") != "1",
    reason="Set RUN_CRM_B2B=1 to run CRM service integration tests against Supabase",
)


class TestListB2bClients:
    def test_returns_source_and_all_ten_clients(self) -> None:
        from services.crm_service import get_crm_service

        result = get_crm_service().list_b2b_clients()

        assert result["source"] in ("supabase", "demo_fallback")
        # 9 original retainer clients (Nia Cano removed — never an actual client, see
        # migration 0030) + CÓDIGO 520 (per-tenant-client-access: a new, not-yet-paying
        # prospect added to the roster) = 10.
        assert len(result["items"]) == 10
        names = {item["name"] for item in result["items"]}
        assert "Medic" in names
        assert "CÓDIGO 520" in names
        assert "Nia Cano" not in names
        assert any("lvaro" in name for name in names)  # Repuestos Don Álvaro (accent-safe match)


class TestB2bPaymentsGrid:
    def test_grid_shape_has_clients_periods_and_cells(self) -> None:
        from services.crm_service import get_crm_service

        result = get_crm_service().b2b_payments_grid(from_period="2026-01-01", to_period="2026-06-30")

        assert "grid" in result
        assert "clients" in result["grid"]
        assert "periods" in result["grid"]
        assert "cells" in result["grid"]
        assert len(result["grid"]["periods"]) == 6

    def test_grand_total_matches_seed_fixture(self) -> None:
        from services.crm_service import get_crm_service

        result = get_crm_service().b2b_payments_grid(from_period="2026-01-01", to_period="2026-06-30")

        # Nia Cano (600,000 in March) removed from the roster entirely — see migration 0030,
        # she was never an actual Contexia client. CÓDIGO 520 (new, not-yet-paying) contributes
        # 0 to this sum by design.
        expected_cop = (
            1_200_000 * 5
            + 2_000_000 * 6
            + 600_000 * 6
            + 2_000_000 * 3
            + 890_000 * 4
            + 890_000 * 4
            + 400_000
            + 400_000
            + 1_200_000
        )
        assert result["totals"]["grand_total"] == expected_cop * 100

    def test_by_client_total_matches_a_known_client(self) -> None:
        from services.crm_service import get_crm_service

        result = get_crm_service().b2b_payments_grid(from_period="2026-01-01", to_period="2026-06-30")

        clients_by_name = {c["name"]: c["id"] for c in result["grid"]["clients"]}
        medic_id = clients_by_name["Medic"]
        assert result["totals"]["by_client"][medic_id] == 2_000_000 * 6 * 100
