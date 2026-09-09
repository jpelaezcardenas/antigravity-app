"""
Tests for the official price catalog (pricing-catalog-and-operator-quote, Stages 1-2).

The load-bearing tests here are the *structural* ones. Prices were previously written down
nowhere in the repo, which let commercial names drift in the frontend and forced Taty's system
prompt to refuse to quote at all. The fix is not "write the numbers somewhere" — it is making it
impossible for the numbers, the plan tiers and the service bands to disagree without a test
failing and naming the offending key.
"""

from __future__ import annotations

import inspect

import pytest

from core import pricing_catalog
from core.plan_features import PLAN_FEATURES
from core.pricing_catalog import (
    SERVICE_BAND_PRICING,
    SOFTWARE_TIERS,
    check_fee_band_coherence,
)
from services.pricing_service import SERVICE_BANDS


class TestCatalogCoversItsKeys:
    def test_covers_exactly_the_plan_tiers(self):
        missing = set(PLAN_FEATURES) - set(SOFTWARE_TIERS)
        extra = set(SOFTWARE_TIERS) - set(PLAN_FEATURES)
        assert not missing, f"tiers priced nowhere: {sorted(missing)}"
        assert not extra, f"catalog prices unknown tiers: {sorted(extra)}"

    def test_covers_exactly_the_service_bands(self):
        missing = set(SERVICE_BANDS) - set(SERVICE_BAND_PRICING)
        extra = set(SERVICE_BAND_PRICING) - set(SERVICE_BANDS)
        assert not missing, f"bands priced nowhere: {sorted(missing)}"
        assert not extra, f"catalog prices unknown bands: {sorted(extra)}"


class TestTierShape:
    def test_every_tier_has_a_commercial_name(self):
        for tier, entry in SOFTWARE_TIERS.items():
            assert entry.commercial_name, f"{tier} has no commercial name"

    def test_every_tier_is_either_fixed_price_or_explicitly_quoted(self):
        """A tier with no price must SAY it is quoted. A silent None reads as free."""
        for tier, entry in SOFTWARE_TIERS.items():
            if entry.price_cents is None:
                assert entry.is_quoted, f"{tier} has no price and is not marked quoted"
            else:
                assert entry.price_cents >= 0
                assert not entry.is_quoted

    def test_freemium_is_actually_zero_not_unpriced(self):
        assert SOFTWARE_TIERS["freemium"].price_cents == 0
        assert SOFTWARE_TIERS["freemium"].is_quoted is False

    def test_records_whether_a_tier_includes_a_licensed_accountant(self):
        """The Entidad A / Entidad B split is the whole reason two revenue lines exist
        (.antigravity/GROUND_TRUTH.md); a tier must say which side it carries."""
        assert SOFTWARE_TIERS["starter"].includes_accountant is False
        assert SOFTWARE_TIERS["growth"].includes_accountant is True
        assert SOFTWARE_TIERS["enterprise"].includes_accountant is True


class TestBandShape:
    def test_a_band_is_either_bounded_or_explicitly_quoted(self):
        """A band with no bounds must SAY it is quoted, so a missing figure is never
        mistaken for a recorded one."""
        for band, entry in SERVICE_BAND_PRICING.items():
            if entry.min_cents is None and entry.max_cents is None:
                assert entry.is_quoted, f"{band} has no bounds and is not marked quoted"
            else:
                assert not entry.is_quoted, f"{band} has bounds but is marked quoted"

    def test_the_quoted_band_has_no_invented_floor(self):
        """The founder published no floor for Complejo. Inventing one (e.g. 'starts where
        Estándar ends') would flag a legitimate complex quote as incoherent."""
        complejo = SERVICE_BAND_PRICING["complejo"]
        assert complejo.min_cents is None
        assert complejo.max_cents is None

    def test_micro_is_a_fixed_price_not_a_range(self):
        """The brief says 'Micro $890.000', a single figure — not a span."""
        micro = SERVICE_BAND_PRICING["micro"]
        assert micro.min_cents == micro.max_cents

    def test_bounded_bands_have_a_maximum_at_or_above_the_minimum(self):
        for band, entry in SERVICE_BAND_PRICING.items():
            if entry.max_cents is not None and entry.min_cents is not None:
                assert entry.max_cents >= entry.min_cents, f"{band} range is inverted"


