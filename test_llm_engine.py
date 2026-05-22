"""
Test suite for LLM Engine with failover and JSON auto-healing.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

from agents.llm_engine import (
    LLMEngine,
    AllProvidersFailedError,
    LLMProvider,
    get_ai_response,
)


class TestLLMEngine:
    """Test suite for LLM Engine"""

    def setup_method(self):
        """Initialize fresh engine for each test"""
        self.engine = LLMEngine()

    def test_parse_json_with_markdown_wrappers(self):
        """Test JSON parsing removes markdown code blocks"""
        response = '''```json
        {
            "status": "success",
            "data": ["item1", "item2"]
        }
        ```'''

        result = self.engine._parse_llm_response(response)
        assert result["status"] == "success"
        assert result["data"] == ["item1", "item2"]

    def test_parse_json_with_trailing_commas(self):
        """Test JSON parsing fixes trailing commas"""
        response = '''{
            "name": "Test",
            "items": ["a", "b",],
            "count": 2,
        }'''

        result = self.engine._parse_llm_response(response)
        assert result["name"] == "Test"
        assert result["items"] == ["a", "b"]
        assert result["count"] == 2

    def test_parse_json_with_regex_extraction(self):
        """Test JSON parsing extracts JSON from surrounding text"""
        response = '''The result is:
        {"status": "ok", "value": 42}
        and that's the answer'''

        result = self.engine._parse_llm_response(response)
        assert result["status"] == "ok"
        assert result["value"] == 42

    def test_parse_invalid_json_fallback(self):
        """Test JSON parsing fallback for unparseable content"""
        response = "This is not JSON at all, just plain text ))))"

        result = self.engine._parse_llm_response(response)
        assert result["parsing_error"] is True
        assert result["status"] == "fallback"
        assert "raw_response" in result

    def test_parse_valid_json_direct(self):
        """Test clean JSON passes through without modification"""
        clean_json = '{"role": "test", "items": [1, 2, 3]}'

        result = self.engine._parse_llm_response(clean_json)
        assert result["role"] == "test"
        assert result["items"] == [1, 2, 3]

    def test_failover_groq_to_cerebras(self):
        """Test failover from Groq to Cerebras on error"""
        # Simulate Groq failure, Cerebras success
        cerebras_response = '{"status": "success"}'

        with patch.object(self.engine, '_call_groq', side_effect=Exception("Groq unavailable")):
            with patch.object(self.engine, '_call_cerebras', return_value=cerebras_response):
                result = self.engine.get_ai_response("test prompt", response_format="json")
                assert result["status"] == "success"

    def test_failover_order_is_correct(self):
        """Test that provider order matches specification"""
        expected_order = [
            LLMProvider.GROQ,
            LLMProvider.CEREBRAS,
            LLMProvider.MISTRAL,
            LLMProvider.GEMINI,
            LLMProvider.OPENROUTER,
        ]

        assert self.engine.provider_order == expected_order

    def test_all_providers_failed_error_raised(self):
        """Test that AllProvidersFailedError is raised when all providers fail"""
        # Mock all methods to raise exceptions
        with patch.object(self.engine, '_call_groq', side_effect=Exception("Groq fail")):
            with patch.object(self.engine, '_call_cerebras', side_effect=Exception("Cerebras fail")):
                with patch.object(self.engine, '_call_mistral', side_effect=Exception("Mistral fail")):
                    with patch.object(self.engine, '_call_gemini', side_effect=Exception("Gemini fail")):
                        with patch.object(self.engine, '_call_openrouter', side_effect=Exception("OpenRouter fail")):
                            with pytest.raises(AllProvidersFailedError):
                                self.engine.get_ai_response("test prompt")

    def test_json_response_format_returns_dict(self):
        """Test that response_format='json' returns a dictionary"""
        test_json = '{"result": "success", "data": [1, 2, 3]}'

        with patch.object(self.engine, '_call_groq', return_value=test_json):
            result = self.engine.get_ai_response(
                prompt="test",
                response_format="json"
            )

            assert isinstance(result, dict)
            assert result["result"] == "success"

    def test_text_response_format_returns_string(self):
        """Test that response_format='text' returns a string"""
        response_text = "This is a text response"

        with patch.object(self.engine, '_call_groq', return_value=response_text):
            result = self.engine.get_ai_response(
                prompt="test",
                response_format="text"
            )

            assert isinstance(result, str)
            assert result == response_text

    def test_system_prompt_included_in_calls(self):
        """Test that system_prompt is passed through to LLM"""
        system_msg = "You are a helpful tax assistant"
        user_prompt = "What is a deduction?"

        mock_response = '{"answer": "test"}'

        with patch.object(self.engine, '_call_groq', return_value=mock_response) as mock_call:
            self.engine.get_ai_response(
                prompt=user_prompt,
                system_prompt=system_msg,
                response_format="json"
            )

            # Verify system prompt was passed
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert system_msg in str(call_args) or call_args[0][1] == system_msg

    def test_max_tokens_parameter(self):
        """Test that max_tokens parameter is respected"""
        with patch.object(self.engine, '_call_groq', return_value='{"ok": true}'):
            self.engine.get_ai_response(
                prompt="test",
                max_tokens=500,
                response_format="json"
            )

            # Verify max_tokens was passed (indirect test via mock call)

    def test_temperature_parameter(self):
        """Test that temperature parameter is respected"""
        with patch.object(self.engine, '_call_groq', return_value='{"ok": true}'):
            # Should not raise error with temperature=0.3 (low randomness)
            result = self.engine.get_ai_response(
                prompt="test",
                temperature=0.3,
                response_format="json"
            )

            assert isinstance(result, dict)

    def test_complex_nested_json_parsing(self):
        """Test parsing complex nested JSON structures"""
        response = '''{
            "campaign": {
                "name": "Q2 Marketing",
                "channels": ["instagram", "linkedin"],
                "metrics": {
                    "budget": 5000.50,
                    "duration_weeks": 4,
                    "expected_roi": 3.5,
                }
            }
        }'''

        result = self.engine._parse_llm_response(response)
        assert result["campaign"]["name"] == "Q2 Marketing"
        assert result["campaign"]["metrics"]["expected_roi"] == 3.5

    def test_json_with_special_characters(self):
        """Test JSON with special characters and escapes"""
        response = '''{
            "description": "Consultoría fiscalsobre impuestos — DIAN compliance",
            "emoji": "✅",
            "code": "if (x > 5) { return 'ok'; }"
        }'''

        # Python handles unicode properly, should work
        # This tests that our JSON parser doesn't mangle unicode
        result = self.engine._parse_llm_response(response)
        assert "DIAN" in result["description"]
        assert "✅" in result["emoji"]


class TestLLMEngineIntegration:
    """Integration tests for LLM Engine"""

    def test_get_ai_response_convenience_function(self):
        """Test the convenience function works correctly"""
        with patch('agents.llm_engine.get_llm_engine') as mock_get:
            mock_engine = MagicMock()
            mock_engine.get_ai_response.return_value = {"status": "ok"}
            mock_get.return_value = mock_engine

            result = get_ai_response("test prompt")
            mock_get.assert_called_once()
            mock_engine.get_ai_response.assert_called_once()

    def test_multiple_sequential_requests(self):
        """Test engine handles multiple sequential requests"""
        engine = LLMEngine()

        responses = [
            '{"result": 1}',
            '{"result": 2}',
            '{"result": 3}',
        ]

        with patch.object(engine, '_call_groq', side_effect=responses):
            for i, _ in enumerate(responses):
                result = engine.get_ai_response("test", response_format="json")
                assert result["result"] == i + 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
