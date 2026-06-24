"""Comms Operator - T11.5: Sends welcome emails and logs workflow."""

import asyncio
from datetime import datetime
from .base import SwarmOperator, TaskResult
import logging

logger = logging.getLogger(__name__)


class CommsOperator(SwarmOperator):
    """Sends welcome emails and notifications."""

    async def execute(self, task) -> TaskResult:
        """Send welcome email."""
        logger.info(f"CommsOperator: Sending welcome email to {task.payload.get('email')}")
        start = datetime.utcnow()

        try:
            email = task.payload.get("email")
            plan = task.payload.get("plan")

            # Mock: send email
            await asyncio.sleep(0.12)

            proof = {
                "email": email,
                "type": "welcome",
                "plan": plan,
                "status": "sent",
                "sent_at": datetime.utcnow().isoformat()
            }

            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            cost = await self._track_cost("email_send")

            logger.info(f"CommsOperator: ✅ Welcome email sent to {email}")
            self._log_proof(proof)

            return TaskResult(
                task_id=task.id,
                operator="comms_operator",
                success=True,
                proof=proof,
                cost=cost,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.error(f"CommsOperator: ❌ {str(e)}")
            return TaskResult(
                task_id=task.id,
                operator="comms_operator",
                success=False,
                proof={},
                cost=0.0,
                duration_ms=duration_ms,
                error=str(e)
            )


class WorkflowTrackerOperator(SwarmOperator):
    """Logs workflow execution to audit trail."""

    async def execute(self, task) -> TaskResult:
        """Log workflow."""
        logger.info(f"WorkflowTrackerOperator: Logging mission {task.payload.get('mission_id')}")
        start = datetime.utcnow()

        try:
            mission_id = task.payload.get("mission_id")
            email = task.payload.get("email")

            # Mock: log to audit trail
            await asyncio.sleep(0.02)

            proof = {
                "mission_id": mission_id,
                "email": email,
                "logged": True,
                "entries": 1,
                "logged_at": datetime.utcnow().isoformat()
            }

            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            cost = await self._track_cost("workflow_log")

            logger.info(f"WorkflowTrackerOperator: ✅ Workflow logged for {mission_id}")
            self._log_proof(proof)

            return TaskResult(
                task_id=task.id,
                operator="workflow_operator",
                success=True,
                proof=proof,
                cost=cost,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.error(f"WorkflowTrackerOperator: ❌ {str(e)}")
            return TaskResult(
                task_id=task.id,
                operator="workflow_operator",
                success=False,
                proof={},
                cost=0.0,
                duration_ms=duration_ms,
                error=str(e)
            )
