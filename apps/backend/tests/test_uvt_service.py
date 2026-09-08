"""
Tests for the UVT lookup service (pricing-quote-engine, Stage 2).

The central invariant here is negative: there must be NO UVT amount hardcoded in the
module. The UVT is re-published by DIAN resolution every December, so a constant would be
wrong every 1 January and would silently misclassify every lead arriving after that date
(design.md Decision #2). `test_module_contains_no_hardcoded_uvt_amount` guards that
directly by reading the module source.

The Supabase client is stubbed — that is the datastore *behind* the function, not the
function under test. The lookup logic itself (year selection, missing-year failure, unit
conversion) runs for real.
"""

from __future__ import annotations

import inspect

import pytest

from services import uvt_service
from services.uvt_service import UvtNotFoundError, cop_to_uvt, get_uvt_for_year

# Real published values, cited to their resolutions so a wrong constant is visible in the
# diff rather than buried in a fixture.
UVT_2025_COP = 49_799  # Resolución DIAN 000193 de 2024
UVT_2026_COP = 52_374  # Resolución DIAN 000238 del 15-dic-2025


def _stub_supabase(rows_by_year: dict[int, dict]):
    """Minimal stand-in for the Supabase query chain used by get_uvt_for_year."""

    class _Query:
        def __init__(self):
            self._year = None

        def select(self, *_args, **_kwargs):
            return self

        def eq(self, _column, value):
            self._year = value
            return self

        def maybe_single(self):
            return self

        def execute(self):
            row = rows_by_year.get(self._year)
            return type("Result", (), {"data": row})()

    class _Client:
        def table(self, name):
            assert name == "uvt_values", f"unexpected table {name!r}"
            return _Query()

    return _Client()


SEEDED = {
    2025: {"year": 2025, "value_cop": UVT_2025_COP, "resolution": "Resolución DIAN 000193 de 2024"},
    2026: {
        "year": 2026,
        "value_cop": UVT_2026_COP,
        "resolution": "Resolución DIAN 000238 del 15 de diciembre de 2025",
    },
}


class TestGetUvtForYear:
    def test_returns_the_2025_value_for_tax_year_2025(self):
        uvt = get_uvt_for_year(2025, supabase_client=_stub_supabase(SEEDED))

        assert uvt.year == 2025
        assert uvt.value_cop == UVT_2025_COP
        assert "000193" in uvt.resolution

    def test_returns_the_2026_value_for_tax_year_2026(self):
        uvt = get_uvt_for_year(2026, supabase_client=_stub_supabase(SEEDED))

        assert uvt.year == 2026
        assert uvt.value_cop == UVT_2026_COP

    def test_the_two_live_uvt_values_do_not_interfere(self):
        """2026 runs two UVTs at once for different purposes; selecting one must not
        leak the other (design.md Decision #2)."""
        client = _stub_supabase(SEEDED)

        assert get_uvt_for_year(2025, supabase_client=client).value_cop == UVT_2025_COP
        assert get_uvt_for_year(2026, supabase_client=client).value_cop == UVT_2026_COP

    def test_missing_year_raises_instead_of_falling_back(self):
        """An unseeded year must fail loudly. Substituting an adjacent year's UVT would
        produce a confidently wrong threshold."""
        with pytest.raises(UvtNotFoundError) as exc:
            get_uvt_for_year(2027, supabase_client=_stub_supabase(SEEDED))

        assert "2027" in str(exc.value)

    def test_year_is_a_required_parameter(self):
        """No implicit 'current year' default inside the service — the caller must say
        which tax year it means."""
        signature = inspect.signature(get_uvt_for_year)
        assert signature.parameters["year"].default is inspect.Parameter.empty


class TestNoHardcodedUvt:
    def test_module_contains_no_hardcoded_uvt_amount(self):
        """The whole point of the table. If someone reintroduces a constant, this fails."""
        source = inspect.getsource(uvt_service)

        for forbidden in ("49799", "49_799", "52374", "52_374"):
            assert forbidden not in source, (
                f"{forbidden!r} is hardcoded in uvt_service — the UVT must be read from "
                "the uvt_values table, never embedded in code"
            )


class TestCopToUvt:
    def test_converts_whole_pesos_to_uvt(self):
        # 1.400 UVT at the 2025 value = $69.718.600 (the filing-obligation threshold).
        assert cop_to_uvt(69_718_600, UVT_2025_COP) == pytest.approx(1400.0)

    def test_is_exact_at_one_uvt(self):
        assert cop_to_uvt(UVT_2025_COP, UVT_2025_COP) == pytest.approx(1.0)

    def test_zero_pesos_is_zero_uvt(self):
        assert cop_to_uvt(0, UVT_2025_COP) == 0.0

    def test_rejects_a_non_positive_uvt_value(self):
        """Guards the divide-by-zero a corrupt or unseeded row would cause."""
        with pytest.raises(ValueError):
            cop_to_uvt(1_000_000, 0)

    def test_takes_whole_pesos_not_minor_units(self):
        """Unit-boundary contract (design.md Decision #1): callers convert the Shadow GL's
        minor units to whole COP before calling this. Passing cents by mistake would
        overstate the UVT figure 100x, so this pins the expected magnitude."""
        one_million_pesos_in_uvt = cop_to_uvt(1_000_000, UVT_2025_COP)

        assert 20 < one_million_pesos_in_uvt < 21
