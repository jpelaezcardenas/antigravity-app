"""
Test suite for Pulso financials aggregation from Shadow GL.

Tests the aggregation service that computes Caja Real, ventas_periodo, and salidas_periodo
from erp_journal_lines for a tenant.

These tests use a hermetic, throwaway tenant per test (see `test_tenant_id` fixture)
rather than the real Cliente Cero tenant. Cliente Cero already has real ingested
production-like data (Siigo CSV / DIAN XML from prior MVP slices); running assertions
against it made earlier versions of this suite non-hermetic — they only "passed"
because their hardcoded expected totals happened to match whatever was already in the
real ledger at the time, and broke (or silently double-counted) as soon as real data or
multiple test runs accumulated. `compute_pulso_snapshot` / `compute_pulso_daily_snapshot`
are tenant-agnostic, so testing them against an isolated tenant is both correct and
trivial.
"""

import uuid

import pytest
from datetime import datetime, date, timedelta

from core.supabase_client import get_supabase


@pytest.fixture
def test_tenant_id():
    """
    Hermetic, throwaway tenant for aggregation tests.

    Using a dedicated tenant (instead of the real Cliente Cero tenant) keeps these
    tests isolated from real production-like ledger data, so expected totals are
    exact rather than "whatever happened to be in the DB at test time."
    """
    supabase = get_supabase()
    nit = f"TEST-{uuid.uuid4().hex[:12]}"
    inserted = (
        supabase.table("tenants")
        .insert(
            {
                "nit": nit,
                "legal_name": "Hermetic Test Tenant (pytest, safe to delete)",
                "is_cliente_cero": False,
            }
        )
        .execute()
    )
    tenant_id = inserted.data[0]["id"]

    yield tenant_id

    # Defensive cleanup: erp_journal_entries/lines.tenant_id -> tenants.id has
    # ON DELETE NO ACTION, so any leftover rows must be removed before the tenant
    # itself, regardless of whether `cleanup_test_entries` already ran.
    supabase.table("erp_journal_lines").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("erp_journal_entries").delete().eq("tenant_id", tenant_id).execute()
    supabase.table("tenants").delete().eq("id", tenant_id).execute()


@pytest.fixture
def cleanup_test_entries():
    """Fixture: cleanup test journal entries (by entry id) after each test."""
    created_ids = []
    yield created_ids

    supabase = get_supabase()
    for entry_id in created_ids:
        supabase.table("erp_journal_lines").delete().eq("entry_id", entry_id).execute()
        supabase.table("erp_journal_entries").delete().eq("id", entry_id).execute()