class TestOfficialAmounts:
    """Pinned to the founder's figures. A silent edit fails here rather than reaching a
    customer as a wrong published price."""

    def test_gps_starter_is_249000(self):
        assert SOFTWARE_TIERS["starter"].price_cents == 249_000_00

    def test_pro_growth_floor_matches_the_estandar_band_floor(self):
        """'Contexia Pro — desde $1.490.000' is the Estándar band's floor, not a separate
        number. Encoding it twice is how the two start disagreeing."""
        assert SOFTWARE_TIERS["growth"].price_cents == SERVICE_BAND_PRICING["estandar"].min_cents

    def test_micro_band_is_890000(self):
        assert SERVICE_BAND_PRICING["micro"].min_cents == 890_000_00

    def test_estandar_band_is_1490000_to_2400000(self):
        assert SERVICE_BAND_PRICING["estandar"].min_cents == 1_490_000_00
        assert SERVICE_BAND_PRICING["estandar"].max_cents == 2_400_000_00

    def test_enterprise_is_quoted_not_free(self):
        assert SOFTWARE_TIERS["enterprise"].is_quoted is True
        assert SOFTWARE_TIERS["enterprise"].price_cents is None


class TestUnitNamingDiscipline:
    def test_no_monetary_identifier_lacks_a_unit_suffix(self):
        """The 100x trap. Every amount in this repo carries its unit in its name; this
        module's neighbour `uvt_values.value_cop` is in whole pesos while these are in
        minor units, so a bare `price` would be genuinely ambiguous."""
        source = inspect.getsource(pricing_catalog)
        for bad in ("price:", "price =", "min:", "max:", "amount:", "amount ="):
            assert bad not in source, f"unit-less monetary identifier {bad!r} in catalog"

    def test_amounts_are_in_minor_units(self):
        """$249.000 stored as 24_900_000 cents, not 249_000 pesos."""
        assert SOFTWARE_TIERS["starter"].price_cents == 24_900_000


class TestFeeBandCoherence:
    def test_fee_inside_the_range_is_fine(self):
        assert check_fee_band_coherence(1_800_000_00, "estandar") is None

    def test_fee_at_either_boundary_is_fine(self):
        assert check_fee_band_coherence(1_490_000_00, "estandar") is None
        assert check_fee_band_coherence(2_400_000_00, "estandar") is None

    def test_fee_below_the_minimum_is_flagged(self):
        warning = check_fee_band_coherence(500_000_00, "estandar")
        assert warning is not None
        # The warning is founder-facing Spanish, so it carries the band's LABEL
        # ("Estándar"), not the internal key ("estandar").
        assert SERVICE_BAND_PRICING["estandar"].label in warning

    def test_fee_above_the_maximum_is_flagged(self):
        warning = check_fee_band_coherence(9_000_000_00, "estandar")
        assert warning is not None

    def test_quoted_band_never_flags_anything(self):
        """Complejo is unbounded on both ends by design — there is no published figure to
        contradict, at any amount."""
        assert check_fee_band_coherence(50_000_000_00, "complejo") is None
        assert check_fee_band_coherence(1_00, "complejo") is None

    def test_micro_flags_any_deviation_from_its_fixed_price(self):
        assert check_fee_band_coherence(890_000_00, "micro") is None
        assert check_fee_band_coherence(950_000_00, "micro") is not None
        assert check_fee_band_coherence(500_000_00, "micro") is not None

    def test_missing_fee_produces_no_warning(self):
        """Nothing to contradict — a client quoted but not yet priced is not an error."""
        assert check_fee_band_coherence(None, "estandar") is None

    def test_missing_band_produces_no_warning(self):
        assert check_fee_band_coherence(1_490_000_00, None) is None

    def test_unknown_band_produces_no_warning_rather_than_raising(self):
        """A roster listing must never blow up on stale data; the CHECK constraint is the
        place that rejects a bad band, not a read path."""
        assert check_fee_band_coherence(1_490_000_00, "inventada") is None

    def test_coherence_is_advisory_and_returns_text_not_an_exception(self):
        """Micro is an exception band and Complejo is quoted, so legitimate off-range fees
        exist by construction. Blocking would force mis-recording the band."""
        result = check_fee_band_coherence(100_00, "micro")
        assert isinstance(result, str)

    def test_warning_formats_amounts_with_colombian_separators(self):
        warning = check_fee_band_coherence(500_000_00, "estandar")
        assert "1.490.000" in warning
