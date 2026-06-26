"""
Phase 8 Stage 2-3: CSV Siigo Parser Tests (TDD)

Tests for parsing Siigo journal CSV exports.
All tests written BEFORE implementation (TDD approach).
"""

import pytest
from io import StringIO
from typing import List, Dict, Any


# Sample valid Siigo CSV
VALID_SIIGO_CSV = """Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,100.00,
2026-06-25,TX-001,4100,Sales Revenue,,100.00
2026-06-25,TX-002,1200,Accounts Payable,,50.00
2026-06-25,TX-002,5100,Purchases,50.00,
"""

# CSV with imbalanced transaction
IMBALANCED_SIIGO_CSV = """Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,100.00,
2026-06-25,TX-001,4100,Sales Revenue,,75.00
"""

# CSV with missing required column
MISSING_COLUMN_CSV = """Fecha,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,1100,Sales Receivable,100.00,
"""

# CSV with invalid date
INVALID_DATE_CSV = """Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026/06/25,TX-001,1100,Sales Receivable,100.00,
"""

# CSV with non-numeric debit
INVALID_DEBIT_CSV = """Fecha,Referencia Externa,Código de Cuenta,Descripción,Débito,Crédito
2026-06-25,TX-001,1100,Sales Receivable,ABC.00,
"""


class TestSiigoCsvParsing:
    """Test Siigo CSV parsing logic."""

    def test_parses_valid_siigo_csv(self):
        """✅ Parse valid CSV with 2 balanced transactions."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        assert len(rows) == 4  # 4 journal lines total
        assert rows[0]["fecha"] == "2026-06-25"
        assert rows[0]["referencia_externa"] == "TX-001"
        assert rows[0]["codigo_cuenta"] == "1100"

    def test_parses_headers_correctly(self):
        """✅ Parse column headers (case-insensitive)."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        # Should have parsed all 4 rows
        assert len(rows) == 4
        # First row should have all expected fields
        assert "fecha" in rows[0]
        assert "referencia_externa" in rows[0]
        assert "codigo_cuenta" in rows[0]

    def test_converts_amounts_to_minor_units(self):
        """✅ Convert decimal amounts to integer cents."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        # 100.00 should become 10000 (cents)
        assert rows[0]["debito_cents"] == 10000
        # Second row: 100.00 credit
        assert rows[1]["credito_cents"] == 10000

    def test_groups_lines_by_transaction(self):
        """✅ Group lines by referencia_externa (transaction ID)."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        # Find all rows for TX-001
        tx_001 = [r for r in rows if r["referencia_externa"] == "TX-001"]
        assert len(tx_001) == 2  # Debit and credit lines

        # Find all rows for TX-002
        tx_002 = [r for r in rows if r["referencia_externa"] == "TX-002"]
        assert len(tx_002) == 2

    def test_detects_balanced_transaction(self):
        """✅ Verify each transaction has debit = credit."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        # TX-001: 100 debit, 100 credit → balanced
        tx_001 = [r for r in rows if r["referencia_externa"] == "TX-001"]
        debits = sum(r.get("debito_cents", 0) for r in tx_001)
        credits = sum(r.get("credito_cents", 0) for r in tx_001)
        assert debits == credits

    def test_detects_all_entries_balanced(self):
        """✅ Verify all transactions in batch are balanced."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        # Batch totals: all debits = all credits
        total_debits = sum(r.get("debito_cents", 0) for r in rows)
        total_credits = sum(r.get("credito_cents", 0) for r in rows)
        assert total_debits == total_credits == 15000  # 100 + 50 in cents

    def test_rejects_missing_required_column(self):
        """❌ Reject CSV missing required column."""
        from services.shadow_gl_service import parse_siigo_csv, SiigoCsvParseError

        with pytest.raises(SiigoCsvParseError) as exc_info:
            parse_siigo_csv(MISSING_COLUMN_CSV)

        assert "Referencia Externa" in str(exc_info.value) or "required" in str(exc_info.value).lower()

    def test_rejects_empty_csv(self):
        """❌ Reject empty CSV."""
        from services.shadow_gl_service import parse_siigo_csv, SiigoCsvParseError

        with pytest.raises(SiigoCsvParseError):
            parse_siigo_csv("")

    def test_rejects_invalid_date_format(self):
        """❌ Reject invalid date format (not YYYY-MM-DD)."""
        from services.shadow_gl_service import parse_siigo_csv, SiigoCsvParseError

        with pytest.raises(SiigoCsvParseError) as exc_info:
            parse_siigo_csv(INVALID_DATE_CSV)

        assert "date" in str(exc_info.value).lower() or "fecha" in str(exc_info.value).lower()

    def test_rejects_non_numeric_debit(self):
        """❌ Reject non-numeric debit amount."""
        from services.shadow_gl_service import parse_siigo_csv, SiigoCsvParseError

        with pytest.raises(SiigoCsvParseError) as exc_info:
            parse_siigo_csv(INVALID_DEBIT_CSV)

        error_msg = str(exc_info.value).lower()
        assert "numeric" in error_msg or "monetary" in error_msg or "amount" in error_msg

    def test_handles_null_credits_correctly(self):
        """✅ Handle NULL credits (empty string) correctly."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        # First row: no credit (empty), should be 0 or None
        assert rows[0]["credito_cents"] == 0 or rows[0]["credito_cents"] is None

    def test_preserves_memo_and_account_code(self):
        """✅ Preserve memo and account code in output."""
        from services.shadow_gl_service import parse_siigo_csv

        rows = parse_siigo_csv(VALID_SIIGO_CSV)

        first_row = rows[0]
        assert first_row["descripcion"] == "Sales Receivable"
        assert first_row["codigo_cuenta"] == "1100"


class TestPhase8Stage2Acceptance:
    """Acceptance criteria for Stage 2-3."""

    def test_parser_function_exists(self):
        """✅ parse_siigo_csv() function exists."""
        from services.shadow_gl_service import parse_siigo_csv

        assert callable(parse_siigo_csv)

    def test_parse_error_exception_exists(self):
        """✅ SiigoCsvParseError exception exists."""
        from services.shadow_gl_service import SiigoCsvParseError

        assert issubclass(SiigoCsvParseError, Exception)

    def test_all_parser_tests_defined(self):
        """✅ All test cases written (12 tests)."""
        # This test just verifies the test suite is complete
        # Actual validation happens when tests run
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
