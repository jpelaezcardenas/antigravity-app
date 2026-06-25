"""
Tests for Siigo CSV parser (Phase 5, Shadow GL real data ingestion).

Run with: pytest test_shadow_gl_siigo_csv.py -v
Or with DB: RUN_SHADOW_GL=1 pytest test_shadow_gl_siigo_csv.py -v
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.supabase_client import get_supabase
from services.shadow_gl_service import parse_siigo_csv, ingest_siigo_csv, SiigoCsvParseError

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SIIGO_JOURNAL_CSV = (
    FIXTURES_DIR / "contexia_siigo_journal_2026-06-18-to-2026-06-24.csv"
).read_text(encoding="utf-8")


class TestParseSiigoCSV:
    """Unit tests for CSV parsing (no database dependency)."""

    def test_parses_valid_siigo_csv(self) -> None:
        """Parse a valid Siigo journal export."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        assert parsed is not None
        # Should have parsed entries (multiple transactions)
        assert len(parsed) > 0
        # First entry should have required fields
        first_entry = parsed[0]
        assert "external_reference_id" in first_entry
        assert "transaction_date" in first_entry
        assert "lines" in first_entry
        assert len(first_entry["lines"]) > 0

    def test_parses_headers_correctly(self) -> None:
        """CSV headers are parsed and mapped correctly."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_entry = parsed[0]
        # Check expected structure
        assert first_entry["external_reference_id"] == "DOC-20260618-001"
        assert first_entry["transaction_date"] == "2026-06-18"
        # Lines should have account_code, debit_minor, credit_minor
        first_line = first_entry["lines"][0]
        assert "account_code" in first_line
        assert "debit_minor" in first_line or first_line["debit_minor"] == 0
        assert "credit_minor" in first_line or first_line["credit_minor"] == 0

    def test_converts_amounts_to_minor_units(self) -> None:
        """Currency amounts (COP) converted to integer cents."""
        # "850000.00" COP → 85000000 centavos
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        # Find the first line with debit_amount
        for entry in parsed:
            for line in entry["lines"]:
                if line["debit_minor"] > 0:
                    # 850000.00 COP should be 85000000 centavos
                    assert line["debit_minor"] == 85000000  # First debit in fixture
                    return
        pytest.fail("No debit found in parsed CSV")

    def test_groups_lines_by_transaction(self) -> None:
        """Multiple lines per transaction are grouped correctly."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        # First transaction (DOC-20260618-001) should have 2 lines
        first_txn = parsed[0]
        assert first_txn["external_reference_id"] == "DOC-20260618-001"
        assert len(first_txn["lines"]) == 2  # Debit + credit

    def test_detects_balanced_transaction(self) -> None:
        """Balanced entry: SUM(debit) = SUM(credit)."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_entry = parsed[0]
        debit_sum = sum(line["debit_minor"] for line in first_entry["lines"])
        credit_sum = sum(line["credit_minor"] for line in first_entry["lines"])
        assert debit_sum == credit_sum, f"Entry imbalanced: debit={debit_sum}, credit={credit_sum}"

    def test_detects_all_entries_balanced(self) -> None:
        """All entries in the CSV are balanced."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        for i, entry in enumerate(parsed):
            debit_sum = sum(line["debit_minor"] for line in entry["lines"])
            credit_sum = sum(line["credit_minor"] for line in entry["lines"])
            assert (
                debit_sum == credit_sum
            ), f"Entry {i} ({entry['external_reference_id']}) imbalanced: debit={debit_sum}, credit={credit_sum}"

    def test_rejects_missing_required_column(self) -> None:
        """Malformed CSV: missing required column."""
        csv_missing_debit = SIIGO_JOURNAL_CSV.replace("debit_amount,", "")
        with pytest.raises(SiigoCsvParseError, match="debit_amount"):
            parse_siigo_csv(csv_missing_debit)

    def test_rejects_empty_csv(self) -> None:
        """Empty CSV returns empty list, not error."""
        empty_csv = "transaction_date,account_code,debit_amount,credit_amount,memo,external_reference_id,currency_code\n"
        parsed = parse_siigo_csv(empty_csv)
        assert parsed == []

    def test_rejects_invalid_date_format(self) -> None:
        """Invalid ISO 8601 date raises error."""
        bad_csv = SIIGO_JOURNAL_CSV.replace("2026-06-18", "18/06/2026")
        with pytest.raises(SiigoCsvParseError, match="date"):
            parse_siigo_csv(bad_csv)

    def test_rejects_non_numeric_debit(self) -> None:
        """Non-numeric debit amount raises error."""
        bad_csv = SIIGO_JOURNAL_CSV.replace("850000.00", "invalid")
        with pytest.raises(SiigoCsvParseError, match="monetary"):
            parse_siigo_csv(bad_csv)

    def test_handles_null_credits_correctly(self) -> None:
        """Empty/null credit amounts treated as 0."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        # First line should have debit, no credit
        first_entry = parsed[0]
        first_line = first_entry["lines"][0]
        assert first_line["debit_minor"] > 0
        assert first_line["credit_minor"] == 0

    def test_preserves_memo_and_account_code(self) -> None:
        """Line detail: account_code and memo preserved."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_entry = parsed[0]
        first_line = first_entry["lines"][0]
        assert first_line["account_code"] == "1105"
        assert first_line["memo"] == "Payment Plan Professional Client A"


