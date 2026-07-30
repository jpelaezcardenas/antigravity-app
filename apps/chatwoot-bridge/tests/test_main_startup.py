"""Tests for the bridge's startup wiring of the durable-inbox poller (whatsapp-durable-inbox).

INBOX_POLLER_ENABLED defaults to False so the bridge keeps working standalone before the poller
is configured (e.g. before WHATSAPP_APP_SECRET is set in Railway, per design.md 4.4)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from config import settings


class TestPollerStartup:
    @pytest.mark.asyncio
    async def test_poller_task_started_when_enabled(self):
        import main as main_module

        with patch.object(settings, "INBOX_POLLER_ENABLED", True), patch.object(
            main_module.inbox_poller, "run_forever"
        ) as mock_run_forever:
            async with main_module.app.router.lifespan_context(main_module.app):
                pass

        mock_run_forever.assert_called_once()

    @pytest.mark.asyncio
    async def test_poller_not_started_when_disabled(self):
        import main as main_module

        with patch.object(settings, "INBOX_POLLER_ENABLED", False), patch.object(
            main_module.inbox_poller, "run_forever"
        ) as mock_run_forever:
            async with main_module.app.router.lifespan_context(main_module.app):
                pass

        mock_run_forever.assert_not_called()
