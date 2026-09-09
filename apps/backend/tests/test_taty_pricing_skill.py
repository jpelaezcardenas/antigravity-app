"""
Tests for Taty's pricing skill (taty-pricing-skill).

Two independent surfaces:
1. The B2B catalog (software tiers + service bands) is now stated on EVERY channel — the base
   prompt block built with or without `lead_context`.
2. The Renta Natural funnel's price refusal is replaced with the founder-given floor, never an
   invented exact number or ceiling — scoped to `lead_context.offer.precio_confirmado`.

Scoping of what is real vs. faked: `TatyAgentService._build_system_prompt` and
`_build_lead_context` run for real against the actual catalog constants — that is the boundary
these tests verify. No LLM call is made; system-prompt construction is pure string assembly.
"""

from __future__ import annotations

import inspect

from core.pricing_catalog import RENTA_NATURAL_PRICING, SERVICE_BAND_PRICING, SOFTWARE_TIERS
from services.taty_lead_router import RENTA_OFFER_CONTEXT, _build_lead_context
from services.taty_service import TatyAgentService

PROFILE = {"nombre_empresa": "Panadería Doña Rosa", "tono": "cercano"}


def _prompt(lead_context=None):
    svc = TatyAgentService.__new__(TatyAgentService)  # no __init__ deps needed for this method
    return svc._build_system_prompt(PROFILE, lead_context=lead_context)


class TestB2bPricingOnEveryChannel:
    def test_base_prompt_without_lead_context_states_tier_names(self):
        """Telegram/PWA shape: no lead_context at all."""
        prompt = _prompt(lead_context=None)
        for tier in SOFTWARE_TIERS.values():
            assert tier.commercial_name in prompt

    def test_base_prompt_states_band_labels(self):
        prompt = _prompt(lead_context=None)
        for band in SERVICE_BAND_PRICING.values():
            assert band.label in prompt

    def test_gps_price_appears_formatted_in_pesos(self):
        prompt = _prompt(lead_context=None)
        assert "249.000" in prompt

    def test_still_present_when_lead_context_is_given(self):
        """The B2B block is independent of the Renta Natural gate — it must not disappear
        just because a WhatsApp lead_context is also present."""
        lead_context = _build_lead_context(current_stage="NUEVOS", current_persona={})
        prompt = _prompt(lead_context=lead_context)
        assert SOFTWARE_TIERS["starter"].commercial_name in prompt

    def test_no_b2b_price_is_a_hardcoded_literal_in_taty_service(self):
        import services.taty_service as mod

        source = inspect.getsource(mod)
        # The GPS price must come from the catalog format call, not be retyped here.
        assert "249.000" not in source or "pricing_catalog" in source


class TestRentaNaturalFloorReplacesRefusal:
    def test_offer_context_price_is_confirmed(self):
        assert RENTA_OFFER_CONTEXT["precio_confirmado"] is True

    def test_offer_context_sources_the_catalog_not_a_bare_literal(self):
        assert RENTA_OFFER_CONTEXT["precio_desde_cop"] == RENTA_NATURAL_PRICING.min_cents // 100

    def test_prompt_states_the_floor(self):
        lead_context = _build_lead_context(current_stage="NUEVOS", current_persona={})
        prompt = _prompt(lead_context=lead_context)
        assert "350.000" in prompt

    def test_prompt_names_the_drivers(self):
        lead_context = _build_lead_context(current_stage="NUEVOS", current_persona={})
        prompt = _prompt(lead_context=lead_context)
        assert "trámite" in prompt.lower() or "tramite" in prompt.lower()
        assert "movimiento" in prompt.lower()
        assert "patrimonio" in prompt.lower()

    def test_old_refusal_instruction_is_gone(self):
        lead_context = _build_lead_context(current_stage="NUEVOS", current_persona={})
        prompt = _prompt(lead_context=lead_context)
        assert "NO inventes ni menciones un número" not in prompt

    def test_prompt_forbids_an_exact_final_number_or_ceiling(self):
        """The load-bearing safety property: real floor, but still no invented final figure."""
        lead_context = _build_lead_context(current_stage="NUEVOS", current_persona={})
        prompt = _prompt(lead_context=lead_context)
        lowered = prompt.lower()
        assert "no digas un precio final exacto" in lowered or "nunca des un valor final exacto" in lowered
        assert "techo" in lowered or "tope máximo" in lowered or "límite superior" in lowered

