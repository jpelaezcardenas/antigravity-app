"""
Maestro Orchestrator Service (FASE 4, Slice 5).

Manages agent registry and coordinates parallel quick_status() fan-out
across all registered agents with per-agent timeout handling.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Dict, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Global agent registry: agent_id → {"agent": instance, "timeout": seconds}
_AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {}


@runtime_checkable
class AgentProtocol(Protocol):
    """
    Protocol that all Maestro-registered agents must implement.

    Any agent calling quick_status() must define it as async def,
    not sync def. Sync implementations are rejected at registration.
    """

    async def quick_status(self) -> Dict[str, Any]:
        """
        Return agent health/status in a structured format.

        Returns:
            dict with at least {"status": "ok"|"timeout"|"error", ...}
        """
        ...


def register_agent(
    agent_id: str,
    agent: Any,
    timeout_seconds: float = 0.4,
) -> str:
    """
    Register an agent with Maestro orchestrator.

    Validates that agent.quick_status() is async (not sync).
    Raises ValueError if quick_status is sync.

    Args:
        agent_id: Unique identifier for the agent
        agent: Agent instance implementing AgentProtocol
        timeout_seconds: Per-agent timeout for quick_status() calls (default 400ms)

    Returns:
        agent_id (for chaining)

    Raises:
        ValueError: If agent.quick_status is not async
    """
    if not hasattr(agent, "quick_status"):
        raise ValueError(f"Agent {agent_id} does not have quick_status method")

    quick_status_method = getattr(agent, "quick_status")

    # Check if it's async
    if not asyncio.iscoroutinefunction(quick_status_method):
        raise ValueError(
            f"Agent {agent_id} has sync quick_status(): "
            f"must be async def. "
            f"See AgentProtocol in maestro_service.py for contract."
        )

    _AGENT_REGISTRY[agent_id] = {
        "agent": agent,
        "timeout": timeout_seconds,
    }
    logger.info(f"Agent {agent_id} registered with timeout {timeout_seconds}s")
    return agent_id


def get_registered_agents() -> Dict[str, Dict[str, Any]]:
    """
    Get the global agent registry.

    Returns:
        dict mapping agent_id → {"agent": instance, "timeout": float}
    """
    return _AGENT_REGISTRY


def unregister_agent(agent_id: str) -> None:
    """Remove an agent from the registry."""
    if agent_id in _AGENT_REGISTRY:
        del _AGENT_REGISTRY[agent_id]
        logger.info(f"Agent {agent_id} unregistered")


async def invoke_swarm_status() -> Dict[str, Any]:
    """
    Fan out quick_status() calls to all registered agents concurrently.

    Returns a per-agent status entry. If one agent times out or errors,
    that agent's entry is marked appropriately and others still return.

    Returns:
        {
            "agents": {
                "agent_id_1": {"status": "ok", ...},
                "agent_id_2": {"status": "timeout"},
                "agent_id_3": {"status": "error", "error": "msg"},
            },
            "total_agents": int,
            "healthy": int,
            "timeouts": int,
            "errors": int,
        }
    """
    if not _AGENT_REGISTRY:
        return {
            "agents": {},
            "total_agents": 0,
            "healthy": 0,
            "timeouts": 0,
            "errors": 0,
        }

    async def call_agent_with_timeout(agent_id: str, agent_info: Dict[str, Any]) -> tuple:
        """Call agent.quick_status() with timeout, return (agent_id, result_dict)."""
        agent = agent_info["agent"]
        timeout = agent_info["timeout"]

        try:
            result = await asyncio.wait_for(
                agent.quick_status(),
                timeout=timeout,
            )
            return (agent_id, result)
        except asyncio.TimeoutError:
            return (agent_id, {"status": "timeout"})
        except Exception as e:
            logger.exception(f"Error calling {agent_id}.quick_status()")
            return (agent_id, {"status": "error", "error": str(e)})

    # Fan out all agents concurrently
    tasks = [
        call_agent_with_timeout(agent_id, agent_info)
        for agent_id, agent_info in _AGENT_REGISTRY.items()
    ]

    results = await asyncio.gather(*tasks)

    # Aggregate results
    agents_result = {}
    healthy_count = 0
    timeout_count = 0
    error_count = 0

    for agent_id, status_dict in results:
        agents_result[agent_id] = status_dict
        if status_dict.get("status") == "ok":
            healthy_count += 1
        elif status_dict.get("status") == "timeout":
            timeout_count += 1
        elif status_dict.get("status") == "error":
            error_count += 1

    return {
        "agents": agents_result,
        "total_agents": len(_AGENT_REGISTRY),
        "healthy": healthy_count,
        "timeouts": timeout_count,
        "errors": error_count,
    }