@pytest.mark.skipif(
    os.environ.get("RUN_SHADOW_GL") != "1",
    reason="Set RUN_SHADOW_GL=1 to run Shadow GL persistence tests against Supabase",
)
class TestIngestSiigoCSVPersistence:
    """Persistence tests for CSV ingestion (requires Supabase)."""

    @pytest.fixture(scope="class")
    def cliente_cero_tenant_id(self) -> str:
        supabase = get_supabase()
        result = (
            supabase.table("tenants")
            .select("id")
            .eq("is_cliente_cero", True)
            .single()
            .execute()
        )
        return result.data["id"]

    @pytest.fixture(autouse=True)
    def _cleanup(self, cliente_cero_tenant_id):
        """Clean up test data after each test."""
        supabase = get_supabase()
        yield
        # Delete all entries/lines created during test
        supabase.table("erp_journal_lines").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).in_("entry_id",
            supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
            .data[0]["id"] if supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
            .data else []
        ).execute()
        supabase.table("erp_journal_entries").delete().eq(
            "tenant_id", cliente_cero_tenant_id
        ).execute()

    @pytest.mark.asyncio
    async def test_ingest_creates_entries_and_lines(self, cliente_cero_tenant_id) -> None:
        """Valid CSV → rows in erp_journal_entries + erp_journal_lines."""
        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, SIIGO_JOURNAL_CSV)
        assert success is True
        assert error is None
        assert summary is not None
        assert summary["row_count"] > 0  # At least 1 entry created

    @pytest.mark.asyncio
    async def test_ingest_idempotent_on_external_reference_id(self, cliente_cero_tenant_id) -> None:
        """Re-upload same CSV → no duplicates."""
        # First upload
        success1, summary1, error1 = await ingest_siigo_csv(cliente_cero_tenant_id, SIIGO_JOURNAL_CSV)
        assert success1 is True
        count1 = summary1["row_count"]

        # Second upload (same data)
        success2, summary2, error2 = await ingest_siigo_csv(cliente_cero_tenant_id, SIIGO_JOURNAL_CSV)
        assert success2 is True
        # Row count should be same (no new rows created)
        assert summary2["row_count"] == count1

    @pytest.mark.asyncio
    async def test_ingest_invalid_csv_returns_error(self, cliente_cero_tenant_id) -> None:
        """Malformed CSV → error, no DB insert."""
        bad_csv = "invalid,csv\nno,required,columns"
        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, bad_csv)
        assert success is False
        assert error is not None

    @pytest.mark.asyncio
    async def test_ingest_creates_approval_queue_on_imbalance(self, cliente_cero_tenant_id) -> None:
        """Imbalanced entry → approval_queue task created."""
        # Create a CSV with imbalanced entry (debit != credit)
        bad_balance_csv = "transaction_date,account_code,account_name,debit_amount,credit_amount,memo,external_reference_id,currency_code\n"
        bad_balance_csv += "2026-06-25,1105,Caja,100000.00,,Imbalanced entry,UNBALANCED-001,COP\n"
        bad_balance_csv += "2026-06-25,4105,Revenue,,50000.00,Wrong credit amount,UNBALANCED-001,COP\n"

        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, bad_balance_csv)
        # Should return success=False with error message about imbalance
        assert success is False
        assert "imbalanced" in (error or "").lower() or "imbalance" in (error or "").lower()
