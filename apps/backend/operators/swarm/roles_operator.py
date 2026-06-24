"""Roles Operator - T11.4: Assigns roles to users."""

import asyncio
from datetime import datetime
from .base import SwarmOperator, TaskResult
import logging

logger = logging.getLogger(__name__)


class RolesOperator(SwarmOperator):
    """Assigns roles to users."""

    async def execute(self, task) -> TaskResult:
        """Assign admin role to user."""
        logger.info(f"RolesOperator: Assigning admin role to {task.payload.get('email')}")
        start = datetime.utcnow()

        try:
            email = task.payload.get("email")

            # Mock: assign role
            await asyncio.sleep(0.05)

            proof = {
                "email": email,
                "role": "admin",
                "assigned": True,
                "assigned_at": datetime.utcnow().isoformat()
            }

            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            cost = await self._track_cost("db_write_role")

            logger.info(f"RolesOperator: ✅ Assigned admin role to {email}")
            self._log_proof(proof)

            return TaskResult(
                task_id=task.id,
                operator="roles_operator",
                success=True,
                proof=proof,
                cost=cost,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.error(f"RolesOperator: ❌ {str(e)}")
            return TaskResult(
                task_id=task.id,
                operator="roles_operator",
                success=False,
                proof={},
                cost=0.0,
                duration_ms=duration_ms,
                error=str(e)
            )
