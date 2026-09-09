"""
Regression test: Taty's stated price for a "starts_from" tier must include "desde", so she
never states a floor price as if it were the final one (found by manually running
TatyAgentService._build_system_prompt against production code, 2026-09-09).
"""

from __future__ import annotations

from services.taty_service import TatyAgentService

PROFILE = {"nombre_empresa": "Panadería Doña Rosa", "tono": "cercano"}


def _prompt():
    svc = TatyAgentService.__new__(TatyAgentService)
    return svc._build_system_prompt(PROFILE, lead_context=None)


class TestGrowthTierStatesDesde:
    def test_contexia_pro_price_is_stated_as_a_floor(self):
        prompt = _prompt()
        assert "desde $1.490.000" in prompt

    def test_flat_price_tiers_have_no_desde(self):
        """GPS is a real flat fee — stating it as 'desde' would be equally dishonest in
        the other direction."""
        prompt = _prompt()
        assert "desde $249.000" not in prompt
        assert "$249.000" in prompt
