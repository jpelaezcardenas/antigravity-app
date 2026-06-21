"""
Maestro Orchestrator Service

Coordinates and parallelizes execution of multiple agents.
Swarm coordinator for Hermes Workspace.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class MaestroOrchestrator:
    """
    Central orchestrator: delegates to 5+ agents in parallel, synthesizes results.

    Execution model:
    - Max 5 concurrent agent invocations (ThreadPoolExecutor)
    - Target: < 500ms total execution time
    - Fallback: if 1 agent fails, others continue (resilient)
    - Telemetry: log each agent result + total time
    """

    AVAILABLE_AGENTS = [
        "centinela",
        "pulso",
        "radar",
        "auditoria",
        "taty",
        "social_ops",
        "kb",
        "approval_queue",
    ]

    MAX_CONCURRENT = 5
    TIMEOUT_MS = 5000

    @staticmethod
    async def invoke(
        action: str,
        agents: Optional[List[str]] = None,
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """
        Main orchestration entry point.

        Args:
            action: "status", "nightly-audit", "approval-sync", etc.
            agents: List of agent names to invoke (default: all read-only agents)
            parallel: Whether to run agents in parallel (default: True)

        Returns:
            {
                "status": "completed" | "partial_failure",
                "execution_time_ms": 420,
                "results": {agent_name: result, ...},
                "narrative": "synthesis summary",
                "errors": [...],
            }
        """
        try:
            if agents is None:
                agents = MaestroOrchestrator._default_agents_for_action(action)

            start_time = datetime.utcnow()

            if parallel:
                results, errors = await MaestroOrchestrator._invoke_parallel(agents, action)
            else:
                results, errors = await MaestroOrchestrator._invoke_sequential(agents, action)

            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Synthesize narrative
            narrative = MaestroOrchestrator._synthesize_narrative(action, results, errors)

            return {
                "status": "completed" if not errors else "partial_failure",
                "execution_time_ms": execution_time_ms,
                "results": results,
                "narrative": narrative,
                "errors": errors if errors else None,
                "timestamp": start_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Orchestrator fatal error: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    @staticmethod
    async def _invoke_parallel(agents: List[str], action: str) -> tuple:
        """
        Invoke multiple agents in parallel using ThreadPoolExecutor.

        Returns:
            (results: dict, errors: list)
        """
        results = {}
        errors = []

        # In real implementation, use ThreadPoolExecutor or asyncio.gather
        # For now, placeholder
        with ThreadPoolExecutor(max_workers=MaestroOrchestrator.MAX_CONCURRENT) as executor:
            futures = {}
            for agent_name in agents:
                future = executor.submit(
                    MaestroOrchestrator._call_agent,
                    agent_name,
                    action
                )
                futures[agent_name] = future

            for agent_name, future in futures.items():
                try:
                    result = future.result(timeout=MaestroOrchestrator.TIMEOUT_MS / 1000)
                    results[agent_name] = result
                    logger.info(f"Agent {agent_name} succeeded")
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {str(e)}")
                    errors.append({"agent": agent_name, "error": str(e)})

        return results, errors

    @staticmethod
    async def _invoke_sequential(agents: List[str], action: str) -> tuple:
        """
        Invoke agents sequentially (fallback, slower).

        Returns:
            (results: dict, errors: list)
        """
        results = {}
        errors = []

        for agent_name in agents:
            try:
                result = await asyncio.wait_for(
                    MaestroOrchestrator._call_agent_async(agent_name, action),
                    timeout=MaestroOrchestrator.TIMEOUT_MS / 1000
                )
                results[agent_name] = result
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {str(e)}")
                errors.append({"agent": agent_name, "error": str(e)})

        return results, errors

    @staticmethod
    def _call_agent(agent_name: str, action: str) -> Dict[str, Any]:
        """
        STUB: Call agent via HTTP or local service.
        In real implementation, route to appropriate service.
        """
        # Placeholder: map agent name to endpoint
        agent_endpoints = {
            "centinela": "/api/v1/centinela",
            "pulso": "/api/v1/pulso",
            "radar": "/api/v1/radar",
            "auditoria": "/api/v1/wizard/auditoria-sombra",
            "kb": "/api/v1/kb",
        }

        endpoint = agent_endpoints.get(agent_name)
        if not endpoint:
            raise ValueError(f"Unknown agent: {agent_name}")

        # In real implementation, call HTTP endpoint or local service
        logger.debug(f"Calling {agent_name} via {endpoint}")

        # Stub response
        return {
            "agent": agent_name,
            "status": "completed",
            "data": {"placeholder": "real data from agent"},
        }

    @staticmethod
    async def _call_agent_async(agent_name: str, action: str) -> Dict[str, Any]:
        """Async version of _call_agent."""
        return MaestroOrchestrator._call_agent(agent_name, action)

    @staticmethod
    def _default_agents_for_action(action: str) -> List[str]:
        """
        Return default agent list based on action.

        "status" → [centinela, pulso, radar] (quick overview)
        "nightly-audit" → [centinela, auditoria, kb] (thorough audit)
        "approval-sync" → [approval-queue] (sync pending approvals)
        """
        action_agents = {
            "status": ["centinela", "pulso", "radar"],
            "nightly-audit": ["centinela", "auditoria", "kb"],
            "approval-sync": ["approval_queue"],
            "full-swarm": MaestroOrchestrator.AVAILABLE_AGENTS,
        }
        return action_agents.get(action, ["pulso"])  # Default to pulso

    @staticmethod
    def _synthesize_narrative(
        action: str,
        results: Dict[str, Any],
        errors: List[Dict]
    ) -> str:
        """
        Synthesize results into 1-paragraph narrative for Hermes display.

        Args:
            action: The orchestration action that was requested
            results: Dict of agent results
            errors: List of errors (empty if all succeeded)

        Returns:
            Natural language summary
        """
        parts = []

        # Centinela status
        if "centinela" in results:
            centinela_data = results["centinela"].get("data", {})
            pending = centinela_data.get("pending_anomalies", 0)
            if pending > 0:
                parts.append(f"⚠️ {pending} anomalía(s) pendiente(s) en Centinela")
            else:
                parts.append("✅ Centinela: sin anomalías")

        # Pulso status
        if "pulso" in results:
            pulso_data = results["pulso"].get("data", {})
            caja = pulso_data.get("caja_disponible", 0)
            parts.append(f"💰 Caja: ${caja:,}")

        # Radar status
        if "radar" in results:
            radar_data = results["radar"].get("data", {})
            risk_level = radar_data.get("risk_level", "unknown")
            parts.append(f"📊 Riesgo: {risk_level}")

        # Errors
        if errors:
            parts.append(f"❌ {len(errors)} error(s) en agentes")

        return " | ".join(parts) if parts else "Estado normal"


# FastAPI integration (stub for FASE 4)
async def orchestrator_endpoint(action: str, agents: List[str] = None, parallel: bool = True):
    """
    Endpoint: POST /hermes/swarm/invoke

    Used by Hermes Workspace to trigger orchestration.
    """
    result = await MaestroOrchestrator.invoke(action, agents, parallel)
    return result
