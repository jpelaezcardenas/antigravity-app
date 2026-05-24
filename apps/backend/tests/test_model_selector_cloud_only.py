"""
Test suite for Cloud-Only model selector configuration.
Validates that all tasks are routed to correct providers (no Ollama local).
"""

import pytest
from core.model_selector import choose_model_for_task, get_task_tier, get_task_description
from agents.llm_engine import LLMProvider


class TestCloudOnlyArchitecture:
    """Verify transition to Cloud-Only (no local Ollama)"""

    def test_no_ollama_in_provider_enum(self):
        """OLLAMA should be removed from LLMProvider enum"""
        assert not hasattr(LLMProvider, 'OLLAMA'), \
            "LLMProvider.OLLAMA should not exist in Cloud-Only architecture"

        # Should have OpenRouter Free instead
        assert hasattr(LLMProvider, 'OPENROUTER_FREE'), \
            "LLMProvider.OPENROUTER_FREE must exist"

    def test_tier1_non_sensitive(self):
        """Tier 1 (non-sensitive) → OpenRouter Free"""
        tier1_tasks = [
            "taty_faq",
            "social_content_gen",
            "data_extraction",
            "general_inquiry"
        ]

        for task in tier1_tasks:
            model = choose_model_for_task(task)
            assert model == LLMProvider.OPENROUTER_FREE, \
                f"{task} should use OpenRouter Free"

            tier = get_task_tier(task)
            assert tier == "tier_1", f"{task} should be Tier 1"

    def test_tier2_financial_cloud_only(self):
        """Tier 2 (financial) → OpenRouter Free (NOT Ollama)"""
        tier2_tasks = [
            "pulso_analysis",
            "centinela_monitoring",
            "transaction_review",
            "cash_flow_analysis"
        ]

        for task in tier2_tasks:
            model = choose_model_for_task(task)
            assert model == LLMProvider.OPENROUTER_FREE, \
                f"{task} should use OpenRouter Free (not Ollama local)"

            tier = get_task_tier(task)
            assert tier == "tier_2", f"{task} should be Tier 2"

    def test_tier3_critical_groq(self):
        """Tier 3 (critical) → Groq (always)"""
        tier3_tasks = [
            "centinela_decision",
            "compliance_audit",
            "fiscal_strategy",
            "taty_fiscal_rag",
        ]

        for task in tier3_tasks:
            model = choose_model_for_task(task)
            assert model == LLMProvider.GROQ, \
                f"{task} should use Groq for critical reliability"

            tier = get_task_tier(task)
            assert tier == "tier_3", f"{task} should be Tier 3"

    def test_task_description_reflects_cloud_only(self):
        """Task descriptions should reflect Cloud-Only architecture"""
        # Tier 2 should mention "Free Cloud" not "Ollama Local"
        tier2_desc = get_task_description("pulso_analysis")

        assert tier2_desc["tier"] == "tier_2", "Should be Tier 2"
        assert tier2_desc["details"]["model"] == "OpenRouter Free", \
            "Tier 2 model should be OpenRouter Free"
        assert "Ollama" not in tier2_desc["details"]["model"], \
            "Should not mention Ollama in Tier 2"

        # Tier 3 should mention Groq
        tier3_desc = get_task_description("centinela_decision")
        assert tier3_desc["details"]["model"] == "Groq", \
            "Tier 3 model should be Groq"

    def test_fallback_chain_order(self):
        """First provider should be OpenRouter Free (fastest, free)"""
        # This tests the actual implementation if needed
        # For now, just verify the model selection is deterministic

        tasks = [
            ("taty_faq", LLMProvider.OPENROUTER_FREE),
            ("pulso_analysis", LLMProvider.OPENROUTER_FREE),
            ("centinela_decision", LLMProvider.GROQ),
            ("taty_fiscal_rag", LLMProvider.GROQ),
        ]

        for task, expected_model in tasks:
            model = choose_model_for_task(task)
            assert model == expected_model, \
                f"Task '{task}' should use {expected_model.value}"

    def test_default_fallback_is_groq(self):
        """Unknown task types should default to Groq (safest)"""
        unknown_task = "some_unknown_task_type"
        model = choose_model_for_task(unknown_task)

        assert model == LLMProvider.GROQ, \
            "Unknown tasks should default to Groq for safety"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
