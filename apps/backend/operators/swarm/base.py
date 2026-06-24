"""
Base SwarmOperator class - Defines interface for all swarm operators.

All operators inherit from this base and implement execute() method.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result returned by operator"""
    task_id: str
    operator: str
    success: bool
    proof: Dict[str, Any]
    cost: float
    duration_ms: int
    error: Optional[str] = None


class SwarmOperator(ABC):
    """
    Base class for all swarm operators.

    Swarm operators are individual agents that execute tasks
    dispatched by the Conductor in parallel.

    Each operator:
    - Receives a Task
    - Executes work (create user, DB write, send email, etc)
    - Returns TaskResult with proof + cost
    - Reports success/failure
    """

    def __init__(self):
        """Initialize operator"""
        self.name = self.__class__.__name__
        logger.debug(f"Initialized operator: {self.name}")

    @abstractmethod
    async def execute(self, task: "Task") -> TaskResult:
        """
        Execute task and return result.

        Must be implemented by subclasses.

        Args:
            task: Task object with type, payload, etc

        Returns:
            TaskResult with proof + cost
        """
        pass

    async def _track_cost(self, operation_type: str) -> float:
        """Get cost for operation"""
        cost_matrix = {
            "auth_create": 0.001,
            "db_write_tenant": 0.002,
            "db_write_user": 0.0005,
            "db_write_role": 0.0005,
            "email_send": 0.01,
            "rls_check": 0.0001,
            "workflow_log": 0.0002,
        }
        return cost_matrix.get(operation_type, 0.0)

    def _log_proof(self, proof: Dict[str, Any]) -> None:
        """Log proof (for audit trail)"""
        logger.info(f"{self.name}: Proof recorded: {proof}")
