"""taty-followup-cadence: 'a lead who responds exits the automated cadence' (spec.md).

route_lead_message is the single per-inbound-message entry point every real WhatsApp message
passes through (presentation/whatsapp_endpoints.py::taty_lead_reply calls it directly), so this is
where the cadence reset must happen — not a duplicate resolution in whatsapp_intake.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.taty_lead_router import _record_inbound_and_reset_cadence, route_lead_message


class TestRouteLeadMessageResetsCadence:
    def _mock_crm_service(self):
        mock_service = MagicMock()
        mock_service.get_tax_profile.return_value = {}
        mock_service.update_tax_profile.return_value = {"lead_id": "lead-1"}
        return mock_service

    def test_any_inbound_message_resets_cadence(self):
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="NUEVOS"
        ), patch(
            "services.taty_lead_router.resolve_cliente_cero_tenant_id", return_value=None
        ), patch(
            "services.taty_lead_router._record_inbound_and_reset_cadence"
        ) as mock_reset:
            route_lead_message("lead-1", "hola, buenos días")

        mock_reset.assert_called_once_with("lead-1")

    def test_a_failure_recording_inbound_never_blocks_the_reply(self):
        """Best-effort: this must degrade gracefully like the file's other side-effect calls, not
        raise and lose the customer's reply."""
        mock_service = self._mock_crm_service()
        with patch(
            "services.taty_lead_router.get_crm_service", return_value=mock_service
        ), patch(
            "services.taty_lead_router._get_lead_stage", return_value="NUEVOS"
        ), patch(
            "services.taty_lead_router.resolve_cliente_cero_tenant_id", return_value=None
        ), patch(
            "services.taty_lead_router._record_inbound_and_reset_cadence",
            side_effect=Exception("supabase down"),
        ):
            result = route_lead_message("lead-1", "hola, buenos días")

        assert result["intent"] == "unknown"


class TestRecordInboundAndResetCadence:
    """The real implementation: stamps last_inbound_at and clears cadence_day, never reuses
    updated_at (which is bumped by unrelated writes)."""

    def test_updates_last_inbound_at_and_clears_cadence_day(self):
        mock_client = MagicMock()
        with patch(
            "services.taty_lead_router.get_service_supabase", return_value=mock_client
        ):
            _record_inbound_and_reset_cadence("lead-1")

        update_call = mock_client.table.return_value.update.call_args[0][0]
        assert update_call["cadence_day"] is None
        assert "last_inbound_at" in update_call
        mock_client.table.return_value.update.return_value.eq.assert_called_once_with(
            "id", "lead-1"
        )
