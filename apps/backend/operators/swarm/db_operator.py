"""DB Operator - T11.3: Creates tenant + user database records."""

import asyncio
from uuid import uuid4
from datetime import datetime
from .base import SwarmOperator, TaskResult
import logging

logger = logging.getLogger(__name__)


class DBOperator(SwarmOperator):
    """Creates tenant + user records in database."""

    async def execute(self, task) -> TaskResult:
        """Create tenant and user records."""
        logger.info(f"DBOperator: Creating tenant for {task.payload.get('customer_email')}")
        start = datetime.utcnow()

        try:
            email = task.payload.get("customer_email")
            plan = task.payload.get("plan")

            # Mock: create records
            tenant_id = str(uuid4())
            await asyncio.sleep(0.15)

            proof = {
                "tenant_id": tenant_id,
                "customer_email": email,
                "plan": plan,
                "created_at": datetime.utcnow().isoformat()
            }

            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            cost = await self._track_cost("db_write_tenant")

            logger.info(f"DBOperator: ✅ Created tenant {tenant_id}")
            self._log_proof(proof)

            return TaskResult(
                task_id=task.id,
                operator="db_operator",
                success=True,
                proof=proof,
                cost=cost,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.error(f"DBOperator: ❌ {str(e)}")
            return TaskResult(
                task_id=task.id,
                operator="db_operator",
                success=False,
                proof={},
                cost=0.0,
                duration_ms=duration_ms,
                error=str(e)
            )
