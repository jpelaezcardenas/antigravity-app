"""
Unit tests for Agents 4-7 (Editor, Repurposer, Analyst, Distribution).

LLM calls are patched to deterministic stubs — no real API hits.

Run from apps/backend:
    pytest tests/test_agents_4_7.py -v
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.agent_4_editor import EditorAgent
from agents.agent_5_repurposer import RepurposerAgent, CHANNEL_CONSTRAINTS
from agents.agent_6_analyst import AnalystAgent
from agents.agent_7_distribution import DistributionAgent


# ---------------------------------------------------------------------------
# Agent 4: Editor
# ---------------------------------------------------------------------------

class TestEditorAgent:
    def setup_method(self) -> None:
        self.agent = EditorAgent()

    def test_missing_input_returns_non_compliant(self) -> None:
        result = self.agent.execute({})
        assert result["is_compliant"] is False
        assert result["issues"][0]["category"] == "input"

    def test_compliant_review(self) -> None:
        mock_response = {
            "is_compliant": True,
            "polished_content": "Texto pulido con tono Contexia.",
            "issues": [],
            "confidence": 0.92,
        }
        with patch.object(self.agent, "call_llm", return_value=mock_response):
            result = self.agent.execute({
                "draft_content": "Necesitas pagar IVA antes del 15 de junio.",
                "channel": "telegram",
            })
        assert result["is_compliant"] is True
        assert result["polished_content"] == "Texto pulido con tono Contexia."
        assert result["confidence"] == 0.92

    def test_llm_parse_failure_returns_fallback(self) -> None:
        with patch.object(self.agent, "call_llm", return_value={"parsing_error": True}):
            result = self.agent.execute({"draft_content": "borrador"})
        assert result["is_compliant"] is False
        assert any(i["category"] == "fallback" for i in result["issues"])

    def test_log_entry_created(self) -> None:
        mock = {"is_compliant": True, "polished_content": "x", "issues": [], "confidence": 1.0}
        with patch.object(self.agent, "call_llm", return_value=mock):
            self.agent.process({"draft_content": "y"})
        assert len(self.agent.interaction_log) == 1
        assert self.agent.interaction_log[0]["status"] == "success"


# ---------------------------------------------------------------------------
# Agent 5: Repurposer
# ---------------------------------------------------------------------------

class TestRepurposerAgent:
    def setup_method(self) -> None:
        self.agent = RepurposerAgent()

    def test_unknown_channel_skipped(self) -> None:
        with patch.object(self.agent, "call_llm", return_value={"formatted_content": "x"}):
            result = self.agent.execute({
                "source_content": "contenido",
                "target_channels": ["nonexistent"],
            })
        assert "nonexistent" in result["skipped_channels"]
        assert result["variants"] == {}

    def test_multi_channel_formatting(self) -> None:
        def side_effect(*args, **kwargs):
            return {"formatted_content": "Versión adaptada"}

        with patch.object(self.agent, "call_llm", side_effect=side_effect):
            result = self.agent.execute({
                "source_content": "Tu IVA vence el 15 de junio. Programa el pago para evitar intereses moratorios.",
                "target_channels": ["telegram", "dashboard"],
            })
        assert "telegram" in result["variants"]
        assert "dashboard" in result["variants"]
        assert result["skipped_channels"] == []

    def test_sms_respects_hard_char_limit(self) -> None:
        long_content = "x" * 500
        with patch.object(self.agent, "call_llm", return_value={"formatted_content": long_content}):
            result = self.agent.execute({
                "source_content": "fuente",
                "target_channels": ["sms"],
            })
        assert len(result["variants"]["sms"]) <= CHANNEL_CONSTRAINTS["sms"]["max_chars"]

    def test_llm_failure_uses_truncation_fallback(self) -> None:
        with patch.object(self.agent, "call_llm", return_value={"parsing_error": True}):
            result = self.agent.execute({
                "source_content": "a" * 50,
                "target_channels": ["sms"],
            })
        assert "sms" in result["variants"]
        assert len(result["variants"]["sms"]) <= CHANNEL_CONSTRAINTS["sms"]["max_chars"]


# ---------------------------------------------------------------------------
# Agent 6: Analyst
# ---------------------------------------------------------------------------

class TestAnalystAgent:
    def setup_method(self) -> None:
        self.agent = AnalystAgent()

    def test_status_sana_with_no_alerts(self) -> None:
        narrative = {
            "executive_summary": "Todo en orden.",
            "top_risks": [],
            "opportunities": [],
        }
        with patch.object(self.agent, "call_llm", return_value=narrative):
            result = self.agent.execute({
                "company_id": "c1",
                "alerts": [],
                "metrics": {"cash_flow": 1000000},
            })
        assert result["status_level"] == "sana"
        assert result["alert_count"] == 0

    def test_status_critica_with_high_severity(self) -> None:
        alerts = [
            {"severity": "crítica", "title": "IVA vencido", "description": "..."},
            {"severity": "alta", "title": "Retención atrasada", "description": "..."},
            {"severity": "alta", "title": "Régimen mal", "description": "..."},
        ]
        narrative = {"executive_summary": "Urgente.", "top_risks": [], "opportunities": []}
        with patch.object(self.agent, "call_llm", return_value=narrative):
            result = self.agent.execute({
                "company_id": "c1",
                "alerts": alerts,
                "metrics": {},
            })
        # 5 + 3 + 3 = 11 → crítica
        assert result["status_level"] == "crítica"
        assert result["alert_count"] == 3

    def test_missing_fields_returns_empty_report(self) -> None:
        result = self.agent.execute({"company_id": "c1"})
        assert "No se pudo generar reporte" in result["executive_summary"]

    def test_llm_failure_uses_fallback_narrative(self) -> None:
        with patch.object(self.agent, "call_llm", return_value={"parsing_error": True}):
            result = self.agent.execute({
                "company_id": "c1",
                "alerts": [{"severity": "media", "title": "x", "description": "y"}],
                "metrics": {"cash": 100},
            })
        # severity media = 2 → vigilancia (2-4 range)
        assert result["status_level"] == "vigilancia"
        assert "Revisión humana" in result["executive_summary"]


# ---------------------------------------------------------------------------
# Agent 7: Distribution
# ---------------------------------------------------------------------------

class TestDistributionAgent:
    def setup_method(self) -> None:
        self.agent = DistributionAgent()

    def test_missing_input_returns_error(self) -> None:
        result = self.agent.execute({})
        assert "error" in result
        assert result["summary"]["total"] == 0

    def test_dashboard_delivery_returns_payload(self) -> None:
        result = self.agent.execute({
            "company_id": "c1",
            "variants": {"dashboard": "Alerta importante"},
        })
        assert result["summary"]["sent"] == 1
        assert result["deliveries"][0]["channel"] == "dashboard"
        assert result["deliveries"][0]["status"] == "sent"
        assert "payload" in result["deliveries"][0]

    def test_unknown_channel_skipped(self) -> None:
        result = self.agent.execute({
            "company_id": "c1",
            "variants": {"carrier_pigeon": "msg"},
        })
        assert result["summary"]["skipped"] == 1
        assert result["deliveries"][0]["status"] == "skipped"

    def test_unimplemented_channel_reports_stub(self) -> None:
        result = self.agent.execute({
            "company_id": "c1",
            "variants": {"sms": "msg", "email": "msg"},
        })
        assert result["summary"]["skipped"] == 2
        statuses = [d["status"] for d in result["deliveries"]]
        assert all(s == "not_implemented" for s in statuses)

    def test_telegram_dispatch_returns_payload_when_service_missing(self) -> None:
        result = self.agent.execute({
            "company_id": "c1",
            "variants": {"telegram": "Tu IVA vence pronto"},
            "recipients": {"telegram": "@user123"},
        })
        # telegram_service may or may not exist; either way status must be 'sent'
        # because the agent falls back to payload return on ImportError.
        delivery = result["deliveries"][0]
        assert delivery["channel"] == "telegram"
        assert delivery["status"] == "sent"
