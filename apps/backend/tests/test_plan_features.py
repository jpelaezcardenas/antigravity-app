"""
Unit tests for core/plan_features.py's tier-to-feature map (plan-tier-feature-gating).

Pure logic, no I/O — this module never touches Supabase itself; callers fetch a tenant's
plan_tier separately and pass the string in.
"""

from __future__ import annotations

import pytest

from core.plan_features import has_feature

ALL_FEATURES = ["pulso_diario", "centinela_alerts", "liquidity_bridge"]


class TestFreemiumTier:
    def test_freemium_includes_pulso_diario(self):
        assert has_feature("freemium", "pulso_diario") is True

    def test_freemium_excludes_centinela_alerts(self):
        assert has_feature("freemium", "centinela_alerts") is False

    def test_freemium_excludes_liquidity_bridge(self):
        assert has_feature("freemium", "liquidity_bridge") is False


class TestPaidTiers:
    @pytest.mark.parametrize("tier", ["starter", "growth", "enterprise"])
    @pytest.mark.parametrize("feature", ALL_FEATURES)
    def test_paid_tier_includes_every_feature(self, tier, feature):
        assert has_feature(tier, feature) is True


class TestUnrecognizedTier:
    def test_unrecognized_tier_fails_open(self):
        assert has_feature("some-future-tier-not-yet-in-the-map", "centinela_alerts") is True

    def test_missing_tier_value_fails_open(self):
        assert has_feature(None, "centinela_alerts") is True
        assert has_feature("", "liquidity_bridge") is True
