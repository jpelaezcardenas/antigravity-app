"""
Regression test for a real bug found by manually exercising Taty's production prompt
(2026-09-09): "Contexia Pro" is priced at the Estándar band's FLOOR ($1.490.000), stated
publicly as "desde $1.490.000" — but `SoftwareTier` had no field recording that, so
`taty_service.py`'s formatter rendered it as a flat price with no "desde", which is
misleading: a Contexia Pro client whose contadora work lands in Complejo pays more than
$1.490.000/mes, and Taty would have stated the floor as if it were the final number.
"""

from __future__ import annotations

from core.pricing_catalog import SOFTWARE_TIERS


class TestStartsFromMarker:
    def test_growth_tier_is_marked_starts_from(self):
        """Growth's price IS the Estándar band's floor, not a flat fee — the official
        listing says 'desde $1.490.000', so the data must carry that fact."""
        assert SOFTWARE_TIERS["growth"].starts_from is True

    def test_flat_tiers_are_not_marked_starts_from(self):
        for tier_key in ("freemium", "starter"):
            assert SOFTWARE_TIERS[tier_key].starts_from is False

    def test_quoted_tier_is_not_marked_starts_from(self):
        """Quoted and starts-from are different concepts: enterprise has no price at all
        yet, growth has a real floor price."""
        assert SOFTWARE_TIERS["enterprise"].starts_from is False
