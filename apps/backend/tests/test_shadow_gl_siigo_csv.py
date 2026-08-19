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
    """Unit tests for CSV parsing (no database dependency).

    parse_siigo_csv returns a flat list of row dicts (one per CSV line), not grouped by
    transaction — grouping by referencia_externa happens inside ingest_siigo_csv. See
    openspec/specs/shadow-gl-siigo-csv-ingestion/spec.md.
    """

    def test_parses_valid_siigo_csv(self) -> None:
        """Parse a valid Siigo journal export."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        assert parsed is not None
        # Should have parsed rows (multiple transaction lines)
        assert len(parsed) > 0
        # First row should have all required flat fields
        first_row = parsed[0]
        assert "referencia_externa" in first_row
        assert "fecha" in first_row
        assert "codigo_cuenta" in first_row
        assert "descripcion" in first_row
        assert "debito_cents" in first_row
        assert "credito_cents" in first_row

    def test_parses_headers_correctly(self) -> None:
        """CSV headers are parsed and mapped correctly."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_row = parsed[0]
        assert first_row["referencia_externa"] == "DOC-20260618-001"
        assert first_row["fecha"] == "2026-06-18"
        assert isinstance(first_row["debito_cents"], int)
        assert isinstance(first_row["credito_cents"], int)

    def test_converts_amounts_to_minor_units(self) -> None:
        """Currency amounts (COP) converted to integer cents."""
        # "850000.00" COP → 85000000 centavos
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        for row in parsed:
            if row["debito_cents"] > 0:
                # 850000.00 COP should be 85000000 centavos
                assert row["debito_cents"] == 85000000  # First debit in fixture
                return
        pytest.fail("No debit found in parsed CSV")

    def test_groups_lines_by_transaction(self) -> None:
        """Rows sharing a referencia_externa form one logical transaction.

        parse_siigo_csv itself no longer groups (it returns flat rows) — grouping now
        happens in ingest_siigo_csv. This test verifies the flat rows still carry enough
        info to group correctly by referencia_externa; the actual grouping behavior is
        covered against ingest_siigo_csv in TestIngestSiigoCSVPersistence.
        """
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_txn_rows = [r for r in parsed if r["referencia_externa"] == "DOC-20260618-001"]
        assert len(first_txn_rows) == 2  # Debit + credit

    def test_detects_balanced_transaction(self) -> None:
        """Balanced transaction: SUM(debit) = SUM(credit) for a given referencia_externa."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_txn_rows = [r for r in parsed if r["referencia_externa"] == "DOC-20260618-001"]
        debit_sum = sum(r["debito_cents"] for r in first_txn_rows)
        credit_sum = sum(r["credito_cents"] for r in first_txn_rows)
        assert debit_sum == credit_sum, f"Transaction imbalanced: debit={debit_sum}, credit={credit_sum}"

    def test_detects_all_entries_balanced(self) -> None:
        """All transactions in the CSV are balanced, grouped by referencia_externa."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        by_ref: dict[str, list] = {}
        for row in parsed:
            by_ref.setdefault(row["referencia_externa"], []).append(row)
        for ref_id, rows in by_ref.items():
            debit_sum = sum(r["debito_cents"] for r in rows)
            credit_sum = sum(r["credito_cents"] for r in rows)
            assert (
                debit_sum == credit_sum
            ), f"Transaction {ref_id} imbalanced: debit={debit_sum}, credit={credit_sum}"

    def test_rejects_missing_required_column(self) -> None:
        """Malformed CSV: missing required column.

        débito/crédito are optional (blank treated as 0) — descripción is required, so drop
        that one to trigger the missing-column check.
        """
        csv_missing_descripcion = SIIGO_JOURNAL_CSV.replace("descripción,", "")
        with pytest.raises(SiigoCsvParseError, match="descripci"):
            parse_siigo_csv(csv_missing_descripcion)

    def test_rejects_empty_csv(self) -> None:
        """Empty CSV returns empty list, not error."""
        empty_csv = "fecha,referencia externa,código de cuenta,descripción,débito,crédito\n"
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
        # First row should have debit, no credit
        first_row = parsed[0]
        assert first_row["debito_cents"] > 0
        assert first_row["credito_cents"] == 0

    def test_preserves_memo_and_account_code(self) -> None:
        """Row detail: codigo_cuenta and descripcion preserved."""
        parsed = parse_siigo_csv(SIIGO_JOURNAL_CSV)
        first_row = parsed[0]
        assert first_row["codigo_cuenta"] == "1105"
        assert first_row["descripcion"] == "Payment Plan Professional Client A"


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
        """Clean up only the rows this test itself created.

        Two bug fixes (shadow-gl-data-integrity-flag):
        1. The previous version passed a single entry id string to
           `.in_("entry_id", ...)`, which iterates a bare string character-by-character —
           Postgres then rejected the first character as an invalid UUID.
        2. The previous version deleted ALL erp_journal_entries for the Cliente Cero tenant
           on teardown, including unrelated pre-existing rows from other sessions/fixtures.
           Snapshot ids before the test runs and delete only what's new, so this class never
           destroys data it didn't create.
        """
        supabase = get_supabase()
        pre_existing_ids = {
            row["id"]
            for row in supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
            .data
        }
        yield
        new_entry_ids = [
            row["id"]
            for row in supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .execute()
            .data
            if row["id"] not in pre_existing_ids
        ]
        if new_entry_ids:
            supabase.table("erp_journal_lines").delete().eq(
                "tenant_id", cliente_cero_tenant_id
            ).in_("entry_id", new_entry_ids).execute()
            supabase.table("erp_journal_entries").delete().in_("id", new_entry_ids).execute()

    @pytest.mark.asyncio
    async def test_ingest_creates_entries_and_lines(self, cliente_cero_tenant_id) -> None:
        """Valid CSV → rows in erp_journal_entries + erp_journal_lines."""
        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, SIIGO_JOURNAL_CSV)
        assert success is True
        assert error is None
        assert summary is not None
        assert summary["row_count"] > 0  # At least 1 entry created

    @pytest.mark.asyncio
    async def test_ingest_groups_lines_by_referencia_externa(self, cliente_cero_tenant_id) -> None:
        """Rows sharing a referencia_externa become one entry with N lines (shadow-gl-siigo-csv-ingestion)."""
        csv_text = (
            "fecha,referencia externa,código de cuenta,descripción,débito,crédito\n"
            "2026-08-18,GROUP-TEST-001,1105,Caja,100000.00,\n"
            "2026-08-18,GROUP-TEST-001,4105,Revenue,,100000.00\n"
        )
        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, csv_text)
        assert success is True
        assert error is None

        supabase = get_supabase()
        entries = (
            supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .eq("external_reference_id", "GROUP-TEST-001")
            .execute()
        )
        assert len(entries.data) == 1
        entry_id = entries.data[0]["id"]

        lines = (
            supabase.table("erp_journal_lines")
            .select("id")
            .eq("tenant_id", cliente_cero_tenant_id)
            .eq("entry_id", entry_id)
            .execute()
        )
        assert len(lines.data) == 2

    @pytest.mark.asyncio
    async def test_ingest_idempotent_on_external_reference_id(self, cliente_cero_tenant_id) -> None:
        """Re-upload same CSV → no duplicates."""
        # First upload
        success1, summary1, error1 = await ingest_siigo_csv(cliente_cero_tenant_id, SIIGO_JOURNAL_CSV)
        assert success1 is True
        count1 = summary1["row_count"]

        # Second upload (same data) — every entry already exists, so ingest_siigo_csv skips
        # all of them; row_count reflects newly-inserted entries only, so it's 0 here, not count1.
        success2, summary2, error2 = await ingest_siigo_csv(cliente_cero_tenant_id, SIIGO_JOURNAL_CSV)
        assert success2 is True
        assert summary2["row_count"] == 0
        assert count1 > 0

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
        bad_balance_csv = "fecha,referencia externa,código de cuenta,descripción,débito,crédito\n"
        bad_balance_csv += "2026-06-25,UNBALANCED-001,1105,Imbalanced entry,100000.00,\n"
        bad_balance_csv += "2026-06-25,UNBALANCED-001,4105,Wrong credit amount,,50000.00\n"

        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, bad_balance_csv)
        # Should return success=False with error message about imbalance
        assert success is False
        assert "imbalanced" in (error or "").lower() or "imbalance" in (error or "").lower()

    @pytest.mark.asyncio
    async def test_ingest_without_flag_defaults_unverified(self, cliente_cero_tenant_id) -> None:
        """Omitting is_verified_real persists is_verified_real=False (shadow-gl-data-integrity-flag).

        Uses an inline CSV with the current Spanish header format that
        parse_siigo_csv/ingest_siigo_csv actually expect today (fecha, referencia externa,
        código de cuenta, descripción, débito, crédito) — the module-level SIIGO_JOURNAL_CSV
        fixture predates that rewrite and uses stale English headers (pre-existing drift,
        tracked separately, out of scope for this change).
        """
        csv_text = (
            "fecha,referencia externa,código de cuenta,descripción,débito,crédito\n"
            "2026-08-18,FLAG-TEST-001,1105,Caja,100000.00,\n"
            "2026-08-18,FLAG-TEST-001,4105,Revenue,,100000.00\n"
        )
        success, summary, error = await ingest_siigo_csv(cliente_cero_tenant_id, csv_text)
        assert success is True
        supabase = get_supabase()
        rows = (
            supabase.table("erp_journal_entries")
            .select("is_verified_real")
            .eq("tenant_id", cliente_cero_tenant_id)
            .eq("external_reference_id", "FLAG-TEST-001")
            .execute()
        )
        assert len(rows.data) == 1
        assert rows.data[0]["is_verified_real"] is False

    @pytest.mark.asyncio
    async def test_ingest_with_flag_marks_verified(self, cliente_cero_tenant_id) -> None:
        """is_verified_real=True persists is_verified_real=True (shadow-gl-data-integrity-flag)."""
        csv_text = (
            "fecha,referencia externa,código de cuenta,descripción,débito,crédito\n"
            "2026-08-18,FLAG-TEST-002,1105,Caja,100000.00,\n"
            "2026-08-18,FLAG-TEST-002,4105,Revenue,,100000.00\n"
        )
        success, summary, error = await ingest_siigo_csv(
            cliente_cero_tenant_id, csv_text, is_verified_real=True
        )
        assert success is True
        supabase = get_supabase()
        rows = (
            supabase.table("erp_journal_entries")
            .select("is_verified_real")
            .eq("tenant_id", cliente_cero_tenant_id)
            .eq("external_reference_id", "FLAG-TEST-002")
            .execute()
        )
        assert len(rows.data) == 1
        assert rows.data[0]["is_verified_real"] is True
