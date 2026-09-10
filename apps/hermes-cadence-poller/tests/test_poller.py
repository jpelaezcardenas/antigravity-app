"""poller.run_tick() — mirrors apps/hermes-gmail-poller's test style for the inert-without-config
guarantee (spec.md: "never a silent no-op that looks successful") and the send/skip flow."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings  # noqa: E402
import poller  # noqa: E402


def _iso_hours_ago(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


class TestRunTickInertWithoutConfig:
    def test_missing_internal_api_key_is_inert_and_logs_error(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key")

        result = poller.run_tick()

        assert result["skipped"] is True
        assert "INTERNAL_API_KEY" in result["reason"]

    def test_missing_supabase_credentials_is_inert_and_logs_error(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "internal-key")
        monkeypatch.setattr(settings, "SUPABASE_URL", "")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")

        result = poller.run_tick()

        assert result["skipped"] is True
        assert "credentials" in result["reason"].lower()


class TestRunTickSendsDueTouches:
    def test_no_eligible_leads_is_not_treated_as_skipped(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "internal-key")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key")

        with patch("supabase_client.get_eligible_leads", return_value=[]):
            result = poller.run_tick()

        assert result.get("skipped") is not True
        assert result["leads_checked"] == 0

    def test_due_lead_triggers_a_send_touch_call(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "internal-key")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key")

        leads = [
            {
                "id": "lead-1",
                "cadence_day": None,
                "last_inbound_at": None,
                "created_at": _iso_hours_ago(30),
            }
        ]

        calls = {}

        def _fake_send_touch(_client, lead_id, day):
            calls["lead_id"] = lead_id
            calls["day"] = day
            return {"sent": True}

        with patch("supabase_client.get_eligible_leads", return_value=leads), patch.object(
            poller, "_send_touch", _fake_send_touch
        ):
            result = poller.run_tick()

        assert calls == {"lead_id": "lead-1", "day": 1}
        assert result["touches_sent"] == 1
        assert result["touches_skipped"] == 0

    def test_lead_not_yet_due_sends_nothing(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "internal-key")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key")

        leads = [
            {
                "id": "lead-1",
                "cadence_day": None,
                "last_inbound_at": None,
                "created_at": _iso_hours_ago(1),
            }
        ]

        with patch("supabase_client.get_eligible_leads", return_value=leads), patch.object(
            poller, "_send_touch"
        ) as mock_send:
            result = poller.run_tick()

        mock_send.assert_not_called()
        assert result["touches_sent"] == 0
        assert result["touches_skipped"] == 0

    def test_backend_refusal_is_counted_as_skipped_not_sent(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "internal-key")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key")

        leads = [
            {
                "id": "lead-1",
                "cadence_day": None,
                "last_inbound_at": None,
                "created_at": _iso_hours_ago(30),
            }
        ]

        def _refused(_client, lead_id, day):
            return {"sent": False, "reason": "not_due_yet"}

        with patch("supabase_client.get_eligible_leads", return_value=leads), patch.object(
            poller, "_send_touch", _refused
        ):
            result = poller.run_tick()

        assert result["touches_sent"] == 0
        assert result["touches_skipped"] == 1

    def test_dry_run_never_calls_send_touch(self, monkeypatch):
        monkeypatch.setattr(settings, "INTERNAL_API_KEY", "internal-key")
        monkeypatch.setattr(settings, "SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "key")
        monkeypatch.setattr(settings, "DRY_RUN", True)

        leads = [
            {
                "id": "lead-1",
                "cadence_day": None,
                "last_inbound_at": None,
                "created_at": _iso_hours_ago(30),
            }
        ]

        with patch("supabase_client.get_eligible_leads", return_value=leads), patch.object(
            poller, "_send_touch"
        ) as mock_send:
            result = poller.run_tick()

        mock_send.assert_not_called()
        assert result["touches_sent"] == 1
