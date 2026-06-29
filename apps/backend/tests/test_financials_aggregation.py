"""
Test suite for Pulso financials aggregation from Shadow GL.

Tests the aggregation service that computes Caja Real, ventas_periodo, and salidas_periodo
from erp_journal_lines for the Cliente Cero tenant.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from core.supabase_client import get_supabase


@pytest.fixture
def cliente_cero_tenant_id():
    """Fixture: resolve Cliente Cero tenant ID from Supabase."""
    supabase = get_supabase()
    result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    return result.data["id"]


@pytest.fixture
def cleanup_test_entries(cliente_cero_tenant_id):
    """Fixture: cleanup test journal entries after each test."""
    created_ids = []
    yield created_ids

    supabase = get_supabase()
    for entry_id in created_ids:
        supabase.table("erp_journal_entries").delete().eq("id", entry_id).execute()
        supabase.table("erp_journal_lines").delete().eq("entry_id", entry_id).execute()


def insert_test_entry(supabase, tenant_id, ref_id: str, entry_date: date, lines: list):
    """Helper: insert a test journal entry with lines."""
    entry_data = {
        "tenant_id": tenant_id,
        "external_reference_id": ref_id,
        "entry_date": entry_date.isoformat(),
        "memo": f"Test entry {ref_id}",
        "source": "test_fixture",
        "uploaded_at": datetime.utcnow().isoformat(),
    }
    inserted = supabase.table("erp_journal_entries").insert(entry_data).execute()
    entry_id = inserted.data[0]["id"]

    line_data = [
        {
            "entry_id": entry_id,
            "tenant_id": tenant_id,
            "account_code": line["account_code"],
            "debit_minor": line.get("debit_minor", 0),
            "credit_minor": line.get("credit_minor", 0),
            "memo": line.get("memo", ""),
            "currency_code": "COP",
        }
        for line in lines
    ]
    supabase.table("erp_journal_lines").insert(line_data).execute()

    return entry_id


class TestFinancialsAggregation:
    """Test suite for GET /api/v1/financials aggregation."""

    def test_caja_real_equals_bank_account_balance(self, cliente_cero_tenant_id, cleanup_test_entries):
        """
        Test: Caja Real = balance of account 1110 (Bancos) = sum(debit_minor) - sum(credit_minor).

        Setup: Insert two entries on account 1110:
          - Entry 1: debit 11,250,000.00 (debits = 1,125,000,000 cents)
          - Entry 2: credit 7,730,000.00 (credits = 773,000,000 cents)

        Expected: caja_real = 352,000,000 cents (3,520,000.00 COP)
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        # Entry 1: debit
        entry1_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "BANK-001",
            today,
            [{"account_code": "1110", "debit_minor": 1125000000, "memo": "Bancos debit"}],
        )
        cleanup_test_entries.append(entry1_id)

        # Entry 2: credit
        entry2_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "BANK-002",
            today,
            [{"account_code": "1110", "credit_minor": 773000000, "memo": "Bancos credit"}],
        )
        cleanup_test_entries.append(entry2_id)

        snapshot = compute_pulso_snapshot(cliente_cero_tenant_id, today.year, today.month)

        assert snapshot["caja_real"] == 352000000, f"Expected 352000000, got {snapshot['caja_real']}"

    def test_ventas_periodo_sums_income_credits(self, cliente_cero_tenant_id, cleanup_test_entries):
        """
        Test: Ventas = sum of credit_minor over income accounts (4100, 4105) in current month.

        Setup: Insert entries on income accounts:
          - 4100: credit 24,700,000.00 (2,470,000,000 cents)
          - 4105: credit 5,100,000.00 (510,000,000 cents)

        Expected: ventas_periodo = 2,980,000,000 cents (29,800,000.00 COP)
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry1_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "SALES-001",
            today,
            [{"account_code": "4100", "credit_minor": 2470000000, "memo": "Ingresos software"}],
        )
        cleanup_test_entries.append(entry1_id)

        entry2_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "SALES-002",
            today,
            [{"account_code": "4105", "credit_minor": 510000000, "memo": "Ingresos adicionales"}],
        )
        cleanup_test_entries.append(entry2_id)

        snapshot = compute_pulso_snapshot(cliente_cero_tenant_id, today.year, today.month)

        assert snapshot["ventas_periodo"] == 2980000000

    def test_salidas_periodo_sums_expense_debits(self, cliente_cero_tenant_id, cleanup_test_entries):
        """
        Test: Salidas = sum of debit_minor over expense accounts (5xxx, 6xxx) in current month.

        Setup: Insert entries on expense accounts:
          - 5210: debit 1,750,000.00 (175,000,000 cents)
          - 6120: debit 150,000.00 (15,000,000 cents)

        Expected: salidas_periodo = 190,000,000 cents (1,900,000.00 COP)
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry1_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "EXPENSE-001",
            today,
            [{"account_code": "5210", "debit_minor": 175000000, "memo": "Cloud infrastructure"}],
        )
        cleanup_test_entries.append(entry1_id)

        entry2_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "EXPENSE-002",
            today,
            [{"account_code": "6120", "debit_minor": 15000000, "memo": "Rent"}],
        )
        cleanup_test_entries.append(entry2_id)

        snapshot = compute_pulso_snapshot(cliente_cero_tenant_id, today.year, today.month)

        assert snapshot["salidas_periodo"] == 190000000

    def test_empty_ledger_returns_zeroes(self, cliente_cero_tenant_id):
        """
        Test: Empty ledger → all fields zero + status="empty".

        Setup: No entries for the tenant.

        Expected: caja_real=0, ventas_periodo=0, salidas_periodo=0, status="empty"
        """
        from services.financials_service import compute_pulso_snapshot

        today = date.today()
        snapshot = compute_pulso_snapshot(cliente_cero_tenant_id, today.year, today.month)

        assert snapshot["caja_real"] == 0
        assert snapshot["ventas_periodo"] == 0
        assert snapshot["salidas_periodo"] == 0
        assert snapshot["status"] == "empty"

    def test_status_healthy_when_positive(self, cliente_cero_tenant_id, cleanup_test_entries):
        """
        Test: status="healthy" when caja_real > 0.
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry_id = insert_test_entry(
            supabase,
            cliente_cero_tenant_id,
            "POS-001",
            today,
            [{"account_code": "1110", "debit_minor": 1000000, "memo": "Positive cash"}],
        )
        cleanup_test_entries.append(entry_id)

        snapshot = compute_pulso_snapshot(cliente_cero_tenant_id, today.year, today.month)

        assert snapshot["status"] == "healthy"
