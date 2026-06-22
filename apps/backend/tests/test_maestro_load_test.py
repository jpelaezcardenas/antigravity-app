"""
Load test for Maestro orchestrator (FASE 4, Slice 5, Task 5.7).

Verify that swarm status invocation completes within <500ms p95 latency budget.
"""

from __future__ import annotations

import asyncio
import time
from typing import List

import pytest


class TestMaestroLoadTest:
    """Load test for swarm status endpoint latency."""

    @pytest.mark.asyncio
    async def test_swarm_status_latency_under_500ms_p95_with_6_agents(self) -> None:
        """
        Concurrent invocations of swarm status should complete within 500ms p95.
        Test with 6 agents (all registered) under concurrent load.
        """
        from services.maestro_service import (
            register_agent,
            invoke_swarm_status,
            get_registered_agents,
        )

        # Clear and register 6 agents
        registry = get_registered_agents()
        registry.clear()

        class TestAgent:
            def __init__(self, name: str, latency_ms: float = 50):
                self.name = name
                self.latency_ms = latency_ms

            async def quick_status(self) -> dict:
                # Simulate agent response time
                await asyncio.sleep(self.latency_ms / 1000.0)
                return {"status": "ok", "agent": self.name, "health": 95}

        # Register 6 agents with varying latencies (50-100ms each)
        agents = {
            "pulso": TestAgent("pulso", 50),
            "radar": TestAgent("radar", 75),
            "auditoria": TestAgent("auditoria", 60),
            "centinela": TestAgent("centinela", 80),
            "taty": TestAgent("taty", 55),
            "social_ops": TestAgent("social_ops", 70),
        }

        for agent_id, agent in agents.items():
            register_agent(agent_id, agent)

        # Run swarm status invocation multiple times to collect latencies
        latencies_ms: List[float] = []
        num_iterations = 10

        for _ in range(num_iterations):
            start = time.time()
            result = await invoke_swarm_status()
            elapsed_ms = (time.time() - start) * 1000

            latencies_ms.append(elapsed_ms)

            # Verify all agents responded
            assert len(result["agents"]) == 6
            assert result["healthy"] == 6

        # Calculate p95 latency
        latencies_ms.sort()
        p95_index = int(len(latencies_ms) * 0.95)
        p95_latency = latencies_ms[p95_index]

        print(f"\n=== Load Test Results ===")
        print(f"Iterations: {num_iterations}")
        print(f"Min latency: {min(latencies_ms):.2f}ms")
        print(f"Max latency: {max(latencies_ms):.2f}ms")
        print(f"Avg latency: {sum(latencies_ms) / len(latencies_ms):.2f}ms")
        print(f"P95 latency: {p95_latency:.2f}ms")
        print(f"Budget: 500ms")
        print(f"Status: {'PASS' if p95_latency < 500 else 'FAIL'}")

        # Assert p95 < 500ms
        assert p95_latency < 500, f"P95 latency {p95_latency:.2f}ms exceeds 500ms budget"

    @pytest.mark.asyncio
    async def test_swarm_status_concurrent_requests_all_complete_within_budget(
        self,
    ) -> None:
        """
        Multiple concurrent swarm status requests should all complete within budget.
        Simulates production load where multiple clients invoke status concurrently.
        """
        from services.maestro_service import (
            register_agent,
            invoke_swarm_status,
            get_registered_agents,
        )

        registry = get_registered_agents()
        registry.clear()

        class FastAgent:
            async def quick_status(self) -> dict:
                await asyncio.sleep(0.05)  # 50ms
                return {"status": "ok", "agent": "fast"}

        register_agent("agent1", FastAgent())

        # Launch 5 concurrent invocations
        start = time.time()
        tasks = [invoke_swarm_status() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        elapsed_ms = (time.time() - start) * 1000

        # All requests should complete
        assert len(results) == 5
        for result in results:
            assert result["healthy"] == 1

        # Total time should be ~50ms (parallel, not sequential)
        # Allow some overhead, but should be much less than 500ms
        assert elapsed_ms < 200, f"Concurrent requests took {elapsed_ms:.2f}ms (expected ~50-100ms parallel)"

        print(f"\n=== Concurrent Load Test Results ===")
        print(f"Concurrent requests: 5")
        print(f"Total time: {elapsed_ms:.2f}ms")
        print(f"Expected: ~50-100ms (parallel)")
        print(f"Status: {'PASS' if elapsed_ms < 200 else 'FAIL'}")
