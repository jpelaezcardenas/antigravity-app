"""Tests for the background orchestration pipeline process_incoming_message.

taty-channel-consolidation: the reply now comes from the backend's Taty sales router
(backend_client.taty_reply) instead of a raw Hermes chat completion, so a single brain owns
intent classification, Wompi payment links and KB grounding on every channel.

Consequence, asserted below: when the lead cannot be identified (intake down or no phone), the
bridge sends the human-takeover fallback rather than answering anyway. Answering an ungrounded
tax question without lead context is precisely what the consolidation exists to prevent.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mocked_clients():
    """Patch every external client function main.py calls, in the module's
    own namespace (main imports the modules, not individual functions)."""
    import main as main_module

    with patch.object(
        main_module.backend_client,
        "whatsapp_intake",
        new=AsyncMock(return_value={"is_new": False, "lead_id": "lead-1"}),
    ) as intake, patch.object(
        main_module.backend_client,
        "taty_reply",
        new=AsyncMock(return_value="Respuesta de Taty"),
    ) as taty_reply, patch.object(
        main_module.chatwoot_client, "send_reply", new=AsyncMock()
    ) as send_reply, patch.object(
        main_module.chatwoot_client, "set_contact_attributes", new=AsyncMock()
    ) as set_attrs, patch.object(
        main_module.hermes_client, "invoke_chat_completion", new=AsyncMock()
    ) as invoke:
        yield main_module, {
            "intake": intake,
            "taty_reply": taty_reply,
            "send_reply": send_reply,
            "set_attrs": set_attrs,
            "invoke": invoke,
        }


class TestAudioFallback:
    @pytest.mark.asyncio
    async def test_audio_attachment_skips_routing_and_sends_fixed_reply(self, mocked_clients):
        main_module, mocks = mocked_clients

        await main_module.process_incoming_message(
            conversation_id=42,
            content="",
            attachments=[{"file_type": "audio"}],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["taty_reply"].assert_not_called()
        mocks["send_reply"].assert_awaited_once()
        args, _ = mocks["send_reply"].call_args
        assert args[0] == 42
        assert "texto" in args[1].lower()


class TestSingleBrainInvariant:
    @pytest.mark.asyncio
    async def test_reply_comes_from_the_sales_router_not_hermes(self, mocked_clients):
        main_module, mocks = mocked_clients

        await main_module.process_incoming_message(
            conversation_id=42,
            content="quiero saber si me toca declarar renta",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["intake"].assert_awaited_once_with("+573001234567")
        mocks["taty_reply"].assert_awaited_once_with(
            "lead-1", "quiero saber si me toca declarar renta"
        )
        mocks["invoke"].assert_not_called()
        mocks["send_reply"].assert_awaited_once_with(42, "Respuesta de Taty")


class TestLeadLifecycle:
    @pytest.mark.asyncio
    async def test_new_lead_sets_contact_attributes_without_onboarding(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["intake"].return_value = {"is_new": True, "lead_id": "lead-1"}

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["set_attrs"].assert_awaited_once()
        args, _ = mocks["set_attrs"].call_args
        assert args[0] == 7
        assert args[1]["estado"] == "nuevo"

    @pytest.mark.asyncio
    async def test_returning_contact_does_not_set_contact_attributes(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["intake"].return_value = {"is_new": False, "lead_id": "lead-1"}

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola de nuevo",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["set_attrs"].assert_not_called()


class TestDegradedPaths:
    @pytest.mark.asyncio
    async def test_intake_failure_hands_over_and_never_answers(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["intake"].return_value = None

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone="+573001234567",
        )

        mocks["taty_reply"].assert_not_called()
        mocks["invoke"].assert_not_called()
        mocks["send_reply"].assert_awaited_once()
        args, _ = mocks["send_reply"].call_args
        assert args[0] == 42
        assert len(args[1]) > 0

    @pytest.mark.asyncio
    async def test_missing_phone_hands_over(self, mocked_clients):
        main_module, mocks = mocked_clients

        await main_module.process_incoming_message(
            conversation_id=42,
            content="Hola",
            attachments=[],
            contact_id=7,
            phone=None,
        )

        mocks["intake"].assert_not_called()
        mocks["taty_reply"].assert_not_called()
        mocks["send_reply"].assert_awaited_once()

    @pytest.mark.asyncio
    async def test_router_failure_sends_fallback_reply(self, mocked_clients):
        main_module, mocks = mocked_clients
        mocks["taty_reply"].return_value = None

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
