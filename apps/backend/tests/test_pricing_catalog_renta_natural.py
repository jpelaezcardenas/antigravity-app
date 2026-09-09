"""
Tests for the Renta Natural catalog entry (taty-pricing-skill, Stage 1).

Pinned to the founder's own words: "desde 350.000 pesos... según el caso" — a floor, no
ceiling, varying by named drivers. No number here should ever be invented; this is what makes
Taty's later "desde $350.000" statement honest rather than a fabricated figure.
"""

from __future__ import annotations

from core.pricing_catalog import RENTA_NATURAL_PRICING


class TestRentaNaturalPricing:
    def test_floor_is_350000_pesos(self):
        assert RENTA_NATURAL_PRICING.min_cents == 35_000_000

    def test_has_no_invented_ceiling(self):
        assert RENTA_NATURAL_PRICING.max_cents is None

    def test_is_marked_quoted(self):
        assert RENTA_NATURAL_PRICING.is_quoted is True

    def test_drivers_match_the_founders_words(self):
        drivers = " ".join(RENTA_NATURAL_PRICING.price_drivers).lower()
        assert "tramite" in drivers or "trámite" in drivers
        assert "movimiento" in drivers
        assert "patrimonio" in drivers

    def test_has_a_commercial_label(self):
        assert RENTA_NATURAL_PRICING.label
