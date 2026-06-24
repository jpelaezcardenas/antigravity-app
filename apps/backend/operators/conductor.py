"""
Conductor: Orchestrates customer onboarding as Hermes Mission.

Responsible for:
- Creating missions (work units)
- Dispatching tasks to swarm operators (in parallel)
- Collecting checkpoints (proof of completion)
- Tracking cost + progress
- Managing mission state
- Integrating with Kanban board
"""

import asyncio
import logging
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field, asdict
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class MissionStatus(str, Enum):
    """Mission lifecycle states"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    """Task lifecycle states (Hermes Kanban compatible)"""
    ASSIGNED = "assigned"
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMED_OUT = "timed_out"


class CheckpointStatus(str, Enum):
    """Checkpoint states (proof of completion)"""
    SUCCESS = "✅"
    PENDING = "⏳"
    FAILED = "❌"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TaskResult:
    """Result returned by a swarm operator"""
    task_id: str
    operator: str
    success: bool
    proof: Dict[str, Any]  # The actual result (user_id, tenant_id, etc)
    cost: float
    duration_ms: int
    error: Optional[str] = None


@dataclass
class Checkpoint:
    """Proof of task completion"""
    timestamp: datetime
    task_type: str  # create_auth_user, create_tenant, assign_role, send_email
    status: CheckpointStatus
    proof: Dict[str, Any]  # The actual proof data
    operator_id: str
    duration_ms: int
    cost: float


@dataclass
class Task:
    """Work item dispatched to operator"""
    id: str
    type: str
    operator: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.ASSIGNED
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None


@dataclass
class Mission:
    """Hermes-compatible mission (orchestrated work unit)"""
    id: str
    type: str  # customer_registration, team_onboarding, etc
    status: MissionStatus
    objective: str

    # Tasks dispatched to swarm
    tasks: List[Task] = field(default_factory=list)

    # Checkpoints (proof of completion)
    checkpoints: List[Checkpoint] = field(default_factory=list)

    # Cost tracking
    cost: float = 0.0
    cost_breakdown: Dict[str, float] = field(default_factory=dict)

    # Progress tracking
    progress: float = 0.0  # 0-100%

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Operator assignments
    operator_assignments: Dict[str, str] = field(default_factory=dict)  # task_id → operator_name

    # Results
    final_result: Dict[str, Any] = field(default_factory=dict)

    # Blockers
    blockers: List[str] = field(default_factory=list)

    def add_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Record proof of task completion"""
        self.checkpoints.append(checkpoint)
        self.progress = (len([c for c in self.checkpoints if c.status == CheckpointStatus.SUCCESS]) / len(self.tasks)) * 100 if self.tasks else 0
        logger.debug(f"Mission {self.id}: checkpoint added, progress={self.progress:.1f}%")

    def add_blocker(self, blocker: str) -> None:
        """Record blocker"""
        if blocker not in self.blockers:
            self.blockers.append(blocker)
            self.status = MissionStatus.BLOCKED
            logger.warning(f"Mission {self.id}: BLOCKED - {blocker}")


# ============================================================================
# CONDUCTOR
# ============================================================================

