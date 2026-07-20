"""
Credential-free unit tests for copywriter_service.py (sell-machine-creative-swarm, Change E).

Mocks the LLM engine entirely, same pattern as test_content_evaluator.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.copywriter_service import (
    _build_grounding_query,
    _llm_generate_hooks,
    generate_hooks,
    rewrite_hook,
)


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


class TestGenerateHooksWithTelemetryReport(object):
    """sell-machine-telemetry-loop, Change G: generate_hooks gains an optional `report` param."""

    def test_no_report_behaves_identically_to_before(self):
        fake_hooks = [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]
        with patch(
            "services.copywriter_service._llm_generate_hooks", return_value=fake_hooks
        ) as mock_llm:
            result = generate_hooks(count=1)

        assert result == fake_hooks
        # Called with no report-derived argument beyond count — signature unchanged for this call.
        mock_llm.assert_called_once_with(1, report=None)

    def test_report_is_passed_through_to_the_llm_call_point(self):
        fake_hooks = [{"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}]
        report = {"hook_performance": {"post_content": {"count": 2}}, "funnel_snapshot": {}}
        with patch(
            "services.copywriter_service._llm_generate_hooks", return_value=fake_hooks
        ) as mock_llm:
            result = generate_hooks(count=1, report=report)

        assert result == fake_hooks
        mock_llm.assert_called_once_with(1, report=report)

    def test_falls_back_to_deterministic_set_when_llm_fails_even_with_a_report(self):
        report = {"hook_performance": {}, "funnel_snapshot": {}}
        with patch(
            "services.copywriter_service._llm_generate_hooks", side_effect=Exception("down")
        ):
            result = generate_hooks(count=3, report=report)

        assert len(result) > 0


class TestBuildGroundingQuery:
    def test_no_report_returns_generic_dian_query(self):
        query = _build_grounding_query()
        assert "renta" in query.lower() or "dian" in query.lower()

    def test_report_with_hook_performance_mentions_its_pain_tags(self):
        report = {"hook_performance": {"multa_dian": {"count": 3}}, "funnel_snapshot": {}}
        query = _build_grounding_query(report)
        assert "multa_dian" in query


class TestLlmGenerateHooksGrounding:
    def test_retrieved_chunks_are_included_in_the_prompt(self):
        fake_engine = MagicMock()
        fake_engine.get_ai_response_with_profile.return_value = [
            {"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}
        ]
        with patch(
            "services.copywriter_service.retrieve_similar",
            return_value=[{"source": "dian", "content": "Articulo 592..."}],
        ) as mock_retrieve, patch(
            "agents.llm_engine.get_llm_engine", return_value=fake_engine
        ):
            _llm_generate_hooks(3)

        mock_retrieve.assert_called_once()
        args, kwargs = fake_engine.get_ai_response_with_profile.call_args
        prompt = kwargs.get("prompt") or args[0]
        assert "Articulo 592" in prompt

    def test_empty_retrieval_does_not_block_generation(self):
        fake_engine = MagicMock()
        fake_engine.get_ai_response_with_profile.return_value = [
            {"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}
        ]
        with patch(
            "services.copywriter_service.retrieve_similar", return_value=[]
        ), patch("agents.llm_engine.get_llm_engine", return_value=fake_engine):
            result = _llm_generate_hooks(3)

        assert len(result) == 1

    def test_retrieval_failure_does_not_block_generation(self):
        fake_engine = MagicMock()
        fake_engine.get_ai_response_with_profile.return_value = [
            {"headline": "H", "body": "B", "cta": "C", "pain_tag": "multa_dian"}
        ]
        with patch(
            "services.copywriter_service.retrieve_similar", side_effect=Exception("KB down")
        ), patch("agents.llm_engine.get_llm_engine", return_value=fake_engine):
            result = _llm_generate_hooks(3)

        assert len(result) == 1


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
