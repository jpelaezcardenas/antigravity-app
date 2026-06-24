"""
Agent operation cost tracking
(change agent-operations-multitenant-security, Slice 3).

Deterministic cost matrix: agent:operation → Decimal cost.
Per agent invocation type. Unknown ops fall back to DEFAULT_COST.
Blocked (access-denied) invocations always cost zero.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

# Cost matrix: "{agent}:{operation}" → cost in USD (Decimal for precision).
# Derived from the T11.6 cost matrix in Phase 3, adapted for the agent layer.
AGENT_OPERATION_COSTS: dict[str, Decimal] = {
    # PULSO (financial summary)
    "pulso:summary": Decimal("0.005"),
    "pulso:get_daily_summary": Decimal("0.005"),
    # CENTINELA (tax compliance)
    "centinela:generate_draft": Decimal("0.01"),
    "centinela:poll_discrepancies": Decimal("0.008"),
    # RADAR (risk analysis)
    "radar:calculate_risk_score": Decimal("0.008"),
    "radar:calculate_cashflow_forecast": Decimal("0.008"),
    # TATY (task automation)
    "taty:invoke": Decimal("0.015"),
    "taty:classify_intent": Decimal("0.005"),
    # SOCIAL-OPS (content/leads)
    "social-ops:status": Decimal("0.003"),
    "social-ops:get_ideas": Decimal("0.003"),
    "social-ops:draft_lead_reply": Decimal("0.005"),
    # AUDITORÍA SOMBRA (audit report)
    "audit:generate_audit_report": Decimal("0.025"),
    # APPROVAL (queue)
    "approval:enqueue": Decimal("0.02"),
    "approval:approve_draft": Decimal("0.015"),
    # MAESTRO (orchestration)
    "maestro:invoke_swarm": Decimal("0.012"),
}


class AgentCostTracker:
    """Resolves and tracks cost for agent operations."""

    # Default cost for unknown agent:operation combinations.
    DEFAULT_COST: Decimal = Decimal("0.01")

    def resolve_cost(self, agent: str, operation: str) -> Decimal:
        """Return the cost for an agent:operation, or DEFAULT_COST if unknown."""
        key = f"{agent}:{operation}"
        return AGENT_OPERATION_COSTS.get(key, self.DEFAULT_COST)

    def resolve_cost_for_status(
        self, agent: str, operation: str, status: str
    ) -> Decimal:
        """Return cost, zero for blocked operations."""
        if status == "blocked":
            return Decimal("0")
        return self.resolve_cost(agent, operation)