class OnboardingConductor:
    """
    Orchestrates customer onboarding as a Hermes Mission.

    Coordinates:
    - Mission creation
    - Task dispatching (to swarm operators in parallel)
    - Checkpoint collection (proof)
    - Cost tracking
    - Kanban board integration
    """

    def __init__(self, session: AsyncSession):
        """Initialize conductor"""
        self.session = session
        self.operators: Dict[str, Any] = {}  # Registered operators

    async def register_operator(self, name: str, operator_class: type) -> None:
        """Register a swarm operator"""
        self.operators[name] = operator_class()
        logger.info(f"Registered operator: {name}")

    async def conduct_customer_onboarding(
        self,
        invite_id: str,
        customer_email: str,
        plan: str
    ) -> Mission:
        """
        Main orchestration method for customer onboarding.

        Returns Mission with:
        - Status: executing → completed
        - Tasks: 5 (auth, db, roles, comms, workflow)
        - Checkpoints: proof of each step
        - Cost: tracked per operation
        - Progress: 0% → 100%

        Args:
            invite_id: UUID of customer invite
            customer_email: Email of customer admin
            plan: Plan type (starter, pro, enterprise)

        Returns:
            Mission object with final state and checkpoints
        """
        # 1. CREATE MISSION
        mission = self._create_mission(
            type="customer_registration",
            customer_email=customer_email,
            plan=plan,
            objective=f"Register {customer_email} ({plan} plan)"
        )
        logger.info(f"Mission {mission.id}: CREATED")

        # 2. DISPATCH TASKS TO SWARM (PARALLEL)
        mission.status = MissionStatus.EXECUTING
        mission.started_at = datetime.utcnow()

        # Prepare task payloads
        tasks_to_dispatch = [
            Task(
                id=str(uuid4()),
                type="create_auth_user",
                operator="auth_operator",
                payload={"invite_id": invite_id, "email": customer_email}
            ),
            Task(
                id=str(uuid4()),
                type="create_tenant",
                operator="db_operator",
                payload={"customer_email": customer_email, "plan": plan}
            ),
            Task(
                id=str(uuid4()),
                type="assign_admin_role",
                operator="roles_operator",
                payload={"email": customer_email}
            ),
            Task(
                id=str(uuid4()),
                type="send_welcome_email",
                operator="comms_operator",
                payload={"email": customer_email, "plan": plan}
            ),
            Task(
                id=str(uuid4()),
                type="log_workflow",
                operator="workflow_operator",
                payload={"mission_id": mission.id, "email": customer_email}
            ),
        ]

        mission.tasks = tasks_to_dispatch
        for task in tasks_to_dispatch:
            mission.operator_assignments[task.id] = task.operator

        logger.info(f"Mission {mission.id}: Dispatching {len(tasks_to_dispatch)} tasks in parallel")

        # 3. EXECUTE ALL TASKS IN PARALLEL
        dispatch_coros = [
            self._dispatch_and_execute_task(mission, task)
            for task in tasks_to_dispatch
        ]

        results: List[TaskResult] = await asyncio.gather(
            *dispatch_coros,
            return_exceptions=False  # Raise if any fails
        )

        # 4. RECORD CHECKPOINTS (PROOF OF COMPLETION)
        logger.info(f"Mission {mission.id}: Recording {len(results)} checkpoints")
        for result in results:
            checkpoint = Checkpoint(
                timestamp=datetime.utcnow(),
                task_type=result.operator,
                status=CheckpointStatus.SUCCESS if result.success else CheckpointStatus.FAILED,
                proof=result.proof,
                operator_id=result.operator,
                duration_ms=result.duration_ms,
                cost=result.cost
            )
            mission.add_checkpoint(checkpoint)

            # Track cost
            if result.operator not in mission.cost_breakdown:
                mission.cost_breakdown[result.operator] = 0.0
            mission.cost_breakdown[result.operator] += result.cost

        # 5. CALCULATE FINAL COST
        mission.cost = sum(mission.cost_breakdown.values())
        logger.info(f"Mission {mission.id}: Total cost = ${mission.cost:.4f}")

        # 6. SET FINAL STATE
        all_successful = all(c.status == CheckpointStatus.SUCCESS for c in mission.checkpoints)
        mission.status = MissionStatus.COMPLETED if all_successful else MissionStatus.FAILED
        mission.completed_at = datetime.utcnow()
        mission.progress = 100.0 if all_successful else 0.0

        # 7. BUILD FINAL RESULT
        mission.final_result = {
            "mission_id": mission.id,
            "status": mission.status.value,
            "customer_email": customer_email,
            "checkpoints": [asdict(c) for c in mission.checkpoints],
            "cost": mission.cost,
            "cost_breakdown": mission.cost_breakdown,
            "duration_seconds": int((mission.completed_at - mission.started_at).total_seconds()),
            "progress": mission.progress
        }

        logger.info(f"Mission {mission.id}: COMPLETED - status={mission.status.value}, cost=${mission.cost:.4f}")

        return mission

    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================

    def _create_mission(
        self,
        type: str,
        customer_email: str,
        plan: str,
        objective: str
    ) -> Mission:
        """Create a new mission"""
        mission = Mission(
            id=f"mission-{str(uuid4())[:8]}",
            type=type,
            status=MissionStatus.PENDING,
            objective=objective
        )
        logger.debug(f"Created mission: {mission.id}")
        return mission

    async def _dispatch_and_execute_task(
        self,
        mission: Mission,
        task: Task
    ) -> TaskResult:
        """
        Dispatch task to operator and execute it.

        Returns TaskResult with proof + cost + duration
        """
        task.status = TaskStatus.EXECUTING
        task.started_at = datetime.utcnow()

        try:
            # Get operator (mock for now)
            operator = self.operators.get(task.operator)
            if not operator:
                logger.warning(f"Operator {task.operator} not registered, using mock")
                # Mock operator execution
                result = await self._mock_operator_execution(task)
            else:
                result = await operator.execute(task)

            task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
            task.result = result
            task.completed_at = datetime.utcnow()

            logger.info(
                f"Task {task.id} ({task.type}): "
                f"success={result.success}, cost=${result.cost:.4f}, duration={result.duration_ms}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Task {task.id} failed: {str(e)}")
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            mission.add_blocker(f"Task {task.type} failed: {str(e)}")
            raise

    async def _mock_operator_execution(self, task: Task) -> TaskResult:
        """
        Mock operator execution (for development/testing).

        In production, this would be replaced by actual operators.
        """
        await asyncio.sleep(0.1)  # Simulate work

        mock_proofs = {
            "create_auth_user": {"user_id": str(uuid4())},
            "create_tenant": {"tenant_id": str(uuid4())},
            "assign_admin_role": {"role": "admin", "confirmed": True},
            "send_welcome_email": {"status": "sent", "timestamp": datetime.utcnow().isoformat()},
            "log_workflow": {"logged": True, "entries": 1},
        }

        return TaskResult(
            task_id=task.id,
            operator=task.operator,
            success=True,
            proof=mock_proofs.get(task.type, {}),
            cost=0.005,  # Mock cost
            duration_ms=150
        )


# ============================================================================
# CONDUCTOR FACTORY
# ============================================================================

async def create_conductor(session: AsyncSession) -> OnboardingConductor:
    """
    Factory function to create and initialize conductor.

    Registers all available swarm operators.
    """
    from .swarm import AuthOperator, DBOperator, RolesOperator, CommsOperator, WorkflowTrackerOperator

    conductor = OnboardingConductor(session)

    # Register swarm operators
    await conductor.register_operator("auth_operator", AuthOperator)
    await conductor.register_operator("db_operator", DBOperator)
    await conductor.register_operator("roles_operator", RolesOperator)
    await conductor.register_operator("comms_operator", CommsOperator)
    await conductor.register_operator("workflow_operator", WorkflowTrackerOperator)

    logger.info("Conductor initialized with 5 swarm operators")
    return conductor
