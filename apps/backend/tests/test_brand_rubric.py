"""
Credential-free unit tests for brand_rubric.py (brand-voice-canonization).

The Claim Ledger is deterministic (no LLM, no network) — it exists specifically so a wrong
peso/UVT figure can never slip past regardless of what an LLM tone check says. See
POST-01-TOPES-RENTA-2026, which shipped $471.000 (10x UVT 2024) instead of $523.740
(10x UVT 2026, core.constants.UVT_2026).
"""

from __future__ import annotations

from agents.brand_rubric import (
    BRAND_RUBRIC_SYSTEM_PROMPT,
    HARD_BAN_PHRASES,
    check_claims,
)
from core.constants import UVT_2026


def _hook(headline="Deja de perder plata por no declarar a tiempo", body="Te ayudamos a evitar sanciones.", cta="Habla con Taty"):
    return {"headline": headline, "body": body, "cta": cta, "pain_tag": "multa_dian"}


class TestHardBanPhrasesExported:
    def test_exports_all_five_known_hard_ban_phrases(self):
        expected = {
            "firma contable regulada",
            "firmamos tus estados financieros",
            "firmamos estados financieros",
            "presentamos tu declaracion de renta",
            "declaramos impuestos en tu nombre",
        }
        assert expected.issubset(set(HARD_BAN_PHRASES))

    def test_system_prompt_is_a_non_empty_string(self):
        assert isinstance(BRAND_RUBRIC_SYSTEM_PROMPT, str)
        assert len(BRAND_RUBRIC_SYSTEM_PROMPT) > 0


class TestClaimLedger:
    def test_accepts_a_hook_with_no_peso_or_uvt_claims(self):
        hook = _hook()
        assert check_claims(hook) is None

    def test_rejects_the_known_wrong_sanction_figure(self):
        hook = _hook(body="La sancion minima por no declarar es de $471.000.")
        reason = check_claims(hook)
        assert reason is not None
        assert "471" in reason

    def test_accepts_the_correctly_sourced_sanction_figure(self):
        correct_sanction = 10 * UVT_2026
        hook = _hook(body=f"La sancion minima por no declarar es de ${correct_sanction:,}.".replace(",", "."))
        assert check_claims(hook) is None

    def test_accepts_the_raw_uvt_2026_value(self):
        formatted = f"{UVT_2026:,}".replace(",", ".")
        hook = _hook(body=f"La UVT vigente en 2026 es de {formatted} UVT.")
        assert check_claims(hook) is None

    def test_rejects_an_arbitrary_unrecognized_peso_figure(self):
        hook = _hook(body="Podrias perder hasta $999.999.999 si no declaras.")
        reason = check_claims(hook)
        assert reason is not None
        assert "999" in reason


class TestClaimLedgerMarketFigures:
    """claim-ledger-market-figures: found live 2026-08-15 — a real Manus research task
    (creative_brief, niche e-commerce segment) produced sourced market figures the Claim Ledger
    rejected as "unsourced" because it only knows fiscal constants. Fixtures below use the exact
    real hook text captured from operator_task ad6d3fcf... (Manus, CCCE-sourced)."""

    def test_accepts_the_real_manus_hook_citing_ecommerce_market_size(self):
        hook = _hook(
            headline="¿Cuánta plata REAL tienes hoy? Tu tienda vende, pero tu caja no se sabe",
            body=(
                "Amigo vendedor: en 2024 el e-commerce colombiano movió $105,4 billones "
                "(+26,7% vs 2023, CCCE) y en el 2T2025 ya fueron $26,9 billones con 140,6 "
                "millones de transacciones (+10,6% anual)."
            ),
            cta="Averigua tu Caja Real de hoy en 5 minutos",
        )
        assert check_claims(hook) is None

    def test_accepts_the_real_manus_hook_citing_average_ticket(self):
        hook = _hook(
            headline="Tu ticket promedio bajó 7,6%: cada peso se ve más y menos plata deja rastro",
            body=(
                "Ojo, que las cifras no mienten: en el 2T2025 se vendió más pero el ticket "
                "promedio cayó a $191.850 (−7,6% anual, CCCE)."
            ),
            cta="Ve el margen real de cada producto, sin excusas",
        )
        assert check_claims(hook) is None

    def test_accepts_a_bare_recognized_source_citation_with_no_percent_or_year(self):
        hook = _hook(body="El comercio electronico colombiano crecio fuerte este año (DANE).")
        assert check_claims(hook) is None

    def test_rejects_a_peso_figure_cited_with_an_unrecognized_source(self):
        hook = _hook(body="Podrias vender hasta $999.999.999 este año (segun mi tio).")
        reason = check_claims(hook)
        assert reason is not None
        assert "999" in reason

    def test_rejects_a_peso_figure_with_no_citation_at_all(self):
        hook = _hook(body="El mercado se movio $500.000.000 el año pasado.")
        reason = check_claims(hook)
        assert reason is not None
        assert "500" in reason

    def test_known_fiscal_constant_still_passes_without_any_citation(self):
        correct_sanction = 10 * UVT_2026
        hook = _hook(
            body=f"La sancion minima por no declarar es de ${correct_sanction:,}.".replace(",", ".")
        )
        assert check_claims(hook) is None
