"""
Tests for Taty's intent router (FASE 4, Slice 4, tasks 4.1–4.2).

Routes a classified Telegram message intent to the correct read-only agent
call (Pulso Diario for daily-status intents, Radar Predictivo for
risk-inquiry intents) and formats a reply. No write-capable endpoint is
ever called from this router.

Low-confidence messages (below threshold) trigger a clarifying fallback
reply with no agent call (task 4.2).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.taty_intent_router import classify_intent, route_message


class TestClassifyIntent:
    def test_status_keywords_classified_as_status(self) -> None:
        intent, confidence = classify_intent("¿cómo va todo hoy?")
        assert intent == "status"
        assert confidence >= 0.6

    def test_risk_keywords_classified_as_risk(self) -> None:
        intent, confidence = classify_intent("¿hay algún riesgo fiscal este mes?")
        assert intent == "risk"
        assert confidence >= 0.6


class TestRouteMessage:
    @pytest.mark.asyncio
    async def test_status_intent_routed_to_pulso(self) -> None:
        """A daily-status message calls Pulso Diario's summary, not Radar."""
        fake_summary = {
            "date": "2026-06-21",
            "tenant_id": "tenant-1",
            "dian_total_minor": 119000,
            "discrepancy_count": 0,
        }
        with patch(
            "services.taty_intent_router.get_daily_summary",
            new=AsyncMock(return_value=fake_summary),
        ) as mock_pulso, patch(
            "services.taty_intent_router.calculate_risk_score",
            new=AsyncMock(),
        ) as mock_radar:
            result = await route_message("tenant-1", "¿cómo va todo hoy?")

        mock_pulso.assert_awaited_once_with("tenant-1")
        mock_radar.assert_not_awaited()
        assert result["intent"] == "status"
        assert "119000" in result["reply"] or "1,190" in result["reply"] or "1190" in result["reply"]

    @pytest.mark.asyncio
    async def test_risk_intent_routed_to_radar(self) -> None:
        """A risk-inquiry message calls Radar's risk-score + forecast, not Pulso."""
        with patch(
            "services.taty_intent_router.calculate_risk_score",
            new=AsyncMock(return_value=85),
        ) as mock_radar_score, patch(
            "services.taty_intent_router.calculate_cashflow_forecast",
            new=AsyncMock(return_value=500000),
        ) as mock_radar_forecast, patch(
            "services.taty_intent_router.get_daily_summary",
            new=AsyncMock(),
        ) as mock_pulso:
            result = await route_message("tenant-1", "¿hay algún riesgo fiscal este mes?")

        mock_radar_score.assert_awaited_once_with("tenant-1")
        mock_radar_forecast.assert_awaited_once_with("tenant-1")
        mock_pulso.assert_not_awaited()
        assert result["intent"] == "risk"
        assert "85" in result["reply"]


class TestLowConfidenceFallback:
    @pytest.mark.asyncio
    async def test_unrecognized_intent_returns_clarifying_reply_no_agent_call(self) -> None:
        """A message with unrecognized intent does not call any agent."""
        with patch(
            "services.taty_intent_router.get_daily_summary",
            new=AsyncMock(),
        ) as mock_pulso, patch(
            "services.taty_intent_router.calculate_risk_score",
            new=AsyncMock(),
        ) as mock_radar:
            result = await route_message("tenant-1", "xyz abc 123 random gibberish")

        mock_pulso.assert_not_awaited()
        mock_radar.assert_not_awaited()
        assert result["intent"] == "unknown"
        assert result["confidence"] == 0.0
        assert "aclarar" in result["reply"].lower() or "clarif" in result["reply"].lower()


class TestSensitiveIntentEscalation:
    @pytest.mark.asyncio
    async def test_correction_intent_creates_approval_queue_entry_no_agent_call(self) -> None:
        """A correction request creates a taty_escalation approval_queue entry, no agent call."""
        fake_approval_id = "approval-123"
        with patch(
            "services.taty_intent_router.enqueue_taty_escalation",
            new=AsyncMock(return_value=fake_approval_id),
        ) as mock_enqueue, patch(
            "services.taty_intent_router.get_daily_summary",
            new=AsyncMock(),
        ) as mock_pulso, patch(
            "services.taty_intent_router.calculate_risk_score",
            new=AsyncMock(),
        ) as mock_radar:
            result = await route_message("tenant-1", "arregla la factura 12345")

        mock_enqueue.assert_awaited_once_with("tenant-1", "arregla la factura 12345")
        mock_pulso.assert_not_awaited()
        mock_radar.assert_not_awaited()
        assert result["intent"] == "correction"
        assert "escalad" in result["reply"].lower()
        assert fake_approval_id in result["approval_id"]
