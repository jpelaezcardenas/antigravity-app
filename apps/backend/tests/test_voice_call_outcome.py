"""Tests for services/voice_call_outcome.py (taty-voice-outbound-calls, Task 4.4/4.5)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.voice_call_outcome import record_call_outcome


class TestRecordCallOutcome:
    def test_rejects_unknown_outcome(self):
        with pytest.raises(ValueError):
            record_call_outcome("lead-1", "NUEVOS", "made_up_outcome")

    def test_qualified_advances_stage_to_prospectos(self):
        mock_crm = MagicMock()
        with patch("services.voice_call_outcome.get_crm_service", return_value=mock_crm):
            record_call_outcome("lead-1", "NUEVOS", "qualified")
        mock_crm.advance_lead.assert_called_once_with("lead-1", "PROSPECTOS", lead_type="qualified")

    def test_not_interested_keeps_current_stage(self):
        mock_crm = MagicMock()
        with patch("services.voice_call_outcome.get_crm_service", return_value=mock_crm):
            record_call_outcome("lead-1", "NUEVOS", "not_interested")
        mock_crm.advance_lead.assert_called_once_with(
            "lead-1", "NUEVOS", lead_type="not_interested"
        )

    def test_callback_requested_keeps_current_stage(self):
        mock_crm = MagicMock()
        with patch("services.voice_call_outcome.get_crm_service", return_value=mock_crm):
            record_call_outcome("lead-1", "NUEVOS", "callback_requested")
        mock_crm.advance_lead.assert_called_once_with(
            "lead-1", "NUEVOS", lead_type="callback_requested"
        )

    def test_voicemail_keeps_current_stage_and_does_not_trigger_a_redial(self):
        """spec.md: 'the outcome is recorded and the lead becomes eligible for the follow-up
        cadence, not an immediate automatic re-dial loop.'"""
        mock_crm = MagicMock()
        with patch("services.voice_call_outcome.get_crm_service", return_value=mock_crm), patch(
            "services.twilio_client.place_call"
        ) as mock_place_call:
            record_call_outcome("lead-1", "NUEVOS", "voicemail")

        mock_crm.advance_lead.assert_called_once_with("lead-1", "NUEVOS", lead_type="voicemail")
        # This module never imports/calls twilio_client at all — asserting it stays untouched
        # proves recording a voicemail outcome cannot, by construction, place another call.
        mock_place_call.assert_not_called()
