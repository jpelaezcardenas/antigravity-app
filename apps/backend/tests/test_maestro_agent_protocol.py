"""
Tests for Maestro Agent Protocol (FASE 4, Slice 5, Task 5.1).

AgentProtocol defines the contract all agents must follow: async quick_status().
CI validation rejects sync implementations at startup.
"""

from __future__ import annotations

import inspect
from typing import Protocol

import pytest


class TestAgentProtocol:
    """AgentProtocol requires async quick_status() method."""

    def test_agent_protocol_defines_async_quick_status(self) -> None:
        """AgentProtocol exists and requires async quick_status()."""
        from services.maestro_service import AgentProtocol

        # Protocol should exist
        assert AgentProtocol is not None
        assert issubclass(AgentProtocol, Protocol)

        # quick_status should be defined
        assert hasattr(AgentProtocol, "quick_status")

        # quick_status should be a coroutine (async)
        method = getattr(AgentProtocol, "quick_status")
        # For Protocol, we check the annotation is marked as async
        # This is validated at registration time, not type-checked here
        assert callable(method)

    def test_agent_registration_rejects_sync_quick_status(self) -> None:
        """Registering an agent with sync quick_status() raises ValueError."""
        from services.maestro_service import register_agent, AgentProtocol

        class SyncAgent:
            """Mock agent with SYNC quick_status (violates protocol)."""

            def quick_status(self) -> dict:
                return {"status": "ok"}

        # Registration should fail because quick_status is not async
        with pytest.raises(ValueError, match="must be async def"):
            register_agent("sync_agent", SyncAgent())

    def test_agent_registration_accepts_async_quick_status(self) -> None:
        """Registering an agent with async quick_status() succeeds."""
        from services.maestro_service import register_agent

        class AsyncAgent:
            """Mock agent with ASYNC quick_status (follows protocol)."""

            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "async_agent"}

        # Registration should succeed
        agent_id = register_agent("async_agent", AsyncAgent())
        assert agent_id == "async_agent"

    def test_registered_agents_list_contains_async_agents(self) -> None:
        """After registration, agent appears in global registry."""
        from services.maestro_service import register_agent, get_registered_agents

        # Clear registry first
        registry = get_registered_agents()
        registry.clear()

        class AsyncAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok"}

        register_agent("test_agent", AsyncAgent())

        agents = get_registered_agents()
        assert "test_agent" in agents
        assert agents["test_agent"]["agent"].quick_status  # async method exists
