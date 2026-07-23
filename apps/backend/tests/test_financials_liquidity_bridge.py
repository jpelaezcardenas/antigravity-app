"""
Tests for the monthly liquidity bridge (pwa-tenant-aware-screens Stage 3).

Covers `compute_liquidity_bridge` (services/financials_service.py) and, indirectly, the
`GET /api/v1/financials/liquidity-bridge` route wiring exercised via the service layer it
delegates to.

Uses the same hermetic, throwaway-tenant pattern as `test_financials_aggregation.py` — see
that module's docstring for why real Cliente Cero data must never back these assertions.
"""

import uuid

import pytest
from datetime import date, timedelta

from core.supabase_client import get_supabase
from tests.test_financials_aggregation import insert_test_entry


@pytest.fixture
def test_tenant_id():
    """Hermetic, throwaway tenant — mirrors `test_financials_aggregation.test_tenant_id`."""
    supabase = get_supabase()
    nit = f"TEST-BRIDGE-{uuid.uuid4().hex[:12]}"
    inserted = (
        supabase.table("tenants")
        .insert(
            {
                "nit": nit,
                "legal_name": "Hermetic Bridge Test Tenant (pytest, safe to delete)",
                "is_cliente_cero": False,
            }
        )
        .execute()
    )
    tenant_id = inserted.data[0]["id"]

    yield tenant_id

    supabase.table("erp_journal_lines").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("erp_journal_entries").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("tenants").delete().eq("id", tenant_id).execute()


@pytest.fixture
def two_test_tenants():
    """Two hermetic, throwaway tenants — mirrors the tenant-scoping regression suite."""
    supabase = get_supabase()
    tenant_ids = []
    for label in ("A", "B"):
        nit = f"TEST-BRIDGE-{label}-{uuid.uuid4().hex[:10]}"
        inserted = (
            supabase.table("tenants")
            .insert({"nit": nit, "legal_name": f"Hermetic Bridge Tenant {label} (pytest)", "is_cliente_cero": False})
            .execute()
        )
        tenant_ids.append(inserted.data[0]["id"])

    yield tenant_ids

    for tenant_id in tenant_ids:
        supabase.table("erp_journal_lines").delete().eq("tenant_id", tenant_id).execute()
        supabase.table("erp_journal_entries").delete().eq("tenant_id", tenant_id).execute()
        supabase.table("tenants").delete().eq("id", tenant_id).execute()


@pytest.fixture
def cleanup_test_entries():
    created_ids = []
    yield created_ids
    supabase = get_supabase()
    for entry_id in created_ids:
        supabase.table("erp_journal_lines").delete().eq("entry_id", entry_id).execute()
        supabase.table("erp_journal_entries").delete().eq("id", entry_id).execute()


