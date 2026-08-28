"""
Test suite for the LLM engine's free-tier failover cascade.
Cascade: Groq -> OpenRouter free -> Cerebras -> NVIDIA NIM (order reflects what's
actually confirmed working live against production keys — see config.py).
"""

import pytest
from unittest.mock import patch, MagicMock
from apps.backend.agents.llm_engine import LLMEngine, LLMProvider, AllProvidersFailedError


class TestProviderOrder:
    """Verify the default failover order matches the documented cascade."""

    @pytest.fixture
    def engine(self):
        return LLMEngine()

    def test_provider_order_is_free_tier_cascade(self, engine):
        assert engine.provider_order == [
            LLMProvider.GROQ,
            LLMProvider.OPENROUTER_FREE,
            LLMProvider.CEREBRAS,
            LLMProvider.NVIDIA,
        ]

    def test_minimax_and_glm_are_not_providers(self):
        """MiniMax M3 and GLM 5.3 are not paid for by this backend — must not exist as options."""
        provider_names = {p.value for p in LLMProvider}
        assert "minimax" not in provider_names
        assert "glm" not in provider_names


class TestGetAiResponseWithProfile:
    """profile_name is accepted for backward compatibility but no longer changes routing."""

    @pytest.fixture
    def engine(self):
        return LLMEngine()

    def test_profile_name_none_uses_default(self, engine):
        with patch.object(engine, 'get_ai_response', return_value="test response") as mock_get:
            result = engine.get_ai_response_with_profile(
                prompt="Test",
                profile_name=None,
            )
            mock_get.assert_called_once()
            assert result == "test response"

    def test_any_profile_name_routes_to_same_cascade(self, engine):
        with patch.object(engine, '_call_with_failover', return_value="test response") as mock_failover:
            result = engine.get_ai_response_with_profile(
                prompt="Test",
                profile_name="taty-v1",
                response_format="text",
            )
            mock_failover.assert_called_once()
            assert result == "test response"


class TestFailoverCascade:
    """Verify each provider is tried in order and failures fall through."""

    @pytest.fixture
    def engine(self):
        return LLMEngine()

    def test_groq_success_short_circuits_cascade(self, engine):
        with patch.object(engine, '_call_groq', return_value="groq answer") as mock_groq, \
             patch.object(engine, '_call_openrouter_free') as mock_or:
            result = engine._call_with_failover("prompt", "", 100, 0.7, 30)
            mock_groq.assert_called_once()
            mock_or.assert_not_called()
            assert result == "groq answer"

    def test_falls_through_to_openrouter_on_groq_failure(self, engine):
        with patch.object(engine, '_call_groq', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_openrouter_free', return_value="openrouter answer") as mock_or:
            result = engine._call_with_failover("prompt", "", 100, 0.7, 30)
            mock_or.assert_called_once()
            assert result == "openrouter answer"

    def test_falls_through_to_nvidia_as_last_resort(self, engine):
        with patch.object(engine, '_call_groq', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_openrouter_free', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_cerebras', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_nvidia', return_value="nvidia answer") as mock_nvidia:
            result = engine._call_with_failover("prompt", "", 100, 0.7, 30)
            mock_nvidia.assert_called_once()
            assert result == "nvidia answer"

    def test_all_providers_failing_raises(self, engine):
        with patch.object(engine, '_call_groq', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_openrouter_free', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_cerebras', side_effect=ValueError("no key")), \
             patch.object(engine, '_call_nvidia', side_effect=ValueError("no key")):
            with pytest.raises(AllProvidersFailedError):
                engine._call_with_failover("prompt", "", 100, 0.7, 30)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
