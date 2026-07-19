"""
Credential-free unit tests for content_evaluator.py (sell-machine-creative-swarm, Change E).

Mocks the LLM engine entirely (no network, no credentials required). No relation to
agent_critic.py (the deterministic accounting validator) — this is a brand/tone evaluator.
"""

from __future__ import annotations

from unittest.mock import patch

from agents.content_evaluator import evaluate_hook


def _hook(headline="Deja de perder plata por no declarar a tiempo", body="Te ayudamos a evitar sanciones.", cta="Habla con Taty"):
    return {"headline": headline, "body": body, "cta": cta, "pain_tag": "multa_dian"}


class TestHardBanRules:
    def test_rejects_a_hook_claiming_contexia_is_a_regulated_accounting_firm(self):
        hook = _hook(body="Somos una firma contable regulada y firmamos tus estados financieros.")
        result = evaluate_hook(hook)
        assert result["approved"] is False
        assert "regulada" in result["reason"].lower() or "firma" in result["reason"].lower()

    def test_hard_ban_cannot_be_overridden_by_the_llm(self):
        hook = _hook(body="Somos una firma contable regulada.")
        with patch("agents.content_evaluator._llm_tone_check", return_value={"approved": True, "reason": "looks fine"}):
            result = evaluate_hook(hook)
        assert result["approved"] is False


class TestPassThrough:
    def test_a_clean_hook_survives_unchanged_via_llm_check(self):
        hook = _hook()
        with patch("agents.content_evaluator._llm_tone_check", return_value={"approved": True, "reason": "on-brand"}):
            result = evaluate_hook(hook)
        assert result["approved"] is True

    def test_llm_provider_failure_falls_back_to_hard_ban_check_only(self):
        hook = _hook()
        with patch("agents.content_evaluator._llm_tone_check", side_effect=Exception("all providers failed")):
            result = evaluate_hook(hook)
        # No hard-ban violation present -> deterministic fallback approves it
        assert result["approved"] is True

    def test_llm_provider_failure_still_rejects_a_hard_banned_hook(self):
        hook = _hook(body="Firmamos tus estados financieros como firma contable regulada.")
        with patch("agents.content_evaluator._llm_tone_check", side_effect=Exception("all providers failed")):
            result = evaluate_hook(hook)
        assert result["approved"] is False


class TestLlmToneRejection:
    def test_llm_can_reject_a_hook_for_robotic_tone(self):
        hook = _hook(body="Se notifica al usuario que debe proceder con la declaracion tributaria correspondiente.")
        with patch(
            "agents.content_evaluator._llm_tone_check",
            return_value={"approved": False, "reason": "robotic tone, jerga opaca"},
        ):
            result = evaluate_hook(hook)
        assert result["approved"] is False
        assert "reason" in result