class TestComputeLiquidityBridge:
    def test_bridge_math_with_opening_balance_and_in_month_movements(
        self, test_tenant_id, cleanup_test_entries
    ):
        """
        initial_balance = cumulative 1110 balance as of the day before the month starts.
        inflows/outflows = sum of in-month 1110 debits/credits.
        final_balance = initial_balance + inflows - outflows.
        """
        from services.financials_service import compute_liquidity_bridge

        supabase = get_supabase()
        today = date.today()
        month_start = today.replace(day=1)
        prior_day = month_start - timedelta(days=1)

        opening_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-OPEN-001", prior_day,
            [
                {"account_code": "1110", "debit_minor": 500000000, "memo": "opening balance"},
                {"account_code": "1205", "credit_minor": 500000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(opening_entry)

        inflow_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-IN-001", month_start,
            [
                {"account_code": "1110", "debit_minor": 200000000, "memo": "inflow"},
                {"account_code": "1205", "credit_minor": 200000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(inflow_entry)

        outflow_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-OUT-001", month_start,
            [
                {"account_code": "1110", "credit_minor": 80000000, "memo": "outflow"},
                {"account_code": "1205", "debit_minor": 80000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(outflow_entry)

        bridge = compute_liquidity_bridge(test_tenant_id, today.year, today.month)

        assert bridge["initial_balance"] == 500000000
        assert bridge["inflows"] == 200000000
        assert bridge["outflows"] == 80000000
        assert bridge["final_balance"] == 620000000
        assert bridge["period"] == f"{today.year:04d}-{today.month:02d}"
        assert bridge["status"] == "ready"

    def test_final_balance_matches_equivalent_caja_real(self, test_tenant_id, cleanup_test_entries):
        """
        final_balance must equal `_compute_caja_real_balance` for the last day of the month —
        the two independently-derived values must not diverge (design.md D3 / spec scenario
        "Final balance matches the equivalent Caja Real balance").
        """
        from services.financials_service import compute_liquidity_bridge, _compute_caja_real_balance
        from calendar import monthrange

        supabase = get_supabase()
        today = date.today()
        month_start = today.replace(day=1)
        prior_day = month_start - timedelta(days=1)
        _, last_day = monthrange(today.year, today.month)
        month_end = today.replace(day=last_day)

        opening_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-MATCH-OPEN", prior_day,
            [
                {"account_code": "1110", "debit_minor": 300000000, "memo": "opening"},
                {"account_code": "1205", "credit_minor": 300000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(opening_entry)

        movement_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-MATCH-MOVE", month_start,
            [
                {"account_code": "1110", "debit_minor": 90000000, "memo": "movement"},
                {"account_code": "1205", "credit_minor": 90000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(movement_entry)

        bridge = compute_liquidity_bridge(test_tenant_id, today.year, today.month)
        expected_final = _compute_caja_real_balance(supabase, test_tenant_id, month_end)

        assert bridge["final_balance"] == expected_final

    def test_empty_tenant_returns_zeroed_empty_status(self, test_tenant_id):
        """No 1110 lines at all -> zeroed, non-error response with status='empty'."""
        from services.financials_service import compute_liquidity_bridge

        today = date.today()
        bridge = compute_liquidity_bridge(test_tenant_id, today.year, today.month)

        assert bridge["initial_balance"] == 0
        assert bridge["inflows"] == 0
        assert bridge["outflows"] == 0
        assert bridge["final_balance"] == 0
        assert bridge["period"] == f"{today.year:04d}-{today.month:02d}"
        assert bridge["status"] == "empty"

    def test_tenant_isolation(self, two_test_tenants, cleanup_test_entries):
        """Tenant A's bridge reflects only A's lines, tenant B's only B's lines."""
        from services.financials_service import compute_liquidity_bridge

        tenant_a, tenant_b = two_test_tenants
        supabase = get_supabase()
        today = date.today()
        month_start = today.replace(day=1)

        entry_a = insert_test_entry(
            supabase, tenant_a, "BRIDGE-ISO-A", month_start,
            [
                {"account_code": "1110", "debit_minor": 150000000, "memo": "A inflow"},
                {"account_code": "1205", "credit_minor": 150000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_a)

        entry_b = insert_test_entry(
            supabase, tenant_b, "BRIDGE-ISO-B", month_start,
            [
                {"account_code": "1110", "debit_minor": 400000000, "memo": "B inflow"},
                {"account_code": "1205", "credit_minor": 400000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_b)

        bridge_a = compute_liquidity_bridge(tenant_a, today.year, today.month)
        bridge_b = compute_liquidity_bridge(tenant_b, today.year, today.month)

        assert bridge_a["inflows"] == 150000000
        assert bridge_b["inflows"] == 400000000
        assert bridge_a["inflows"] != bridge_b["inflows"]

    def test_month_boundary_excludes_prior_and_next_month_movements(
        self, test_tenant_id, cleanup_test_entries
    ):
        """
        Movements dated before month_start or after month_end must not be counted as
        inflows/outflows — they belong to `initial_balance` (if before) or a future
        bridge query (if after), not this month's in-month sums.
        """
        from services.financials_service import compute_liquidity_bridge
        from calendar import monthrange

        supabase = get_supabase()
        today = date.today()
        month_start = today.replace(day=1)
        prior_day = month_start - timedelta(days=1)
        _, last_day = monthrange(today.year, today.month)
        month_end = today.replace(day=last_day)
        next_month_start = month_end + timedelta(days=1)

        before_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-BOUND-BEFORE", prior_day,
            [
                {"account_code": "1110", "debit_minor": 100000000, "memo": "before month"},
                {"account_code": "1205", "credit_minor": 100000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(before_entry)

        in_month_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-BOUND-IN", month_end,
            [
                {"account_code": "1110", "debit_minor": 20000000, "memo": "last day of month"},
                {"account_code": "1205", "credit_minor": 20000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(in_month_entry)

        after_entry = insert_test_entry(
            supabase, test_tenant_id, "BRIDGE-BOUND-AFTER", next_month_start,
            [
                {"account_code": "1110", "debit_minor": 999000000, "memo": "next month, must not count"},
                {"account_code": "1205", "credit_minor": 999000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(after_entry)

        bridge = compute_liquidity_bridge(test_tenant_id, today.year, today.month)

        assert bridge["initial_balance"] == 100000000
        assert bridge["inflows"] == 20000000
        assert bridge["outflows"] == 0
        assert bridge["final_balance"] == 120000000
