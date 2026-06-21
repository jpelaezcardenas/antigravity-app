"""
Unit + integration tests for the LLM Engine.

Unit tests use mock providers (no API calls). The e2e test against Groq is
gated by RUN_E2E_LLM=1 so CI does not spend tokens.

Run from apps/backend:
    pytest tests/test_llm_engine.py -v
    RUN_E2E_LLM=1 pytest tests/test_llm_engine.py::test_e2e_groq -v
"""

from __future__ import annotations

import os
from typing import Iterator
from unittest.mock import patch

import pytest

from agents.llm_engine import (
    AllProvidersFailedError,
    LLMEngine,
    LLMProvider,
    get_ai_response,
)
from agents.anonymizer import Anonymizer
from agents.base_agent import BaseAgent, AgentRole


# ---------------------------------------------------------------------------
# JSON parser layers
# ---------------------------------------------------------------------------

class TestJsonParser:
    def setup_method(self) -> None:
        self.engine = LLMEngine()

    def test_direct_json(self) -> None:
        assert self.engine._parse_llm_response('{"a": 1}') == {"a": 1}

    def test_strips_markdown_fence(self) -> None:
        raw = 'Here is the data:\n```json\n{"x": [1, 2]}\n```'
        assert self.engine._parse_llm_response(raw) == {"x": [1, 2]}

    def test_repairs_trailing_commas(self) -> None:
        raw = '{"items": [1, 2, 3,], "last": "ok",}'
        parsed = self.engine._parse_llm_response(raw)
        assert parsed == {"items": [1, 2, 3], "last": "ok"}

    def test_extracts_json_from_prose(self) -> None:
        raw = 'Sure, here you go: {"name": "Contexia"} ¡Saludos!'
        assert self.engine._parse_llm_response(raw) == {"name": "Contexia"}

    def test_synonym_remapping(self) -> None:
        raw = '{"hallazgos": ["a", "b"]}'
        out = self.engine._parse_llm_response(
            raw, synonyms={"hallazgos": "riesgos"}
        )
        assert out == {"riesgos": ["a", "b"]}

    def test_synonym_does_not_overwrite_existing(self) -> None:
        raw = '{"hallazgos": ["x"], "riesgos": ["already"]}'
        out = self.engine._parse_llm_response(
            raw, synonyms={"hallazgos": "riesgos"}
        )
        assert out["riesgos"] == ["already"]

    def test_coerces_dict_to_list(self) -> None:
        raw = '{"riesgos": {"nivel": "alto"}}'
        out = self.engine._parse_llm_response(raw, list_keys={"riesgos"})
        assert out == {"riesgos": [{"nivel": "alto"}]}

    def test_safe_fallback_on_natural_language(self) -> None:
        raw = "Sorry, I cannot produce JSON for this question."
        out = self.engine._parse_llm_response(raw)
        assert out["parsing_error"] is True
        assert out["status"] == "fallback"
        assert raw in out["raw_response"]


# ---------------------------------------------------------------------------
# Failover loop
# ---------------------------------------------------------------------------

class _FakeProvider:
    """Drop-in replacement for the per-provider _call_* methods."""

    def __init__(self, behavior: str = "ok", value: str = "fake-response") -> None:
        self.behavior = behavior
        self.value = value
        self.calls = 0

    def __call__(self, *args, **kwargs) -> str:
        self.calls += 1
        if self.behavior == "ok":
            return self.value
        if self.behavior == "rate_limit":
            raise TimeoutError("simulated 429")
        if self.behavior == "missing_key":
            raise ValueError("client not initialized")
        raise RuntimeError(f"unknown behavior {self.behavior}")


def _install_providers(engine: LLMEngine, behaviors: dict) -> dict:
    """Patch each _call_<provider> on engine. Returns the fake objects."""
    fakes = {}
    for provider, fake in behaviors.items():
        method_name = f"_call_{provider.value}"
        fakes[provider] = fake
        setattr(engine, method_name, fake)
    return fakes


