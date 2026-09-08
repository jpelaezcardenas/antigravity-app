"""
Migration-file tests for 0048_uvt_values_and_service_band.sql (pricing-quote-engine).

These read the migration FILE rather than a live database, on purpose: the migration is
deliberately not applied yet (applying to Supabase production requires the founder's
explicit approval — tasks.md 11.4b), so a live-schema test would either be skipped into
uselessness or would encourage applying it just to get a green run.

What they protect is what a file test genuinely can: that the seeded UVT figures match the
resolutions they cite, that the constraint the service layer relies on actually exists, and
that the file is idempotent. The live-schema assertions belong in a follow-up run after
the migration is applied.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

MIGRATION = (
    Path(__file__).resolve().parents[1] / "migrations" / "0048_uvt_values_and_service_band.sql"
)


@pytest.fixture(scope="module")
def sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


class TestMigrationFileExists:
    def test_migration_number_does_not_collide(self):
        """0033/0034 collided once when two sessions generated migrations in parallel
        (ARCHITECTURE.md Decisión #15). This asserts 0048 is uniquely claimed."""
        migrations_dir = MIGRATION.parent
        numbered = [p.name for p in migrations_dir.glob("0048_*.sql")]
        assert numbered == [MIGRATION.name], f"0048 is claimed more than once: {numbered}"


class TestUvtValuesTable:
    def test_creates_the_table_idempotently(self, sql):
        assert "CREATE TABLE IF NOT EXISTS public.uvt_values" in sql

    def test_year_is_the_primary_key(self, sql):
        assert re.search(r"year\s+integer\s+PRIMARY KEY", sql)

    def test_value_is_bigint_named_for_whole_pesos(self, sql):
        """`value_cop`, not `value_minor`: the UVT is stored in whole pesos, unlike the
        Shadow GL's *_minor columns (design.md Decision #1)."""
        assert re.search(r"value_cop\s+bigint\s+NOT NULL", sql)
        assert "value_minor" not in sql

    def test_records_the_resolution_that_set_each_value(self, sql):
        assert re.search(r"resolution\s+text\s+NOT NULL", sql)


class TestSeededValues:
    def test_seeds_uvt_2025_with_its_resolution(self, sql):
        assert "(2025, 49799, 'Resolución DIAN 000193 de 2024')" in sql

    def test_seeds_uvt_2026_with_its_resolution(self, sql):
        assert "(2026, 52374, 'Resolución DIAN 000238 del 15 de diciembre de 2025')" in sql

    def test_seed_is_idempotent(self, sql):
        assert "ON CONFLICT (year) DO NOTHING" in sql

    def test_the_two_seeded_years_are_distinct_values(self, sql):
        """Both UVTs are live during 2026 for different purposes; seeding the same number
        twice would silently collapse that distinction."""
        assert "49799" in sql and "52374" in sql


class TestServiceBandColumn:
    def test_adds_the_column_idempotently(self, sql):
        assert "ADD COLUMN IF NOT EXISTS service_band text" in sql

    def test_constrains_the_allowed_bands(self, sql):
        assert "chk_b2b_clients_service_band" in sql
        assert "IN ('micro', 'estandar', 'complejo')" in sql

    def test_allows_null_so_an_unquoted_client_is_not_mislabelled(self, sql):
        assert "service_band IS NULL OR service_band IN" in sql

    def test_has_no_default_band(self, sql):
        """A default would fabricate a band for every historical client whose quote nobody
        recorded — the exact inference this change exists to remove."""
        assert not re.search(r"service_band text\s+.*DEFAULT", sql)

    def test_does_not_recreate_monthly_fee_cents(self, sql):
        """It already exists (migration 0020), verified live 2026-09-08."""
        assert "ADD COLUMN IF NOT EXISTS monthly_fee_cents" not in sql

    def test_constraint_is_added_guarded(self, sql):
        assert "SELECT 1 FROM pg_constraint WHERE conname = 'chk_b2b_clients_service_band'" in sql


class TestRowLevelSecurity:
    def test_enables_rls_on_uvt_values(self, sql):
        assert "ALTER TABLE public.uvt_values ENABLE ROW LEVEL SECURITY" in sql

    def test_reads_are_open_but_writes_are_service_role_only(self, sql):
        """Public legal reference data: readable by everyone, writable only by the backend.
        Deliberately NOT a single permissive `FOR ALL USING (true)` — the shape the
        2026-09-05 masterprompt audit flags on erp_journal_* as no isolation at all."""
        assert "uvt_values_read_all" in sql
        assert "FOR SELECT" in sql
        assert "uvt_values_service_role_write" in sql
        assert "TO service_role" in sql

    def test_does_not_grant_blanket_write_access(self, sql):
        read_policy = sql.split("uvt_values_read_all", 1)[1].split("uvt_values_service_role_write")[0]
        assert "FOR ALL" not in read_policy
