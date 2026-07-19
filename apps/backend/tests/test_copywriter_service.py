"""
Credential-free unit tests for copywriter_service.py (sell-machine-creative-swarm, Change E).

Mocks the LLM engine entirely, same pattern as test_content_evaluator.py.
"""

from __future__ import annotations

from unittest.mock import patch

from services.copywriter_service import generate_hooks, rewrite_hook


class TestGenerateHooks:
    def test_returns_the_requested_count_via_llm(self):
        fake_hooks = [
            {"headline": f"Hook {i}", "body": "body", "cta": "cta", "pain_tag": "multa_dian"}
            for i in range(3)
        ]
        with patch("services.copywriter_service._llm_generate_hooks", return_value=fake_hooks):
            result = generate_hooks(count=3)

        assert len(result) == 3
        assert all({"headline", "body", "cta", "pain_tag"} <= set(h.keys()) for h in result)

    def test_falls_back_to_a_deterministic_hook_set_when_llm_fails(self):
        with patch("services.copywriter_service._llm_generate_hooks", side_effect=Exception("all providers failed")):
            result = generate_hooks(count=3)

        assert len(result) > 0
        assert all({"headline", "body", "cta", "pain_tag"} <= set(h.keys()) for h in result)

    def test_deterministic_fallback_never_errors_regardless_of_requested_count(self):
        with patch("services.copywriter_service._llm_generate_hooks", side_effect=Exception("down")):
            result = generate_hooks(count=5)
        assert isinstance(result, list)


class TestRewriteHook:
    def test_returns_a_rewritten_hook_via_llm(self):
        original = {"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}
        rewritten = {"headline": "H2", "body": "B2", "cta": "C2", "pain_tag": "multa_dian"}
        with patch("services.copywriter_service._llm_rewrite_hook", return_value=rewritten):
            result = rewrite_hook(original, reason="robotic tone")

        assert result["headline"] == "H2"

    def test_falls_back_to_the_original_hook_when_llm_fails(self):
        original = {"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}
        with patch("services.copywriter_service._llm_rewrite_hook", side_effect=Exception("down")):
            result = rewrite_hook(original, reason="robotic tone")

        assert result == original