class TestFailover:
    def test_first_provider_succeeds_no_failover(self) -> None:
        engine = LLMEngine()
        fakes = _install_providers(
            engine,
            {p: _FakeProvider("ok", value=p.value) for p in engine.provider_order},
        )
        result = engine._call_with_failover("hi", "", 10, 0.5, 30)
        assert result == engine.provider_order[0].value
        # Only the first provider was called
        assert fakes[engine.provider_order[0]].calls == 1
        assert fakes[engine.provider_order[1]].calls == 0

    def test_failover_skips_to_next_on_rate_limit(self) -> None:
        engine = LLMEngine()
        order = engine.provider_order
        behaviors = {order[0]: _FakeProvider("rate_limit")}
        behaviors[order[1]] = _FakeProvider("ok", value="second-wins")
        for p in order[2:]:
            behaviors[p] = _FakeProvider("ok", value=p.value)
        fakes = _install_providers(engine, behaviors)

        result = engine._call_with_failover("hi", "", 10, 0.5, 30)
        assert result == "second-wins"
        assert fakes[order[0]].calls == 1
        assert fakes[order[1]].calls == 1

    def test_all_providers_failed_raises(self) -> None:
        engine = LLMEngine()
        _install_providers(
            engine,
            {p: _FakeProvider("rate_limit") for p in engine.provider_order},
        )
        with pytest.raises(AllProvidersFailedError):
            engine._call_with_failover("hi", "", 10, 0.5, 30)


# ---------------------------------------------------------------------------
# JSON retry with re-prompt
# ---------------------------------------------------------------------------

class TestJsonRetry:
    def test_retries_on_missing_required_key(self) -> None:
        engine = LLMEngine()
        calls = {"n": 0}
        responses = [
            '{"summary": "first attempt"}',           # missing "risks"
            '{"summary": "ok", "risks": ["x"]}',       # valid
        ]

        def fake_call(*args, **kwargs) -> str:
            calls["n"] += 1
            return responses[min(calls["n"] - 1, len(responses) - 1)]

        with patch.object(engine, "_call_with_failover", side_effect=fake_call):
            out = engine.get_ai_response(
                prompt="anything",
                response_format="json",
                required_keys={"summary", "risks"},
                max_json_retries=1,
            )

        assert out == {"summary": "ok", "risks": ["x"]}
        assert calls["n"] == 2

    def test_returns_last_attempt_after_retries_exhausted(self) -> None:
        engine = LLMEngine()

        with patch.object(engine, "_call_with_failover", return_value="never json"):
            out = engine.get_ai_response(
                prompt="x",
                response_format="json",
                required_keys={"summary"},
                max_json_retries=1,
            )

        assert out.get("parsing_error") is True


# ---------------------------------------------------------------------------
# Anonymizer integration in BaseAgent
# ---------------------------------------------------------------------------

class _DummyAgent(BaseAgent):
    def execute(self, input_data: dict) -> dict:
        return {}


class TestBaseAgentAnonymization:
    def test_call_llm_masks_pii_before_provider(self) -> None:
        agent = _DummyAgent(role=AgentRole.GENERATOR, name="test-agent")
        captured = {}

        def fake_get_ai_response(prompt: str, **kwargs) -> str:
            captured["prompt"] = prompt
            return f"Procesado para {prompt.split()[-1]}"

        with patch("agents.llm_engine.get_ai_response", side_effect=fake_get_ai_response):
            out = agent.call_llm(
                "Cliente NIT 900.123.456-7 declaró $5.000.000",
                response_format="text",
            )

        assert "900.123.456-7" not in captured["prompt"]
        assert "<NIT_1>" in captured["prompt"]
        assert "<MONEY_1>" in captured["prompt"]
        # Response was rehydrated
        assert "<NIT_1>" not in out

    def test_anonymize_false_passes_prompt_through(self) -> None:
        agent = _DummyAgent(role=AgentRole.GENERATOR, name="test-agent")
        captured = {}

        def fake_get_ai_response(prompt: str, **kwargs) -> str:
            captured["prompt"] = prompt
            return "ok"

        with patch("agents.llm_engine.get_ai_response", side_effect=fake_get_ai_response):
            agent.call_llm("test prompt no PII", anonymize=False)

        assert captured["prompt"] == "test prompt no PII"


# ---------------------------------------------------------------------------
# End-to-end (gated)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    os.environ.get("RUN_E2E_LLM") != "1",
    reason="E2E LLM test disabled (set RUN_E2E_LLM=1 to run)",
)
def test_e2e_groq_real_call() -> None:
    """Smoke test against a real provider. Requires GROQ_API_KEY in env."""
    response = get_ai_response(
        prompt="Reply with the single word PONG and nothing else.",
        system_prompt="You are a test echo. Reply with one word.",
        response_format="text",
        max_tokens=10,
        temperature=0.0,
    )
    assert isinstance(response, str)
    assert "pong" in response.lower()
