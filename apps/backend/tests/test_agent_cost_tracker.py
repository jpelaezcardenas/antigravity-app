"""
Tests for AgentCostTracker
(change agent-operations-multitenant-security, Slice 3).

Deterministic cost matrix: agent:operation → Decimal cost.
Unknown operations resolve to a documented default.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from services.agent_cost_tracker import AgentCostTracker, AGENT_OPERATION_COSTS


class TestAgentOperationCosts:
    def test_known_operation_has_cost(self):
        assert AGENT_OPERATION_COSTS.get("centinela:generate_draft") == Decimal("0.01")
        assert AGENT_OPERATION_COSTS.get("pulso:summary") == Decimal("0.005")

    def test_known_operations_all_are_decimal(self):
        for op, cost in AGENT_OPERATION_COSTS.items():
            assert isinstance(cost, Decimal), f"{op} cost is {type(cost)}, not Decimal"


class TestAgentCostTrackerResolveCost:
    def test_resolve_known_operation(self):
        tracker = AgentCostTracker()
        cost = tracker.resolve_cost("centinela", "generate_draft")
        assert cost == Decimal("0.01")

    def test_resolve_unknown_operation_returns_default(self):
        tracker = AgentCostTracker()
        cost = tracker.resolve_cost("unknown_agent", "unknown_op")
        assert cost == tracker.DEFAULT_COST
        assert isinstance(cost, Decimal)

    def test_resolve_partial_match_returns_default(self):
        """Only exact 'agent:operation' matches; partial doesn't count."""
        tracker = AgentCostTracker()
        # centinela exists, but centinela:nonexistent doesn't
        cost = tracker.resolve_cost("centinela", "nonexistent")
        assert cost == tracker.DEFAULT_COST

    def test_blocked_operation_resolves_to_zero(self):
        """An invocation blocked by access control has cost 0."""
        tracker = AgentCostTracker()
        cost = tracker.resolve_cost_for_status("centinela", "summary", status="blocked")
        assert cost == Decimal("0")

    def test_successful_operation_resolves_normally(self):
        """A blocked status overrides cost; other statuses use the matrix."""
        tracker = AgentCostTracker()
        cost = tracker.resolve_cost_for_status("centinela", "generate_draft", status="success")
        assert cost == AGENT_OPERATION_COSTS.get("centinela:generate_draft")
