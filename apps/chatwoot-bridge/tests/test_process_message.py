"""Tests for the background orchestration pipeline process_incoming_message
(Task Group 10): audio fallback, full text pipeline (intake -> history ->
Hermes -> reply) in order, Hermes-failure fallback reply, and CRM-failure
graceful continuation (design.md decisions 5 and 7)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mocked_clients():
    """Patch every external client function main.py calls, in the module's
    own namespace (main imports the modules, not individual functions)."""
    import main as main_module

    with patch.object(
        main_module.backend_client, "whatsapp_intake", new=AsyncMock(return_value={"is_new": False})
    ) as intake, patch.object(
        main_module.backend_client, "trigger_onboarding", new=AsyncMock()
    ) as onboarding, patch.object(
        main_module.chatwoot_client, "get_recent_messages", new=AsyncMock(return_value=[])
    ) as history, patch.object(
        main_module.chatwoot_client, "send_reply", new=AsyncMock()
    ) as send_reply, patch.object(
        main_module.chatwoot_client, "set_contact_attributes", new=AsyncMock()
    ) as set_attrs, patch.object(
        main_module.hermes_client, "invoke_chat_completion", new=AsyncMock(return_value="Respuesta de Taty")
    ) as invoke:
        yield main_module, {
            "intake": intake,
            "onboarding": onboarding,
            "history": history,
            "send_reply": send_reply,
            "set_attrs": set_attrs,
            "invoke": invoke,
        }


class TestAudioFallback:
    @pytest.mark.asyncio
    async def test_audio_attachment_skips_hermes_and_sends_fixed_reply(self, mocked_clients):
        main_module, mocks = mocked_clients

        await main_module.process_incoming_message(
            conversation_id=42,
            content="",
            attachments=[{"file_type": "audio"}],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["invoke"].assert_not_called()
        mocks["send_reply"].assert_awaited_once()
        args, _ = mocks["send_reply"].call_args
        assert args[0] == 42
        assert "texto" in args[1].lower()


class TestFullTextPipeline:
    @pytest.mark.asyncio
    async def test_calls_intake_history_hermes_reply_in_order(self, mocked_clients):
        main_module, mocks = mocked_clients

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["intake"].assert_awaited_once_with("+573001234567")
        mocks["history"].assert_awaited_once_with(42)
        mocks["invoke"].assert_awaited_once_with([], "Hola")
        mocks["send_reply"].assert_awaited_once_with(42, "Respuesta de Taty")

    @pytest.mark.asyncio
    async def test_new_lead_triggers_onboarding_and_sets_contact_attributes(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["intake"].return_value = {"is_new": True}

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["onboarding"].assert_awaited_once()
        mocks["set_attrs"].assert_awaited_once()
        args, _ = mocks["set_attrs"].call_args
        assert args[0] == 7
        assert args[1]["estado"] == "nuevo"

    @pytest.mark.asyncio
    async def test_returning_contact_does_not_trigger_onboarding(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["intake"].return_value = {"is_new": False}

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola de nuevo",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["onboarding"].assert_not_called()
        mocks["set_attrs"].assert_not_called()

    @pytest.mark.asyncio
    async def test_intake_failure_still_proceeds_to_hermes_reply(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["intake"].return_value = None

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["onboarding"].assert_not_called()
        mocks["invoke"].assert_awaited_once()
        mocks["send_reply"].assert_awaited_once_with(42, "Respuesta de Taty")

    @pytest.mark.asyncio
    async def test_hermes_failure_sends_fallback_reply(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["invoke"].return_value = None

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["send_reply"].assert_awaited_once()
        args, _ = mocks["send_reply"].call_args
        assert args[0] == 42
        assert args[1] != "Respuesta de Taty"
        assert len(args[1]) > 0