def insert_test_entry(supabase, tenant_id, ref_id: str, entry_date: date, lines: list):
    """
    Helper: insert a test journal entry with lines.

    `erp_journal_lines` has an AFTER INSERT/UPDATE/DELETE trigger
    (`erp_journal_lines_balanced` -> `assert_entry_balanced()`) that rejects any
    entry where sum(debit_minor) != sum(credit_minor) across its lines. Callers
    MUST pass already-balanced lines (e.g. a real account line plus a contra line
    on a neutral account such as 1205/Cuentas por Cobrar or 2105/Cuentas por
    Pagar) — this helper does not balance on the caller's behalf.
    """
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
    """Test suite for compute_pulso_snapshot (monthly aggregation)."""

    def test_caja_real_equals_bank_account_balance(self, test_tenant_id, cleanup_test_entries):
        """
        Test: Caja Real = balance of account 1110 (Bancos) = sum(debit_minor) - sum(credit_minor).

        Each entry is balanced against account 1205 (Cuentas por Cobrar), a neutral
        contra-account not counted by any classification rule.

        Expected: caja_real = 352,000,000 cents (3,520,000.00 COP)
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry1_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "BANK-001",
            today,
            [
                {"account_code": "1110", "debit_minor": 1125000000, "memo": "Bancos debit"},
                {"account_code": "1205", "credit_minor": 1125000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry1_id)

        entry2_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "BANK-002",
            today,
            [
                {"account_code": "1110", "credit_minor": 773000000, "memo": "Bancos credit"},
                {"account_code": "1205", "debit_minor": 773000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry2_id)

        snapshot = compute_pulso_snapshot(test_tenant_id, today.year, today.month)

        assert snapshot["caja_real"] == 352000000, f"Expected 352000000, got {snapshot['caja_real']}"

    def test_caja_real_includes_prior_period_balance(self, test_tenant_id, cleanup_test_entries):
        """
        Test: Caja Real is the CUMULATIVE balance of account 1110 up to the period
        being queried — not just the net movement within that single month.

        A real bank balance carries over from prior months; computing it from a
        single month's lines alone would understate (or misreport) "today's" cash.

        Setup: one entry dated in a PRIOR month, one entry dated today.
        Expected: caja_real for the CURRENT month query includes both.
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()
        first_of_this_month = today.replace(day=1)
        prior_month_date = first_of_this_month - timedelta(days=1)  # last day of prior month

        prior_entry_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "CARRYOVER-001",
            prior_month_date,
            [
                {"account_code": "1110", "debit_minor": 500000000, "memo": "Prior month balance"},
                {"account_code": "1205", "credit_minor": 500000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(prior_entry_id)

        current_entry_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "CARRYOVER-002",
            today,
            [
                {"account_code": "1110", "debit_minor": 100000000, "memo": "This month movement"},
                {"account_code": "1205", "credit_minor": 100000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(current_entry_id)

        snapshot = compute_pulso_snapshot(test_tenant_id, today.year, today.month)

        assert snapshot["caja_real"] == 600000000, (
            f"Expected cumulative balance 600000000 (prior + current), got {snapshot['caja_real']}"
        )

    def test_ventas_periodo_sums_income_credits(self, test_tenant_id, cleanup_test_entries):
        """
        Test: Ventas = sum of credit_minor over income accounts (4100, 4105) in current month.

        Expected: ventas_periodo = 2,980,000,000 cents (29,800,000.00 COP)
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry1_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "SALES-001",
            today,
            [
                {"account_code": "4100", "credit_minor": 2470000000, "memo": "Ingresos software"},
                {"account_code": "1205", "debit_minor": 2470000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry1_id)

        entry2_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "SALES-002",
            today,
            [
                {"account_code": "4105", "credit_minor": 510000000, "memo": "Ingresos adicionales"},
                {"account_code": "1205", "debit_minor": 510000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry2_id)

        snapshot = compute_pulso_snapshot(test_tenant_id, today.year, today.month)

        assert snapshot["ventas_periodo"] == 2980000000

    def test_salidas_periodo_sums_expense_debits(self, test_tenant_id, cleanup_test_entries):
        """
        Test: Salidas = sum of debit_minor over expense accounts (5xxx, 6xxx) in current month.

        Expected: salidas_periodo = 190,000,000 cents (1,900,000.00 COP)
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry1_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "EXPENSE-001",
            today,
            [
                {"account_code": "5210", "debit_minor": 175000000, "memo": "Cloud infrastructure"},
                {"account_code": "2105", "credit_minor": 175000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry1_id)

        entry2_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "EXPENSE-002",
            today,
            [
                {"account_code": "6120", "debit_minor": 15000000, "memo": "Rent"},
                {"account_code": "2105", "credit_minor": 15000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry2_id)

        snapshot = compute_pulso_snapshot(test_tenant_id, today.year, today.month)

        assert snapshot["salidas_periodo"] == 190000000

    def test_empty_ledger_returns_zeroes(self, test_tenant_id):
        """
        Test: Empty ledger → all fields zero + status="empty".
        """
        from services.financials_service import compute_pulso_snapshot

        today = date.today()
        snapshot = compute_pulso_snapshot(test_tenant_id, today.year, today.month)

        assert snapshot["caja_real"] == 0
        assert snapshot["ventas_periodo"] == 0
        assert snapshot["salidas_periodo"] == 0
        assert snapshot["status"] == "empty"

    def test_status_healthy_when_positive(self, test_tenant_id, cleanup_test_entries):
        """
        Test: status="healthy" when caja_real > 0.
        """
        from services.financials_service import compute_pulso_snapshot

        supabase = get_supabase()
        today = date.today()

        entry_id = insert_test_entry(
            supabase,
            test_tenant_id,
            "POS-001",
            today,
            [
                {"account_code": "1110", "debit_minor": 1000000, "memo": "Positive cash"},
                {"account_code": "1205", "credit_minor": 1000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_id)

        snapshot = compute_pulso_snapshot(test_tenant_id, today.year, today.month)

        assert snapshot["status"] == "healthy"


class TestPulsoDailySnapshot:
    """
    Test suite for compute_pulso_daily_snapshot — the "Pulso diario" promise:
    Caja Real as of today, Ventas/Gastos specifically for YESTERDAY (not the
    whole month). This backs the real CashTodayCard component
    (lib/types/contexia.ts: CashToday { total, yours, yesterdaySales, expenses }).
    """

    def test_caja_real_is_cumulative_balance_as_of_date(self, test_tenant_id, cleanup_test_entries):
        """
        Caja Real (as_of=today) must include account 1110 movements from any
        prior date, not just "yesterday" or "today" — it's a running balance.
        """
        from services.financials_service import compute_pulso_daily_snapshot

        supabase = get_supabase()
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        e1 = insert_test_entry(
            supabase, test_tenant_id, "DAILY-CASH-001", two_days_ago,
            [
                {"account_code": "1110", "debit_minor": 300000000, "memo": "older"},
                {"account_code": "1205", "credit_minor": 300000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(e1)

        e2 = insert_test_entry(
            supabase, test_tenant_id, "DAILY-CASH-002", yesterday,
            [
                {"account_code": "1110", "debit_minor": 100000000, "memo": "yesterday"},
                {"account_code": "1205", "credit_minor": 100000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(e2)

        e3 = insert_test_entry(
            supabase, test_tenant_id, "DAILY-CASH-003", today,
            [
                {"account_code": "1110", "debit_minor": 50000000, "memo": "today"},
                {"account_code": "1205", "credit_minor": 50000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(e3)

        snapshot = compute_pulso_daily_snapshot(test_tenant_id, today)

        assert snapshot["caja_real"] == 450000000, (
            f"Expected cumulative balance 450000000, got {snapshot['caja_real']}"
        )

    def test_ventas_ayer_sums_only_yesterdays_income_credits(self, test_tenant_id, cleanup_test_entries):
        """
        ventas_ayer must sum ONLY income credits (4100/4105) dated exactly
        yesterday — entries from today or earlier days must not be counted.
        """
        from services.financials_service import compute_pulso_daily_snapshot

        supabase = get_supabase()
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)

        counted = insert_test_entry(
            supabase, test_tenant_id, "DAILY-SALES-001", yesterday,
            [
                {"account_code": "4100", "credit_minor": 80000000, "memo": "yesterday sale"},
                {"account_code": "1205", "debit_minor": 80000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(counted)

        not_counted_today = insert_test_entry(
            supabase, test_tenant_id, "DAILY-SALES-002", today,
            [
                {"account_code": "4105", "credit_minor": 99000000, "memo": "today sale, must not count"},
                {"account_code": "1205", "debit_minor": 99000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(not_counted_today)

        not_counted_older = insert_test_entry(
            supabase, test_tenant_id, "DAILY-SALES-003", two_days_ago,
            [
                {"account_code": "4100", "credit_minor": 77000000, "memo": "older sale, must not count"},
                {"account_code": "1205", "debit_minor": 77000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(not_counted_older)

        snapshot = compute_pulso_daily_snapshot(test_tenant_id, today)

        assert snapshot["ventas_ayer"] == 80000000, (
            f"Expected only yesterday's sales (80000000), got {snapshot['ventas_ayer']}"
        )

    def test_gastos_ayer_sums_only_yesterdays_expense_debits(self, test_tenant_id, cleanup_test_entries):
        """
        gastos_ayer must sum ONLY expense debits (5xxx/6xxx) dated exactly
        yesterday.
        """
        from services.financials_service import compute_pulso_daily_snapshot

        supabase = get_supabase()
        today = date.today()
        yesterday = today - timedelta(days=1)

        counted = insert_test_entry(
            supabase, test_tenant_id, "DAILY-EXP-001", yesterday,
            [
                {"account_code": "5210", "debit_minor": 12000000, "memo": "yesterday expense"},
                {"account_code": "2105", "credit_minor": 12000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(counted)

        not_counted_today = insert_test_entry(
            supabase, test_tenant_id, "DAILY-EXP-002", today,
            [
                {"account_code": "6120", "debit_minor": 9000000, "memo": "today expense, must not count"},
                {"account_code": "2105", "credit_minor": 9000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(not_counted_today)

        snapshot = compute_pulso_daily_snapshot(test_tenant_id, today)

        assert snapshot["gastos_ayer"] == 12000000, (
            f"Expected only yesterday's expenses (12000000), got {snapshot['gastos_ayer']}"
        )

    def test_daily_snapshot_empty_ledger_returns_zeroes(self, test_tenant_id):
        """Empty ledger → all fields zero + status='empty'."""
        from services.financials_service import compute_pulso_daily_snapshot

        today = date.today()
        snapshot = compute_pulso_daily_snapshot(test_tenant_id, today)

        assert snapshot["caja_real"] == 0
        assert snapshot["ventas_ayer"] == 0
        assert snapshot["gastos_ayer"] == 0
        assert snapshot["status"] == "empty"

    def test_daily_snapshot_status_healthy_when_positive(self, test_tenant_id, cleanup_test_entries):
        """status='healthy' when caja_real > 0."""
        from services.financials_service import compute_pulso_daily_snapshot

        supabase = get_supabase()
        today = date.today()

        entry_id = insert_test_entry(
            supabase, test_tenant_id, "DAILY-POS-001", today,
            [
                {"account_code": "1110", "debit_minor": 1000000, "memo": "Positive cash"},
                {"account_code": "1205", "credit_minor": 1000000, "memo": "contra"},
            ],
        )
        cleanup_test_entries.append(entry_id)

        snapshot = compute_pulso_daily_snapshot(test_tenant_id, today)

        assert snapshot["status"] == "healthy"
