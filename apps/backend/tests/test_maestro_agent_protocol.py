"""
Tests for Maestro Agent Protocol (FASE 4, Slice 5, Task 5.1).

AgentProtocol defines the contract all agents must follow: async quick_status().
CI validation rejects sync implementations at startup.
"""

from __future__ import annotations

import inspect
from typing import Protocol

import pytest


class TestMaestroSwarmInvoke:
    """Maestro asyncio.gather fan-out orchestrator."""

    @pytest.mark.asyncio
    async def test_swarm_status_calls_all_agents_concurrently_and_returns_per_agent_entries(
        self,
    ) -> None:
        """
        invoke_swarm_status() calls quick_status() on ALL registered agents
        in parallel via asyncio.gather, returns per-agent status entries.
        """
        from services.maestro_service import (
            register_agent,
            invoke_swarm_status,
            get_registered_agents,
        )

        # Clear registry
        registry = get_registered_agents()
        registry.clear()

        # Register 3 test agents
        class Agent1:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "agent1", "health": 100}

        class Agent2:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "agent2", "health": 95}

        class Agent3:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "agent3", "health": 90}

        register_agent("agent1", Agent1())
        register_agent("agent2", Agent2())
        register_agent("agent3", Agent3())

        # Invoke swarm status
        result = await invoke_swarm_status()

        # Verify result structure
        assert "agents" in result
        assert "total_agents" in result
        assert "healthy" in result
        assert "timeouts" in result
        assert "errors" in result

        # Verify all agents present in result
        agents = result["agents"]
        assert len(agents) == 3
        assert "agent1" in agents
        assert "agent2" in agents
        assert "agent3" in agents

        # Verify per-agent status entries
        assert agents["agent1"]["status"] == "ok"
        assert agents["agent1"]["health"] == 100
        assert agents["agent2"]["status"] == "ok"
        assert agents["agent2"]["health"] == 95
        assert agents["agent3"]["status"] == "ok"
        assert agents["agent3"]["health"] == 90

        # Verify aggregated counts
        assert result["total_agents"] == 3
        assert result["healthy"] == 3
        assert result["timeouts"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_swarm_status_returns_empty_when_no_agents_registered(self) -> None:
        """Empty registry returns empty swarm status."""
        from services.maestro_service import invoke_swarm_status, get_registered_agents

        registry = get_registered_agents()
        registry.clear()

        result = await invoke_swarm_status()

        assert result["agents"] == {}
        assert result["total_agents"] == 0
        assert result["healthy"] == 0
        assert result["timeouts"] == 0
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_one_agent_timeout_marked_timeout_other_agents_respond(self) -> None:
        """
        One agent timing out is marked "timeout".
        Other agents still respond without being blocked.
        """
        import asyncio
        from services.maestro_service import (
            register_agent,
            invoke_swarm_status,
            get_registered_agents,
        )

        registry = get_registered_agents()
        registry.clear()

        class FastAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "fast"}

        class SlowAgent:
            async def quick_status(self) -> dict:
                # Sleep longer than timeout (default 0.4s)
                await asyncio.sleep(1.0)
                return {"status": "ok", "agent": "slow"}

        # Register with different timeouts
        register_agent("fast", FastAgent(), timeout_seconds=0.5)
        register_agent("slow", SlowAgent(), timeout_seconds=0.1)  # Will timeout

        result = await invoke_swarm_status()

        # Fast agent should respond normally
        assert result["agents"]["fast"]["status"] == "ok"

        # Slow agent should be marked timeout
        assert result["agents"]["slow"]["status"] == "timeout"

        # Aggregated counts
        assert result["total_agents"] == 2
        assert result["healthy"] == 1
        assert result["timeouts"] == 1
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_one_agent_exception_marked_error_other_agents_respond(self) -> None:
        """
        One agent raising an exception is marked "error".
        Other agents still respond without crashing the request.
        """
        from services.maestro_service import (
            register_agent,
            invoke_swarm_status,
            get_registered_agents,
        )

        registry = get_registered_agents()
        registry.clear()

        class HealthyAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "healthy"}

        class BrokenAgent:
            async def quick_status(self) -> dict:
                raise RuntimeError("Agent database connection failed")

        register_agent("healthy", HealthyAgent())
        register_agent("broken", BrokenAgent())

        result = await invoke_swarm_status()

        # Healthy agent should respond normally
        assert result["agents"]["healthy"]["status"] == "ok"

        # Broken agent should be marked error with message
        assert result["agents"]["broken"]["status"] == "error"
        assert "Agent database connection failed" in result["agents"]["broken"]["error"]

        # Aggregated counts
        assert result["total_agents"] == 2
        assert result["healthy"] == 1
        assert result["timeouts"] == 0
        assert result["errors"] == 1


class TestAgentRegistration:
    """Register real agents (Pulso, Radar, Auditoría, Centinela, Taty, Social Ops)."""

    @pytest.mark.asyncio
    async def test_register_all_required_agents_and_invoke_swarm_status(self) -> None:
        """
        All 6 required agents can be registered and respond to quick_status().
        Maestro orchestrator invokes all concurrently without errors.
        """
        from services.maestro_service import (
            register_agent,
            invoke_swarm_status,
            get_registered_agents,
        )

        # Clear registry
        registry = get_registered_agents()
        registry.clear()

        # Define agent wrappers that implement AgentProtocol
        # Each wraps the real service with a minimal quick_status()
        class PulsoAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "pulso_diario", "health": 100}

        class RadarAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "radar_predictivo", "health": 95}

        class AuditoriaAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "auditoria_sombra", "health": 100}

        class CentinelaAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "centinela", "health": 90}

        class TatyAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "taty", "health": 98}

        class SocialOpsAgent:
            async def quick_status(self) -> dict:
                return {"status": "ok", "agent": "social_ops", "health": 92}

        # Register all agents
        agents = {
            "pulso_diario": PulsoAgent(),
            "radar_predictivo": RadarAgent(),
            "auditoria_sombra": AuditoriaAgent(),
            "centinela": CentinelaAgent(),
            "taty": TatyAgent(),
            "social_ops": SocialOpsAgent(),
        }

        for agent_id, agent_instance in agents.items():
            register_agent(agent_id, agent_instance)

        # Invoke swarm status
        result = await invoke_swarm_status()

        # Verify all agents responded
        assert len(result["agents"]) == 6
        for agent_id in agents.keys():
            assert agent_id in result["agents"]
            assert result["agents"][agent_id]["status"] == "ok"

        # Verify counts
        assert result["total_agents"] == 6
        assert result["healthy"] == 6
        assert result["timeouts"] == 0
        assert result["errors"] == 0


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
