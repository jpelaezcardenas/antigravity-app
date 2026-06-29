"""
Test suite for profile-based LLM routing.
Verifies that profiles are correctly recognized and fallback chains work.
"""

import pytest
from unittest.mock import patch, MagicMock
from apps.backend.agents.llm_engine import LLMEngine, PROFILE_CONFIGS, LLMProvider, AllProvidersFailedError


class TestProfileConfigurations:
    """Test that all profiles are properly configured."""

    def test_all_profiles_exist(self):
        """Verify all expected profiles are defined."""
        expected_profiles = {
            "taty-v1",
            "centinela-v1",
            "pulso-v1",
            "radar-v1",
            "auditoria-v1",
            "social-ops-v1",
            "kb-v1",
            "maestro-v1",
        }
        assert set(PROFILE_CONFIGS.keys()) == expected_profiles, "Profile set mismatch"

    def test_each_profile_has_fallback_chain(self):
        """Verify each profile has a fallback chain defined."""
        for profile_name, config in PROFILE_CONFIGS.items():
            assert "fallback_chain" in config, f"Profile {profile_name} missing fallback_chain"
            assert isinstance(config["fallback_chain"], list), f"Profile {profile_name} fallback_chain not a list"
            assert len(config["fallback_chain"]) > 0, f"Profile {profile_name} fallback_chain is empty"


class TestGetAiResponseWithProfile:
    """Test the new get_ai_response_with_profile() method."""

    @pytest.fixture
    def engine(self):
        """Create a LLMEngine instance for testing."""
        return LLMEngine()

    def test_profile_name_none_uses_default(self, engine):
        """Test that profile_name=None falls back to default routing."""
        with patch.object(engine, 'get_ai_response', return_value="test response") as mock_get:
            result = engine.get_ai_response_with_profile(
                prompt="Test",
                profile_name=None,
            )
            mock_get.assert_called_once()
            assert result == "test response"

    def test_unknown_profile_uses_default(self, engine):
        """Test that unknown profile falls back to default routing."""
        with patch.object(engine, 'get_ai_response', return_value="test response") as mock_get:
            result = engine.get_ai_response_with_profile(
                prompt="Test",
                profile_name="nonexistent-profile",
            )
            mock_get.assert_called_once()
            assert result == "test response"

    def test_valid_profile_uses_custom_order(self, engine):
        """Test that valid profile uses custom provider order."""
        with patch.object(engine, '_call_with_failover_custom_order', return_value="test response") as mock_failover:
            result = engine.get_ai_response_with_profile(
                prompt="Test",
                profile_name="taty-v1",
                response_format="text",
            )
            mock_failover.assert_called_once()
            # Verify fallback chain was passed
            call_kwargs = mock_failover.call_args[1]
            assert "provider_order" in call_kwargs
            assert call_kwargs["provider_order"] == PROFILE_CONFIGS["taty-v1"]["fallback_chain"]

    def test_json_format_uses_custom_retry(self, engine):
        """Test that JSON format uses custom retry method."""
        with patch.object(engine, '_get_json_with_retry_custom_order', return_value={"key": "value"}) as mock_retry:
            result = engine.get_ai_response_with_profile(
                prompt="Test",
                profile_name="centinela-v1",
                response_format="json",
            )
            mock_retry.assert_called_once()
            assert result == {"key": "value"}

    def test_all_profiles_have_groq_in_fallback(self, engine):
        """Verify Groq is in fallback chain for all profiles (critical provider)."""
        for profile_name, config in PROFILE_CONFIGS.items():
            fallback = config["fallback_chain"]
            assert LLMProvider.GROQ in fallback, f"Profile {profile_name} missing Groq in fallback chain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
